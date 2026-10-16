"""Plain-language preferences: the reader tells their bot what they want more or less of.

The bot stores these preferences as weights (boost or demote sources, authors, topics)
in feedback.json or in config.json rules. No voting UI, no export needed.
"""
import json
import os
import re

UP, DOWN = 1.0, -1.0
EMPTY = {"sources": {}, "authors": {}, "sections": {}, "keywords": {}, "hidden": []}
STOP = set("about after again their there these those which would could should every under still being where while into from with that this have will your what when they them than then just more most over only some such very".split())


def keywords(text: str, n: int = 6) -> list[str]:
    ws = [w for w in re.findall(r"[a-z][a-z0-9+-]{3,}", (text or "").lower()) if w not in STOP]
    return list(dict.fromkeys(ws))[:n]


def norm(s) -> str:
    return (s or "").strip().lower().lstrip("@")


def load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            w = json.load(f)
        return {**json.loads(json.dumps(EMPTY)), **w}
    except Exception:
        return json.loads(json.dumps(EMPTY))


def save(path: str, w: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(w, f, ensure_ascii=False, indent=1)


def bump(w: dict, category: str, key: str, amount: float) -> None:
    """Adjust weight for a source, author, keyword, etc."""
    if category not in w:
        w[category] = {}
    key = norm(key)
    w[category][key] = round(w[category].get(key, 0) + amount, 2)


def hide(w: dict, identifier: str) -> None:
    """Hide a source, author, or handle."""
    key = norm(identifier)
    if key and key not in w.get("hidden", []):
        if "hidden" not in w:
            w["hidden"] = []
        w["hidden"].append(key)


def score(item: dict, w: dict) -> float:
    s = w["sources"].get(norm(item.get("source")), 0) + w["authors"].get(norm(item.get("author")), 0)
    s += w["sections"].get(norm(item.get("section")), 0)
    text = ((item.get("title") or "") + " " + (item.get("text") or "")).lower()
    s += sum(v for k, v in w["keywords"].items() if k and re.search(r"\b" + re.escape(k), text))
    return s


def is_hidden(item: dict, w: dict) -> bool:
    return any(norm(x) in w["hidden"] for x in (item.get("source"), item.get("author"), item.get("handle")) if x)
