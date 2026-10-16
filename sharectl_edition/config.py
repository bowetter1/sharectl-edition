"""Load the edition config (JSON). Missing keys fall back to DEFAULTS."""
import copy
import json

DEFAULTS = {
    "name": "Reader",
    "greeting": "Good morning, {name}.",
    "timezone": "America/New_York",
    "language": "en",
    "strings": {},  # the agent's translation of the UI strings for a language that is not built in
    "sources": {"rss": [], "youtube": [], "x": {"enabled": False, "timeline_file": ""}},
    "sections": [],
    "rules": {
        "max_per_source": 3,
        "max_news": 24,
        "max_videos": 6,
        "max_per_channel": 2,
        "fresh_days": 14,
        "max_political": 2,
        "political_keywords": [],
        "boost_keywords": [],
        "mute_keywords": [],
        "require_image": False,
        "prefer_people": True,
    },
    "modules": {"weather": None, "markets": None},
    "publish": {"target": "static", "out": "site"},
    "feedback_file": "feedback.json",
}


def _merge(base, extra):
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        user = json.load(f)
    return _merge(copy.deepcopy(DEFAULTS), user)
