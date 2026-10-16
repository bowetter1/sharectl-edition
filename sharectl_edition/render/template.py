"""Render selected items as a single static newspaper page (index.html, CSS inlined)."""
import html
import os
from datetime import datetime
from urllib.parse import urlsplit

from . import labels

HERE = os.path.dirname(os.path.abspath(__file__))
PALETTE = ["#5b3fd1", "#0b6bb3", "#0e7469", "#157a3d", "#a35f00", "#c2410c", "#b4235a", "#1b4f9c"]
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' rx='7' fill='%23000'/%3E%3Ctext x='16' y='23' font-family='Georgia,serif' "
           "font-weight='700' font-size='22' fill='%23fff' text-anchor='middle'%3Es%3C/text%3E%3C/svg%3E")
e = html.escape

STRINGS = {}


def set_strings(overrides: dict | None = None):
    """Set UI strings before rendering."""
    global STRINGS
    STRINGS = labels.get(overrides)


def fmt_date(now) -> str:
    return STRINGS["date"].format(day=STRINGS["days"][now.weekday()], month=STRINGS["months"][now.month - 1], d=now.day, y=now.year)


def esc_attr(s: str) -> str:
    return html.escape(s or "", quote=True)


def short(text: str, n: int = 110) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0].rstrip(",.;:–-") + "…"


def color_for(key: str) -> str:
    return PALETTE[sum(map(ord, key or "x")) % len(PALETTE)]


def pic(it, cls="pic"):
    if not it.get("image"):
        return ""
    return (f'<a class="{cls}" href="{esc_attr(it["url"])}" style="--img:url(\'{esc_attr(it["image"])}\')">'
            f'<img src="{esc_attr(it["image"])}" alt="" loading="lazy" referrerpolicy="no-referrer"></a>')


def byline(it):
    """Writer's name before the outlet."""
    if it.get("author"):
        names = ", ".join([it["author"]] + it.get("coauthors", []))
        if it["kind"] == "post":
            sub = "@" + it.get("handle", "") + (" · " + STRINGS["via"].format(name=it["via"]) if it.get("via") else "")
        else:
            sub = " · ".join(x for x in (it.get("author_title"), it["source_name"], it.get("agency")) if x)
        return f'<div class="by"><span><b>{e(names)}</b><small>{e(sub)}</small></span></div>'
    return f'<div class="by"><span><b>{e(it["source_name"])}</b></span></div>'


def hed(it, size):
    if it["kind"] == "post":
        n = 170 if size == "small" else 420
        return f'<p class="hed {size}"><a href="{esc_attr(it["url"])}">{e(short(it["text"], n))}</a></p>'
    return f'<h3 class="hed {size}"><a href="{esc_attr(it["url"])}">{e(it["title"])}</a></h3>'


def dek(it):
    return f'<p class="dek">{e(short(it["text"], 220))}</p>' if it.get("text") else ""


def art(it, cls, body):
    return f'<article class="it {cls}" style="--c:{color_for(it["source"])}">{body}</article>'


def when(it, tz):
    try:
        return datetime.fromisoformat(it["published"].replace("Z", "+00:00")).astimezone(tz)
    except Exception:
        return None


def front(lead, items, tz):
    main = art(lead, "f-art", f'{pic(lead, "pic whole")}<p class="kicker">{STRINGS["top_story"]}</p>'
               f'{hed(lead, "giant").replace("<h3", "<h2").replace("</h3>", "</h2>")}{dek(lead)}{byline(lead)}')
    dated = sorted(((when(it, tz), it) for it in items if it is not lead), 
                   key=lambda x: x[0] or datetime.min.replace(tzinfo=tz), reverse=True)
    rows = "".join(
        f'<li style="--s:{it["sec_color"]}"><time>{t.strftime(STRINGS["time"])}</time><a href="{esc_attr(it["url"])}">'
        f'{e(short(it.get("title") or it["text"], 90))}</a><small><span class="sec">{e(it["sec_title"])}</span>'
        f'{e(it.get("author") or it["source_name"])}</small></li>' for t, it in dated[:7] if t)
    return (f'<section class="w front" id="top"><div class="f-main">{main}</div>'
            f'<aside class="f-side"><ol class="latest">{rows}</ol></aside></section>')


def big(it):
    size = "big" if it.get("image") else "mid"
    return art(it, "lead", f'{pic(it)}{byline(it)}{hed(it, size)}{dek(it)}')


def small(it):
    return art(it, "small-art", f'{pic(it)}{byline(it)}{hed(it, "small")}')


def two(items):
    cards = "".join(art(it, "col", f'{pic(it)}{byline(it)}{hed(it, "mid")}{dek(it)}') for it in items)
    return f'<div class="w two">{cards}</div>'


def briefs(items):
    rows = "".join(art(it, "brief", f'<div class="b-text">{byline(it)}{hed(it, "small")}{dek(it)}</div>'
                       + pic(it)) for it in items)
    return f'<div class="w briefs"><p class="kicker">{STRINGS["more_news"]}</p>{rows}</div>'


def voices(items):
    """X posts rendered as quote cards."""
    cards = "".join(art(it, "voice", f'{byline(it)}<p class="quote"><a href="{esc_attr(it["url"])}">{e(it["text"])}</a></p>'
                        + (f'<a class="out" href="{esc_attr(it["link_out"])}">{STRINGS["read_more"].format(site=e(urlsplit(it["link_out"]).netloc))} →</a>'
                           if it.get("link_out") else "")) for it in items)
    return f'<div class="w voices"><p class="kicker">{STRINGS["voices"]}</p><div class="v-grid">{cards}</div></div>'


def video_desk(sec):
    """Video section with play button overlays."""
    tiles = "".join(art(it, "tile", f'<a class="yt" href="{esc_attr(it["url"])}"><img src="{esc_attr(it["image"])}" alt="" loading="lazy">'
                        f'<span class="play-btn" aria-hidden="true"></span></a>{byline(it)}{hed(it, "small")}')
                    for it in sec["items"])
    return (f'<section class="desk videos" id="{sec["key"]}" style="--s:{sec["color"]}"><header class="w d-head">'
            f'<h2>{e(sec["title"])}</h2></header><div class="w v-tiles">{tiles}</div></section>')


def desk(sec):
    items = sec["items"]
    
    # All videos: use video layout
    if all(it["kind"] == "video" for it in items):
        return video_desk(sec)
    
    blocks = []
    
    # Group consecutive text-only posts together
    from itertools import groupby
    for text_only, group in groupby(items, key=lambda it: it["kind"] == "post" and not it.get("image")):
        ordered = list(group)
        if text_only:
            blocks.append(voices(ordered))
            continue
        
        # Regular news layout
        main = ordered[0]
        side = ordered[1:4]
        remaining = ordered[4:]
        
        aside = f'<aside class="t-side">{"".join(small(it) for it in side)}</aside>'
        blocks.append(f'<div class="w top"><div class="t-main">{big(main)}</div>{aside}</div>')
        
        if remaining:
            blocks.append(two(remaining[:2]))
        if len(remaining) > 2:
            blocks.append(briefs(remaining[2:]))
    
    head = f'<header class="w d-head"><h2>{e(sec["title"])}</h2>' + (f'<p>{e(sec["sub"])}</p>' if sec.get("sub") else "") + "</header>"
    return f'<section class="desk" id="{sec["key"]}" style="--s:{sec["color"]}">{head}{"".join(blocks)}</section>'


def why_block(cfg, report, every):
    """End of paper: sources used and article count."""
    report = report or {}
    stats = report.get("sources") or {}
    read = sum(s.get("read", 0) for s in stats.values())
    kept = len(every)
    
    intro = STRINGS["why_ai_intro"].format(kept=kept)
    names = list(dict.fromkeys(it["source_name"] for it in every))
    srcs = "".join(f"<li>{e(n)}</li>" for n in names)
    
    return (f'<section class="w why" id="why"><h2>{STRINGS["why_title"]}</h2><p class="why-intro">{e(intro)}</p>'
            f'<div class="why-cols"><div><p class="kicker">{STRINGS["sources_today"]}</p><ul class="src-list">{srcs}</ul></div>'
            f'</div></section><p class="w the-end">{STRINGS["the_end"]}</p>')


def page(cfg, sections, now, tz, report=None, lead_id=None):
    set_strings(cfg.get("strings"))
    
    with open(os.path.join(HERE, "edition.css"), encoding="utf-8") as f:
        css = f.read()
    
    for s in sections:
        s.setdefault("color", color_for(s["key"]))
        for it in s["items"]:
            it["sec"], it["sec_title"], it["sec_color"] = s["key"], s["title"], s["color"]
    
    every = [it for s in sections for it in s["items"]]
    news_like = [it for it in every if it["kind"] != "video"]
    lead = next((it for it in news_like if it.get("image") and it["kind"] == "news"), news_like[0] if news_like else None)
    
    if lead_id is not None:
        lead = next(it for it in news_like if it["id"] == lead_id)
    
    if lead:
        for s in sections:
            if lead in s["items"]:
                s["items"].remove(lead)
        sections = [s for s in sections if s["items"]]
    
    hello = cfg["greeting"].format(name=cfg["name"])
    date = fmt_date(now)
    nav = (f'<a class="pill plain" href="#top">{STRINGS["top_story"]}</a>' if lead else "") + "".join(
        f'<a class="pill" href="#{s["key"]}" style="--s:{s["color"]}">{e(s["title"])}</a>' for s in sections)
    nav += f'<a class="pill why-link" href="#why">{STRINGS["why"]}</a>'
    
    body = (f'<header class="masthead"><div class="w m-row"><span>{date}</span><b>sharectl</b><span>{STRINGS["tagline"]}</span></div>'
            f'<div class="w m-name"><a href="#top">{e(hello)}</a></div></header>'
            f'<nav class="nav"><div class="w nav-in">{nav}</div></nav><main>'
            + (front(lead, every, tz) if lead else "")
            + "".join(desk(s) for s in sections)
            + why_block(cfg, report, every)
            + f'</main><footer class="w foot"><span>{STRINGS["footer"]}</span><span>{STRINGS["tell_agent"]}</span></footer>')
    
    return (f'<!doctype html><html lang="{STRINGS["html_lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(hello)} · {date}</title><meta name="robots" content="noindex"><link rel="icon" href="{FAVICON}">'
            f'<style>{css}</style></head>'
            f'<body class="paper" data-edition="{now:%Y-%m-%d}">{body}</body></html>')
