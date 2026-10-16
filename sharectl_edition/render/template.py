"""Render selected items as a single static newspaper page (index.html, CSS inlined)."""
import html
import json
import os
import re
from datetime import datetime
from itertools import groupby
from urllib.parse import urlsplit

from . import labels

HERE = os.path.dirname(os.path.abspath(__file__))
PALETTE = ["#5b3fd1", "#0b6bb3", "#0e7469", "#157a3d", "#a35f00", "#c2410c", "#b4235a", "#1b4f9c"]
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' rx='7' fill='%23000'/%3E%3Ctext x='16' y='23' font-family='Georgia,serif' "
           "font-weight='700' font-size='22' fill='%23fff' text-anchor='middle'%3Es%3C/text%3E%3C/svg%3E")
e = html.escape

EN = labels.EN  # the strings in use; `set_language` swaps them before a render


def set_language(lang: str | None, overrides: dict | None = None) -> dict:
    """Pick the UI strings for this edition (built-in language plus the reader's `strings` from config).
    Call before building the morning blocks and the page."""
    global EN
    EN = labels.get(lang, overrides)
    return EN


def fmt_date(now) -> str:
    return EN["date"].format(day=EN["days"][now.weekday()], month=EN["months"][now.month - 1], d=now.day, y=now.year)


def esc_attr(s: str) -> str:
    return html.escape(s or "", quote=True)


def short(text: str, n: int = 110) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0].rstrip(",.;:–-") + "…"


def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name or "") if p[:1].isalpha()]
    return "".join(p[0] for p in parts[:2]).upper() or "•"


def color_for(key: str) -> str:
    return PALETTE[sum(map(ord, key or "x")) % len(PALETTE)]


# ---------- building blocks ----------

def pic(it, cls="pic"):
    if not it.get("image"):
        return ""
    if it["kind"] == "post":
        cls += " whole"  # X images are often screenshots with text: show them whole, never crop
    return (f'<a class="{cls}" href="{esc_attr(it["url"])}" style="--img:url(\'{esc_attr(it["image"])}\')">'
            f'<img src="{esc_attr(it["image"])}" alt="" loading="lazy" referrerpolicy="no-referrer"></a>')


def byline(it):
    """Writer's name and photo before the outlet. Falls back to the outlet (logo) when no person is credited."""
    if it.get("author") and it["kind"] != "video":
        photo = it.get("author_photo")
        av = (f'<span class="av"><img src="{esc_attr(photo)}" alt="" loading="lazy" referrerpolicy="no-referrer"></span>'
              if photo else f'<span class="av">{e(initials(it["author"]))}</span>')
        names = ", ".join([it["author"]] + it.get("coauthors", []))
        if it["kind"] == "post":
            sub = "@" + it.get("handle", "") + (" · " + EN["via"].format(name=it["via"]) if it.get("via") else "")
        else:
            sub = " · ".join(x for x in (it.get("author_title"), it["source_name"], it.get("agency")) if x)
        return f'<div class="by">{av}<span><b>{e(names)}</b><small>{e(sub)}</small></span></div>'
    logo = it.get("author_photo") or it.get("avatar")
    av = (f'<span class="av logo"><img src="{esc_attr(logo)}" alt="" loading="lazy" referrerpolicy="no-referrer"></span>'
          if logo else f'<span class="av">{e(initials(it["source_name"]))}</span>')
    sub = it.get("agency") or ""
    return f'<div class="by">{av}<span><b>{e(it["source_name"])}</b>{f"<small>{e(sub)}</small>" if sub else ""}</span></div>'


def thumbs(it):
    return ""


def hed(it, size):
    if it["kind"] == "post":
        n = 170 if size == "small" else 420
        return f'<p class="hed {size}"><a href="{esc_attr(it["url"])}">{e(short(it["text"], n))}</a></p>'
    return f'<h3 class="hed {size}"><a href="{esc_attr(it["url"])}">{e(it["title"])}</a></h3>'


def dek(it):
    return f'<p class="dek">{e(short(it["text"], 220))}</p>' if it.get("text") and it["kind"] != "post" else ""


def art(it, cls, body):
    return f'<article class="it {cls}" style="--c:{color_for(it["source"])}">{body}</article>'


def when(it, tz):
    try:
        return datetime.fromisoformat(it["published"].replace("Z", "+00:00")).astimezone(tz)
    except Exception:
        return None


# ---------- morning modules ----------

CLOUD = "M7 18.5h10.5a4 4 0 0 0 .4-8 5.5 5.5 0 0 0-10.6 1.4A3.3 3.3 0 0 0 7 18.5z"
CLOUD_UP = "M7 15h10.5a4 4 0 0 0 .4-8 5.5 5.5 0 0 0-10.6 1.4A3.3 3.3 0 0 0 7 15z"
ICONS = {
    "sun": '<circle class="sun" cx="12" cy="12" r="4.2"/><path class="ray" d="M12 2.6v2.2M12 19.2v2.2M2.6 12h2.2M19.2 12h2.2M5.4 5.4 7 7M17 17l1.6 1.6M5.4 18.6 7 17M17 7l1.6-1.6"/>',
    "partly": f'<circle class="sun" cx="8.5" cy="8.5" r="3.4"/><path class="ray" d="M8.5 2.4v1.3M2.4 8.5h1.3M4.2 4.2l.9.9M12.8 4.2l-.9.9"/><path class="cloud" d="{CLOUD}"/>',
    "cloud": f'<path class="cloud" d="{CLOUD}"/>',
    "rain": f'<path class="cloud" d="{CLOUD_UP}"/><path d="M9 18l-1 3M13 18l-1 3M17 18l-1 3"/>',
    "snow": f'<path class="cloud" d="{CLOUD_UP}"/><circle class="dot" cx="8.5" cy="19" r="1"/><circle class="dot" cx="12.5" cy="20.5" r="1"/><circle class="dot" cx="16.5" cy="19" r="1"/>',
    "storm": f'<path class="cloud" d="{CLOUD_UP}"/><path d="M13 16.5 11 19.5h3l-2 3"/>',
    "fog": '<path d="M4 9h16M6 13h12M4 17h16"/>',
}


def icon(sym):
    return f'<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">{ICONS.get(sym, ICONS["cloud"])}</svg>'


def weather_headline(w) -> str:
    word = EN["wx_words"].get(w["sym"], w["sym"])
    key = "wx_hed" if w.get("place") else "wx_hed_noplace"
    return EN[key].format(word=word, hi=round(w["hi"]), place=w.get("place", ""))


def num(x: float, digits: int = 2, sign: bool = False) -> str:
    """A number the way the reader writes it: 1,234.56 in English, 1 234,56 in Swedish (from the strings table)."""
    s = f"{x:+,.{digits}f}" if sign else f"{x:,.{digits}f}"
    return s.replace(",", "\0").replace(".", EN["decimal"]).replace("\0", EN["thousands"])


def pct(x: float, digits: int = 1, sign: bool = False) -> str:
    return EN["percent"].format(n=num(x, digits, sign))


def markets_headline(ms) -> str:
    best = max(ms, key=lambda m: abs(m["change"]))
    return EN["mk_rose" if best["change"] > 0 else "mk_fell"].format(label=best["label"], pct=num(abs(best["change"]), 1))


def weather_block(w, headline=None):
    headline = headline or weather_headline(w)
    deg = lambda x: f"{round(x)}°"
    r = w["rain"]
    rain = EN["no_rain"] if r < 10 else EN["some_rain"].format(p=r) if r < 40 else EN["rain"].format(p=r)
    sub = EN["weather_sub"].format(hi=deg(w["hi"]), lo=deg(w["lo"]), wind=round(w["wind"]), unit=w["wind_unit"], rain=rain)
    cells = "".join(f'<li class="{"now" if i == 0 else ""}"><span>{EN["now"] if i == 0 else h["time"]}</span>'
                    f'{icon(h["sym"])}<b>{deg(h["temp"])}</b></li>' for i, h in enumerate(w["strip"]))
    t = w["tomorrow"]
    cells += f'<li class="tmrw"><span>{EN["tomorrow"]}</span>{icon(t["sym"])}<b>{deg(t["hi"])}</b><small>{deg(t["lo"])}</small></li>'
    return (f'<div class="mod weather wx-{w["sym"]}"><div class="mod-text"><p class="kicker">{EN["weather"]}</p>'
            f'<h2 class="mod-hed">{e(headline)}</h2><p class="mod-sub">{e(sub)}</p><p class="mod-src">Open-Meteo</p></div>'
            f'<div class="mod-data"><ol class="hours">{cells}</ol></div></div>')


def spark(values, prev):
    values = values[:: max(1, len(values) // 60)] or [prev]
    lo, hi = min(values + [prev]), max(values + [prev])
    span = (hi - lo) or 1
    y = lambda v: 30 - (v - lo) / span * 28
    step = 100 / max(1, len(values) - 1)
    pts = " ".join(f"{i * step:.1f},{y(v):.1f}" for i, v in enumerate(values))
    return (f'<svg class="spark" viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden="true">'
            f'<line class="base" x1="0" x2="100" y1="{y(prev):.1f}" y2="{y(prev):.1f}"/><polyline points="{pts}"/></svg>')


def markets_block(ms, title=None, headline=None):
    title = title or EN["markets"]
    headline = headline or markets_headline(ms)
    up = sum(m["change"] > 0 for m in ms)
    mood = "up" if up * 2 > len(ms) else "down"
    cells = "".join(f'<li class="{"up" if m["change"] > 0 else "down"}"><span class="lbl">{e(m["label"])}</span>'
                    f'<span class="chg">{pct(m["change"], 2, sign=True)}</span>'
                    f'<span class="nm">{e(m["name"])}</span>'
                    f'<span class="val">{num(m["price"])}</span>{spark(m["spark"], m["prev"])}</li>' for m in ms)
    return (f'<div class="mod markets {mood}"><div class="mod-text"><p class="kicker">{e(title)}</p>'
            f'<h2 class="mod-hed">{e(headline)}</h2><p class="mod-sub">{EN["markets_sub_up"].format(up=up, n=len(ms))}</p>'
            f'<p class="mod-src">Yahoo Finance</p></div><div class="mod-data"><ul class="idx">{cells}</ul></div></div>')


# ---------- front page and sections ----------

def front(lead, items, tz):
    main = art(lead, "f-art", f'{pic(lead, "pic whole")}<p class="kicker">{EN["top_story"]}</p>'
               f'{hed(lead, "giant").replace("<h3", "<h2").replace("</h3>", "</h2>")}{dek(lead)}{byline(lead)}{thumbs(lead)}')
    dated = sorted(((when(it, tz), it) for it in items if it is not lead), key=lambda x: x[0] or datetime.min.replace(tzinfo=tz), reverse=True)
    rows = "".join(
        f'<li style="--s:{it["sec_color"]}"><time>{t.strftime(EN["time"])}</time><a href="{esc_attr(it["url"])}">'
        f'{e(short(it.get("title") or it["text"], 90))}</a><small><span class="sec">{e(it["sec_title"])}</span>'
        f'{e(it.get("author") or it["source_name"])}</small></li>' for t, it in dated[:7] if t)
    return (f'<section class="w front" id="top"><div class="f-main">{main}</div>'
            f'<aside class="f-side"><h3 class="kicker">{EN["latest"]}</h3><ol class="latest">{rows}</ol></aside></section>')


def big(it):
    size = "big" if it.get("image") or it["kind"] != "post" else "mid"
    return art(it, "lead", f'{pic(it)}{byline(it)}{hed(it, size)}{dek(it)}{thumbs(it)}')


def small(it):
    return art(it, "small-art", f'{pic(it)}{byline(it)}{hed(it, "small")}{thumbs(it)}')


def voices(items):
    cards = "".join(art(it, "voice", f'{byline(it)}<p class="quote"><a href="{esc_attr(it["url"])}">{e(it["text"])}</a></p>'
                        + (f'<a class="out" href="{esc_attr(it["link_out"])}">{EN["read_more"].format(site=e(urlsplit(it["link_out"]).netloc))} →</a>'
                           if it.get("link_out") else "") + thumbs(it)) for it in items)
    return f'<div class="w voices"><p class="kicker">{EN["voices"]}</p><div class="v-grid">{cards}</div></div>'


def two(items):
    cards = "".join(art(it, "col", f'{pic(it)}{byline(it)}{hed(it, "mid")}{dek(it)}{thumbs(it)}') for it in items)
    return f'<div class="w two">{cards}</div>'


def briefs(items):
    rows = "".join(art(it, "brief", f'<div class="b-text">{byline(it)}{hed(it, "small")}{dek(it)}{thumbs(it)}</div>'
                       + pic(it)) for it in items)
    return f'<div class="w briefs"><p class="kicker">{EN["more_news"]}</p>{rows}</div>'


def video_desk(sec):
    tiles = "".join(art(it, "tile", f'<a class="yt" href="{esc_attr(it["url"])}"><img src="{esc_attr(it["image"])}" alt="" loading="lazy">'
                        f'<span class="play-btn" aria-hidden="true"></span></a>{byline(it)}{hed(it, "small")}{thumbs(it)}')
                    for it in sec["items"])
    return (f'<section class="desk videos" id="{sec["key"]}" style="--s:{sec["color"]}"><header class="w d-head">'
            f'<h2>{e(sec["title"])}</h2><p>{e(sec.get("sub") or EN["videos_sub"])}</p></header><div class="w v-tiles">{tiles}</div></section>')


def desk(sec):
    items = sec["items"]
    if all(it["kind"] == "video" for it in items):
        return video_desk(sec)
    blocks = []
    # Keep the editor's order, using voices only for consecutive text-only posts.
    for text_only, group in groupby(items, key=lambda it: it["kind"] == "post" and not it.get("image")):
        ordered = list(group)
        if text_only:
            blocks.append(voices(ordered))
            continue
        main, others = ordered[0], ordered[1:]
        side, remaining = others[:3], others[3:]
        aside = f'<aside class="t-side">{"".join(small(it) for it in side)}</aside>'
        blocks.append(f'<div class="w top"><div class="t-main">{big(main)}</div>{aside}</div>')
        if remaining:
            blocks.append(two(remaining[:2]))
        if len(remaining) > 2:
            blocks.append(briefs(remaining[2:]))
    head = f'<header class="w d-head"><h2>{e(sec["title"])}</h2>' + (f'<p>{e(sec["sub"])}</p>' if sec.get("sub") else "") + "</header>"
    return f'<section class="desk" id="{sec["key"]}" style="--s:{sec["color"]}">{head}{"".join(blocks)}</section>'


FEEDBACK_JS = ""


def why_block(cfg, report, every):
    """The end of the paper: which sources made it in, what the rules left out, and a line that says it's over.
    `report` is the build report ({sources, skipped, counts}); it may be empty when rendering a fixture."""
    report = report or {}
    rules = cfg.get("rules") or {}
    stats = report.get("sources") or {}
    read = sum(s.get("read", 0) + s.get("videos", 0) + s.get("posts", 0) for s in stats.values())
    kept = sum((report.get("counts") or {}).values()) or len(every)
    intro = EN["why_ai_intro" if report.get("editor") == "ai" else "why_intro"].format(read=read or "–", n=len(stats) or len({it["source"] for it in every}), kept=kept,
                                   per_source=rules.get("max_per_source", "–"), political=rules.get("max_political", "–"))
    skipped = report.get("skipped") or {}
    reasons = "".join(f'<li><b>{n}</b> {e(EN["skip_reasons"].get(k, k))}</li>' for k, n in skipped.items() if n)
    names = list(dict.fromkeys(it["source_name"] for it in every))
    srcs = "".join(f"<li>{e(n)}</li>" for n in names)
    return (f'<section class="w why" id="why"><h2>{EN["why_title"]}</h2><p class="why-intro">{e(intro)}</p>'
            f'<div class="why-cols"><div><p class="kicker">{EN["sources_today"]}</p><ul class="src-list">{srcs}</ul></div>'
            + (f'<div><p class="kicker">{EN["why_skipped"]}</p><ul class="skip-list">{reasons}</ul></div>' if reasons else "")
            + f'</div></section><p class="w the-end">{EN["the_end"]}</p>')


def page(cfg, sections, morning, now, tz, report=None, lead_id=None):
    set_language(cfg.get("language"), cfg.get("strings"))
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
    nav = (f'<a class="pill plain" href="#top">{EN["top_story_nav"]}</a>' if lead else "") + "".join(
        f'<a class="pill" href="#{s["key"]}" style="--s:{s["color"]}">{e(s["title"])}</a>' for s in sections)
    nav += f'<a class="pill why-link" href="#why">{EN["why"]}</a>'
    body = (f'<header class="masthead"><div class="w m-row"><span>{date}</span><b>sharectl</b><span>{EN["tagline"]}</span></div>'
            f'<div class="w m-name"><a href="#top">{e(hello)}</a></div></header>'
            f'<nav class="nav"><div class="w nav-in">{nav}</div></nav><main>'
            + (f'<section class="w morning" aria-label="This morning">{"".join(morning)}</section>' if morning else "")
            + (front(lead, news_like, tz) if lead else "")
            + "".join(desk(s) for s in sections)
            + why_block(cfg, report, every)
            + f'</main><footer class="w foot"><span>{EN["footer"]}</span><span>{EN["tell_agent"]}</span></footer>')
    return (f'<!doctype html><html lang="{EN["html_lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(hello)} · {date}</title><meta name="robots" content="noindex"><link rel="icon" href="{FAVICON}">'
            f'<style>{css}</style></head>'
            f'<body class="paper" data-edition="{now:%Y-%m-%d}">{body}</body></html>')
