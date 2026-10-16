"""X (Twitter) posts. Optional.

This package never logs in to X. The user's bot fetches the home timeline (or list/search results)
with its own X tools and saves the raw API v2 response as JSON:
    {"data": [posts], "includes": {"users": [...], "media": [...], "tweets": [...]}}
This module turns that file into edition items.
Legacy saved exports using includes.posts and the reposted reference type are also accepted.
"""
import html
import json
import re


def clean(t: str) -> str:
    t = html.unescape(t or "")
    t = re.sub(r"https://t\.co/\S+", "", t)
    return re.sub(r"[ \t]+", " ", t).strip()


def from_timeline(path: str, section: str = "") -> tuple[dict, list[dict]]:
    with open(path, encoding="utf-8") as f:
        tl = json.load(f)
    inc = tl.get("includes", {})
    users = {u["id"]: u for u in inc.get("users", [])}
    media = {m["media_key"]: m for m in inc.get("media", [])}
    posts = {p["id"]: p for p in inc.get("tweets", inc.get("posts", []))}
    items, seen = [], set()
    for t in tl.get("data", []):
        refs = {r["type"]: r["id"] for r in t.get("referenced_tweets", [])}
        src = t
        repost_id = refs.get("retweeted") or refs.get("reposted")
        if repost_id:
            src = posts.get(repost_id)
            if not src:
                continue
        if "replied_to" in refs and len(clean(t["text"])) < 40:
            continue
        if src["id"] in seen:
            continue
        seen.add(src["id"])
        u = users.get(src["author_id"], {})
        text = clean(src.get("note_tweet", {}).get("text") or src["text"])
        if len(text) < 20:
            continue
        img = ""
        for k in (src.get("attachments") or {}).get("media_keys", []):
            m = media.get(k, {})
            img = m.get("url") or m.get("preview_image_url") or ""
            if img:
                break
        link = next((e.get("expanded_url") for e in (src.get("entities") or {}).get("urls", [])
                     if e.get("expanded_url") and "x.com/" not in e["expanded_url"] and "twitter.com/" not in e["expanded_url"]), "")
        pm = src.get("public_metrics", {})
        handle = u.get("username", "")
        items.append({
            "id": "x-" + src["id"], "kind": "post", "source": "x-" + handle.lower(), "source_name": "X",
            "section": section, "title": "", "text": text[:600], "image": img,
            "url": f"https://x.com/{handle}/status/{src['id']}", "link_out": link,
            "published": src.get("created_at", ""), "author": u.get("name", handle), "handle": handle,
            "author_photo": (u.get("profile_image_url") or "").replace("_normal", "_200x200"),
            "via": users.get(t["author_id"], {}).get("name") if src is not t else "",
            "likes": pm.get("like_count", 0), "lang": src.get("lang", ""),
        })
    return {"x": {"ok": True, "read": len(tl.get("data", [])), "kept": len(items)}}, items
