"""Fetch -> select -> render. Returns the HTML and a report of what was kept and skipped."""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from . import feedback, select
from .fetch import markets, news, weather, x, youtube
from .render import template


def build(cfg: dict, base_dir: str = ".", offline_items: str | None = None) -> tuple[str, dict]:
    tz = ZoneInfo(cfg["timezone"])
    now = datetime.now(tz)
    rules = cfg["rules"]
    fb_path = os.path.join(base_dir, cfg["feedback_file"])
    w = feedback.load(fb_path)
    report = {"date": now.isoformat(), "sources": {}}

    if offline_items:  # re-render from a saved items.json (used by tests and the example)
        with open(offline_items, encoding="utf-8") as f:
            raw = json.load(f)
        news_items, videos, posts = raw["news"], raw["videos"], raw["posts"]
        wx, mk = raw.get("weather"), raw.get("markets")
    else:
        st, news_items = news.run(cfg["sources"]["rss"])
        report["sources"].update(st)
        st, videos = youtube.run(cfg["sources"].get("youtube", []))
        report["sources"].update(st)
        posts = []
        xcfg = cfg["sources"].get("x") or {}
        if xcfg.get("enabled") and xcfg.get("timeline_file"):
            p = os.path.join(base_dir, xcfg["timeline_file"])
            if os.path.exists(p):
                st, posts = x.from_timeline(p, xcfg.get("section", ""))
                report["sources"].update(st)
        mods = cfg.get("modules") or {}
        wx = weather.fetch(mods["weather"], cfg["timezone"]) if mods.get("weather") else None
        mk = markets.fetch(mods["markets"]) if mods.get("markets") else None
        report["raw"] = {"news": news_items, "videos": videos, "posts": posts, "weather": wx, "markets": mk}

    posts = select.pick_posts(posts, rules, w)
    picked, skipped = select.pick_news(news_items, rules, w, avoid=[p["text"][:140] for p in posts])
    vids = select.pick_videos(videos, rules, w, now)
    sections = select.assign_sections(picked + posts + vids, cfg["sections"])
    report["skipped"] = dict(skipped)
    report["counts"] = {"news": len(picked), "posts": len(posts), "videos": len(vids)}

    morning = []
    if wx:
        morning.append(template.weather_block(wx, weather.headline(wx)))
    if mk:
        morning.append(template.markets_block(mk, (cfg["modules"]["markets"] or {}).get("title", "Markets"), markets.headline(mk)))
    return template.page(cfg, sections, morning, now, tz), report
