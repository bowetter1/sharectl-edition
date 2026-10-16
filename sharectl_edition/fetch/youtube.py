"""YouTube via each channel's public RSS feed (no API key, never downloads video).
Falls back to the channel's /videos page when the RSS endpoint is down."""
import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from .. import net

NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}


def resolve(handle: str) -> tuple[str | None, str, str, str | None]:
    try:
        h = net.get(f"https://www.youtube.com/@{handle}", 20, browser=True)
        cid = (re.search(r'rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]{22})"', h)
               or re.search(r'"externalId":"(UC[\w-]{22})"', h))
        av = re.search(r'<meta property="og:image" content="([^"]+)"', h)
        nm = re.search(r'<meta property="og:title" content="([^"]+)"', h)
        return (cid.group(1) if cid else None, html.unescape(av.group(1)) if av else "",
                html.unescape(nm.group(1)) if nm else handle, None)
    except net.FetchError as e:
        return (None, "", handle, str(e))


def scrape_videos(handle: str) -> tuple[list[dict], str | None]:
    """Fallback: latest uploads from the channel's /videos page."""
    try:
        h = net.get(f"https://www.youtube.com/@{handle}/videos", 20, browser=True)
        out = []
        for chunk in h.split('"lockupViewModel":{')[1:]:
            vid = re.search(r'i\.ytimg\.com/vi/([\w-]{11})/', chunk)
            t = re.search(r'"lockupMetadataViewModel":\{"title":\{"content":"((?:[^"\\]|\\.)*)"', chunk)
            age = re.search(r'"accessibilityLabel":"(\d+) (minute|hour|day|week|month|year)s? ago"', chunk)
            if not (vid and t):
                continue
            n, unit = (int(age.group(1)), age.group(2)) if age else (0, "day")
            hours = n * {"minute": 1 / 60, "hour": 1, "day": 24, "week": 168, "month": 720, "year": 8760}[unit]
            out.append({"vid": vid.group(1), "title": json.loads('"' + t.group(1) + '"'), "hours": hours, "desc": ""})
            if len(out) >= 8:
                break
        return out, None
    except net.FetchError as e:
        return [], str(e)


def _item(handle, name, avatar, vid, title, desc, pub, rank, section):
    return {"id": f"yt-{vid}", "kind": "video", "yt_id": vid, "source": "yt-" + handle.lower(), "source_name": name,
            "section": section, "title": title, "text": desc, "url": f"https://www.youtube.com/watch?v={vid}",
            "image": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg", "published": pub.isoformat(),
            "author": name, "author_photo": avatar, "avatar": avatar, "feed_rank": rank}


def fetch_channel(ch: dict) -> tuple[dict, list[dict]]:
    handle = ch["handle"].lstrip("@")
    section = ch.get("section", "video")
    cid, avatar, name, resolve_error = resolve(handle)
    st = {"ok": False, "channel_id": cid, "videos": 0}
    now = datetime.now(timezone.utc)
    items = []
    root = None
    feed_error = None
    if cid:
        try:
            root = ET.fromstring(net.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", 20).encode())
        except net.FetchError as e:
            feed_error = str(e)
        except Exception:
            pass
    if root is not None:
        name = root.findtext("a:title", "", NS) or name
        for k, en in enumerate(root.findall("a:entry", NS)):
            g = en.find("m:group", NS)
            desc = (g.findtext("m:description", "", NS) if g is not None else "").strip()
            desc = re.sub(r"https?://\S+", "", desc.split("\n\n")[0])[:240].strip()
            pub = datetime.fromisoformat(en.findtext("a:published", "", NS).replace("Z", "+00:00"))
            items.append(_item(handle, name, avatar, en.findtext("yt:videoId", "", NS), en.findtext("a:title", "", NS),
                               desc, pub, k, section))
    else:
        scraped, scrape_error = scrape_videos(handle)
        for k, v in enumerate(scraped):
            items.append(_item(handle, name, avatar, v["vid"], v["title"], "", now - timedelta(hours=v["hours"]), k, section))
        if scraped:
            st["via"] = "channel page"
        elif scrape_error or feed_error or resolve_error:
            st["error"] = scrape_error or feed_error or resolve_error
    st.update(ok=bool(items), videos=len(items))
    return st, items


def run(channels: list[dict]) -> tuple[dict, list[dict]]:
    stats, items = {}, []
    for ch in channels:
        st, its = fetch_channel(ch)
        stats["yt-" + ch["handle"].lstrip("@").lower()] = st
        items += its
    return stats, items
