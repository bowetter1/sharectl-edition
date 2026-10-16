"""News from public RSS/Atom feeds, plus each article's Open Graph tags and byline.

Only the headline, a short summary, the lead image and the author are kept. Readers
always click through to the publisher; full article text is never stored or republished.
"""
import email.utils
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from .. import net

ATOM = "{http://www.w3.org/2005/Atom}"
AGENCIES = {"ap": "AP", "associated press": "AP", "reuters": "Reuters", "afp": "AFP", "bloomberg": "Bloomberg"}
# A credited "author" that is really the outlet. Matched as whole words, so "AB" never catches "Gabriel".
ORG_WORDS = ["news", "staff", "newsroom", "editors", "editorial", "team", "desk", "contributor", "contributors",
             "media", "press", "group", "inc", "llc", "ltd", "ab", "as", "oy", "gmbh", "magazine", "journal", "times",
             "post", "daily", "redaktion", "redaktionen", "nyheter", "tidning", "tt", "ntb", "ritzau"]
_ORG_RE = re.compile(r"(?<![\w-])(?:" + "|".join(map(re.escape, ORG_WORDS)) + r")(?![\w-])", re.I)


def looks_like_org(name: str) -> bool:
    return bool(_ORG_RE.search(name or ""))


def strip(t: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t or ""))).strip()


def _date(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    try:
        return email.utils.parsedate_to_datetime(s).astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except Exception:
        return ""


def parse_feed(xml: str) -> list[dict]:
    """RSS 2.0 or Atom -> [{title, link, desc, image, published, author}]."""
    try:
        root = ET.fromstring(xml.encode("utf-8"))
    except Exception:
        return []
    out = []
    for it in root.iter("item"):
        g = lambda tag: (it.findtext(tag) or "").strip()
        img = ""
        for el in it:
            if (el.tag.endswith("content") or el.tag.endswith("thumbnail") or el.tag == "enclosure") and el.get("url"):
                if "image" in (el.get("type") or "image") or el.tag.endswith("thumbnail"):
                    img = img or el.get("url")
        author = g("{http://purl.org/dc/elements/1.1/}creator") or g("author")
        out.append({"title": strip(g("title")), "link": g("link"), "desc": strip(g("description"))[:400],
                    "image": img, "published": _date(g("pubDate")), "author": strip(author)})
    for en in root.iter(ATOM + "entry"):
        link = ""
        for l in en.findall(ATOM + "link"):
            if l.get("rel", "alternate") == "alternate":
                link = l.get("href", "")
                break
        summary = en.findtext(ATOM + "summary") or en.findtext(ATOM + "content") or ""
        out.append({"title": strip(en.findtext(ATOM + "title")), "link": link, "desc": strip(summary)[:400], "image": "",
                    "published": _date(en.findtext(ATOM + "published") or en.findtext(ATOM + "updated")),
                    "author": strip(en.findtext(f"{ATOM}author/{ATOM}name") or "")})
    return out


def _meta(h: str, prop: str) -> str:
    for pat in (rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]+content=["\']([^"\']*)',
                rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']{prop}["\']'):
        m = re.search(pat, h, re.I)
        if m:
            return html.unescape(m.group(1)).strip()
    return ""


def _ld_authors(h: str) -> list[dict]:
    out = []
    for blob in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', h, re.S | re.I):
        try:
            data = json.loads(blob.strip())
        except Exception:
            continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, list):
                stack.extend(x)
                continue
            if not isinstance(x, dict):
                continue
            if "author" in x and x.get("@type") != "Person":
                for p in x["author"] if isinstance(x["author"], list) else [x["author"]]:
                    if isinstance(p, str):
                        out.append({"name": p})
                    elif isinstance(p, dict) and p.get("name"):
                        img = p.get("image")
                        img = img.get("url") if isinstance(img, dict) else (img[0] if isinstance(img, list) and img else img)
                        out.append({"name": p["name"], "url": p.get("url") or "", "image": img or "",
                                    "title": p.get("jobTitle") or "", "org": p.get("@type") == "Organization"})
            stack.extend(v for k, v in x.items() if k != "author" and isinstance(v, (dict, list)))
        if out:
            break
    return out


def byline(h: str, feed_author: str = "") -> dict:
    """People first: {people:[{name,image,title}], agency}. Never invented, only what the page or feed states."""
    raw = _ld_authors(h)
    if not raw:
        name = _meta(h, "author") or feed_author
        raw = [{"name": name}] if name else []
    people, agency = [], None
    for r in raw:
        for part in re.split(r",| and |&", r["name"]):
            n = part.strip()
            if not n or n.startswith("http"):
                continue
            if n.lower() in AGENCIES:
                agency = AGENCIES[n.lower()]
                continue
            if r.get("org") or len(n.split()) < 2 or looks_like_org(n):
                continue
            people.append({"name": n, "image": r.get("image", ""), "title": r.get("title", "")})
    return {"people": people[:3], "agency": agency}


def article_meta(url: str, feed_author: str = "") -> dict:
    if not net.allowed(url):
        return {"title": "", "description": "", "image": "", "byline": byline("", feed_author)}
    try:
        h = net.get(url, 12, browser=True)[:800_000]
        return {"title": _meta(h, "og:title"), "description": _meta(h, "og:description") or _meta(h, "description"),
                "image": _meta(h, "og:image"), "byline": byline(h, feed_author)}
    except net.FetchError:
        return {"title": "", "description": "", "image": "", "byline": byline("", feed_author)}


def fetch_source(src: dict, candidates: int = 8) -> tuple[dict, list[dict]]:
    """One configured source -> (stats, items). src = {id, name, url, section?, priority?}."""
    urls = src["url"] if isinstance(src["url"], list) else [src["url"]]
    arts, used, error = [], None, None
    for u in urls:
        try:
            arts = parse_feed(net.get(u, 20, browser=True))
            if arts:
                used = u
                break
        except net.FetchError as e:
            error = str(e)
    # Repeated feed entries are one candidate, keeping the first occurrence's metadata.
    # Deduplicate before the cap so repeats cannot crowd out other articles.
    unique, seen = [], set()
    for a in arts:
        if a["link"] and a["title"] and a["link"] not in seen:
            unique.append(a)
            seen.add(a["link"])
    arts = unique[:candidates]
    stats = {"name": src["name"], "ok": bool(arts), "feed": used or urls[0], "read": len(arts)}
    if error and not arts:
        stats["error"] = error
    if src.get("enrich", True):
        with ThreadPoolExecutor(6) as ex:
            metas = list(ex.map(lambda a: article_meta(a["link"], a["author"]), arts))
    else:
        metas = [{"title": "", "description": "", "image": "", "byline": byline("", a["author"])} for a in arts]
    site = re.match(r"https?://[^/]+", (arts[0]["link"] if arts else urls[0])).group(0)
    items = []
    for a, m in zip(arts, metas):
        title = m["title"] or a["title"]
        title = re.sub(r"\s*[|–—-]\s*" + re.escape(src["name"]) + r"\s*$", "", title, flags=re.I)
        people = m["byline"]["people"]
        items.append({
            "id": src["id"] + "-" + hashlib.sha1(a["link"].encode()).hexdigest()[:10],
            "kind": "news", "source": src["id"], "source_name": src["name"], "section": src.get("section", ""),
            "title": title, "text": (m["description"] or a["desc"])[:300], "url": a["link"],
            "image": m["image"] or a["image"], "published": a["published"],
            "author": people[0]["name"] if people else "",
            "coauthors": [p["name"] for p in people[1:]],
            "author_photo": people[0]["image"] if people else "",
            "author_title": people[0]["title"] if people else "",
            "agency": m["byline"]["agency"] or "",
            "avatar": f"https://www.google.com/s2/favicons?domain={site}&sz=128",
            "priority": src.get("priority", 0), "cap": src.get("cap"),
        })
    return stats, items


def run(sources: list[dict], candidates: int = 8) -> tuple[dict, list[dict]]:
    stats, items = {}, []
    with ThreadPoolExecutor(8) as ex:
        for src, (st, its) in zip(sources, ex.map(lambda s: fetch_source(s, candidates), sources)):
            stats[src["id"]] = st
            items += its
    return stats, items
