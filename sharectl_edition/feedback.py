"""Thumbs up / thumbs down feedback, stored locally as JSON next to the config.

The edition page keeps clicks in the reader's browser (localStorage) and offers an
"Export feedback" link. The bot imports that file (or the user just tells the bot in chat,
and the bot calls `feedback add`). Weights then boost or demote sources, authors and topics.
"""
import json
import os
import re

UP, DOWN = 1.0, -1.0
EMPTY = {"sources": {}, "authors": {}, "sections": {}, "keywords": {}, "hidden": [], "seen": []}
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


def apply(w: dict, ev: dict) -> bool:
    """ev = {item_id, vote: 'up'|'down', source, author, section, title, ts}. Returns False if already seen."""
    key = f'{ev.get("item_id")}|{ev.get("vote")}|{ev.get("ts")}'
    if key in w["seen"]:
        return False
    w["seen"].append(key)
    v = UP if ev.get("vote") == "up" else DOWN if ev.get("vote") == "down" else 0
    if not v:
        return True
    bump = lambda d, k, x: d.__setitem__(k, round(d.get(k, 0) + x, 2))
    if ev.get("source"):
        bump(w["sources"], norm(ev["source"]), v)
    if ev.get("author"):
        bump(w["authors"], norm(ev["author"]), v)
    if ev.get("section"):
        bump(w["sections"], norm(ev["section"]), v * 0.5)
    kws = keywords(ev.get("title", ""))
    for k in kws:
        bump(w["keywords"], k, v / max(1, len(kws)))
    return True


def import_file(path: str, events_file: str) -> int:
    w = load(path)
    with open(events_file, encoding="utf-8") as f:
        evs = json.load(f)
    evs = evs.get("events", evs) if isinstance(evs, dict) else evs
    n = sum(apply(w, e) for e in evs)
    save(path, w)
    return n


def score(item: dict, w: dict) -> float:
    s = w["sources"].get(norm(item.get("source")), 0) + w["authors"].get(norm(item.get("author")), 0)
    s += w["sections"].get(norm(item.get("section")), 0)
    text = ((item.get("title") or "") + " " + (item.get("text") or "")).lower()
    s += sum(v for k, v in w["keywords"].items() if k and re.search(r"\b" + re.escape(k), text))
    return s


def is_hidden(item: dict, w: dict) -> bool:
    return any(norm(x) in w["hidden"] for x in (item.get("source"), item.get("author"), item.get("handle")) if x)
