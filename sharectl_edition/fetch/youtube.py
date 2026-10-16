"""YouTube videos via channel RSS feeds (no API key). Falls back to /videos page when RSS fails."""
import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from .. import net

NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}


def resolve(handle: str) -> tuple[str | None, str, str]:
    """Get channel ID, avatar, and name from @handle."""
    try:
        h = net.get(f"https://www.youtube.com/@{handle}", 20, browser=True)
        cid = (re.search(r'rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]{22})"', h)
               or re.search(r'"externalId":"(UC[\w-]{22})"', h))
        av = re.search(r'<meta property="og:image" content="([^"]+)"', h)
        nm = re.search(r'<meta property="og:title" content="([^"]+)"', h)
        return (cid.group(1) if cid else None, 
                html.unescape(av.group(1)) if av else "",
                html.unescape(nm.group(1)) if nm else handle)
    except net.FetchError:
        return (None, "", handle)


def scrape_videos(handle: str) -> list[dict]:
    """Fallback: latest uploads from channel /videos page."""
    try:
        h = net.get(f"https://www.youtube.com/@{handle}/videos", 20, browser=True)
        out = []
        for chunk in h.split('"lockupViewModel":{')[1:]:
            vid = re.search(r'i\.ytimg\.com/vi/([\w-]{11})/', chunk)
            t = re.search(r'"title":\{"content":"((?:[^"\\]|\\.)*)"', chunk)
            age = re.search(r'"accessibilityLabel":"(\d+) (minute|hour|day|week|month)s? ago"', chunk)
            if not (vid and t):
                continue
            n, unit = (int(age.group(1)), age.group(2)) if age else (0, "day")
            hours = n * {"minute": 1/60, "hour": 1, "day": 24, "week": 168, "month": 720}[unit]
            out.append({
                "vid": vid.group(1),
                "title": json.loads('"' + t.group(1) + '"'),
                "hours": hours
            })
            if len(out) >= 8:
                break
        return out
    except net.FetchError:
        return []


def fetch_channel(ch: dict) -> tuple[dict, list[dict]]:
    """Fetch videos from one YouTube channel."""
    handle = ch["handle"].lstrip("@")
    section = ch.get("section", "video")
    cid, avatar, name = resolve(handle)
    
    stats = {"ok": False, "videos": 0}
    items = []
    now = datetime.now(timezone.utc)
    
    # Try RSS feed first
    if cid:
        try:
            xml = net.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", 20)
            root = ET.fromstring(xml.encode())
            name = root.findtext("a:title", "", NS) or name
            
            for en in root.findall("a:entry", NS):
                g = en.find("m:group", NS)
                desc = (g.findtext("m:description", "", NS) if g else "").strip()
                desc = re.sub(r"https?://\S+", "", desc.split("\n\n")[0])[:240].strip()
                pub = datetime.fromisoformat(en.findtext("a:published", "", NS).replace("Z", "+00:00"))
                vid = en.findtext("yt:videoId", "", NS)
                
                items.append({
                    "id": f"yt-{vid}",
                    "kind": "video",
                    "source": "yt-" + handle.lower(),
                    "source_name": name,
                    "section": section,
                    "title": en.findtext("a:title", "", NS),
                    "text": desc,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "image": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                    "published": pub.isoformat(),
                    "author": name,
                    "avatar": avatar
                })
        except Exception:
            pass
    
    # Fallback to /videos page scraping
    if not items:
        scraped = scrape_videos(handle)
        for v in scraped:
            pub = now - timedelta(hours=v["hours"])
            items.append({
                "id": f"yt-{v['vid']}",
                "kind": "video",
                "source": "yt-" + handle.lower(),
                "source_name": name,
                "section": section,
                "title": v["title"],
                "text": "",
                "url": f"https://www.youtube.com/watch?v={v['vid']}",
                "image": f"https://i.ytimg.com/vi/{v['vid']}/hqdefault.jpg",
                "published": pub.isoformat(),
                "author": name,
                "avatar": avatar
            })
    
    stats.update(ok=bool(items), videos=len(items))
    return stats, items


def run(channels: list[dict]) -> tuple[dict, list[dict]]:
    """Fetch videos from all configured channels."""
    stats, items = {}, []
    for ch in channels:
        st, its = fetch_channel(ch)
        stats["yt-" + ch["handle"].lstrip("@").lower()] = st
        items += its
    return stats, items
