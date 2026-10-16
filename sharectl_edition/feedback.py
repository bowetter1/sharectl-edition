"""Plain-language preferences: the reader tells their bot what they want more or less of.

The bot stores these preferences as weights (boost or demote sources, authors, topics)
in feedback.json or in config.json rules. No voting UI, no export needed.
"""
import json
import os

EMPTY = {"sources": {}, "authors": {}, "sections": {}, "keywords": {}, "hidden": []}


def norm(s) -> str:
    return (s or "").strip().lower().lstrip("@")


def load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            w = json.load(f)
        return {**json.loads(json.dumps(EMPTY)), **w}
    except FileNotFoundError:
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
