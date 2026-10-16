"""Editorial selection: the reader's rules applied to fetched items.

Order of operations:
  1. drop hidden sources/authors and muted keywords
  2. rank each source's candidates by feedback score + boost keywords (feed order breaks ties)
  3. near-duplicate headlines across sources are dropped (first one wins)
  4. political stories are capped (keyword list is configurable)
  5. per-source caps, then a round-robin across sources up to max_news
  6. each item lands in a section by keywords, else its source's default section
"""
import collections
import re

from . import feedback

DEFAULT_POLITICAL = ["election", "senate", "congress", "republican", "democrat", "gop", "white house",
                     "governor", "ballot", "impeach", "partisan", "lawmakers", "trump", "biden", "harris"]
STOP = set("after before under between their there about would could should first years people".split())


def has(text: str, words: list[str]) -> bool:
    t = " " + (text or "").lower() + " "
    return any(re.search(r"(?<![a-z0-9])" + re.escape(w.lower()) + r"(?![a-z0-9])", t) for w in words if w)


def _words(t: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{3,}", (t or "").lower()) if w not in STOP}


def same_story(a: str, b: str) -> bool:
    """Near-duplicate headline test: token Jaccard similarity over normalized titles."""
    sa, sb = _words(a), _words(b)
    if not sa or not sb:
        return False
    intersection = len(sa & sb)
    union = len(sa | sb)
    jaccard = intersection / union if union > 0 else 0
    short_threshold = 0.75 if min(len(sa), len(sb)) <= 5 else 0.6
    return jaccard >= short_threshold


def classify(item: dict, sections: list[dict]) -> str:
    text = (item.get("title") or "") + " " + (item.get("text") or "")
    for s in sections:
        if s.get("keywords") and has(text, s["keywords"]) and item["kind"] in s.get("kinds", ["news", "post"]):
            return s["key"]
    return item.get("section") or (sections[-1]["key"] if sections else "news")


def _rank(items, w, boost):
    def key(ix):
        i, it = ix
        bonus = 1.0 if boost and has(it.get("title", "") + " " + it.get("text", ""), boost) else 0.0
        return (-(feedback.score(it, w) + bonus), i)
    return [it for _, it in sorted(enumerate(items), key=key)]


def round_robin(groups: dict, limit: int) -> list:
    out, k = [], 0
    while len(out) < limit and any(k < len(g) for g in groups.values()):
        for g in groups.values():
            if k < len(g) and len(out) < limit:
                out.append(g[k])
        k += 1
    return out


def pick_news(items: list[dict], rules: dict, w: dict, avoid: list[str] = ()) -> tuple[list, collections.Counter]:
    skipped = collections.Counter()
    political = rules.get("political_keywords") or DEFAULT_POLITICAL
    by_src = collections.defaultdict(list)
    for it in items:
        by_src[it["source"]].append(it)
    kept, seen_titles, pol = collections.defaultdict(list), list(avoid), 0
    for src, lst in by_src.items():
        cap = lst[0].get("cap") or (rules["max_per_source"] + (lst[0].get("priority") or 0))
        for it in _rank(lst, w, rules.get("boost_keywords")):
            text = it["title"] + " " + it.get("text", "")
            if feedback.is_hidden(it, w):
                skipped["hidden by you"] += 1
            elif has(text, rules.get("mute_keywords", [])):
                skipped["muted keyword"] += 1
            elif rules.get("require_image") and not it.get("image"):
                skipped["no image"] += 1
            elif any(same_story(it["title"], t) for t in seen_titles):
                skipped["same story as another source"] += 1
            elif len(kept[src]) >= cap:
                skipped["max per source"] += 1
            elif has(text, political) and pol >= rules.get("max_political", 2):
                skipped["politics cap"] += 1
            else:
                if has(text, political):
                    pol += 1
                kept[src].append(it)
                seen_titles.append(it["title"])
    prio = [it for src, lst in kept.items() for it in lst if lst and lst[0].get("priority")]
    rest = {s: l for s, l in kept.items() if not (l and l[0].get("priority"))}
    max_news_limit = rules["max_news"]
    prio_limited = prio[:max_news_limit]
    out = prio_limited + round_robin(rest, max(0, max_news_limit - len(prio_limited)))
    skipped["no room in the edition"] += sum(len(l) for l in kept.values()) - len(out)
    return out, skipped


def pick_videos(items: list[dict], rules: dict, w: dict, now) -> list[dict]:
    from datetime import datetime
    political = rules.get("political_keywords") or DEFAULT_POLITICAL
    by = collections.defaultdict(list)
    for it in items:
        if feedback.is_hidden(it, w) or has(it["title"], political) or has(it["title"], rules.get("mute_keywords", [])):
            continue
        age = (now - datetime.fromisoformat(it["published"])).days
        it["age_days"] = age
        by[it["source"]].append(it)
    groups = {}
    for src, lst in by.items():
        lst.sort(key=lambda c: c["age_days"])
        fresh = [c for c in lst if c["age_days"] <= rules["fresh_days"]][: rules["max_per_channel"]]
        groups[src] = fresh  # quiet channels are skipped rather than showing stale video
    groups = dict(sorted(groups.items(), key=lambda kv: -max((feedback.score(c, w) for c in kv[1]), default=0)))
    return round_robin(groups, rules["max_videos"])


def pick_posts(items: list[dict], rules: dict, w: dict) -> list[dict]:
    per = collections.Counter()
    out = []
    for it in sorted(items, key=lambda i: -(feedback.score(i, w) + min(i.get("likes", 0), 5000) / 5000)):
        if feedback.is_hidden(it, w) or has(it["text"], rules.get("mute_keywords", [])):
            continue
        if per[it["source"]] >= rules.get("max_per_x_account", 2):
            continue
        per[it["source"]] += 1
        out.append(it)
    return out[: rules.get("max_posts", 20)]


def assign_sections(items: list[dict], sections: list[dict]) -> list[dict]:
    """-> [{key,title,sub,color,items}] in config order, empty sections dropped."""
    buckets = collections.OrderedDict((s["key"], {**s, "items": []}) for s in sections)
    for it in items:
        k = classify(it, sections)
        if k not in buckets:
            buckets[k] = {"key": k, "title": k.title(), "items": []}
        buckets[k]["items"].append(it)
    return [b for b in buckets.values() if b["items"]]
