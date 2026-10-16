"""X (Twitter) posts from saved timeline JSON.

The AI fetches the timeline with its own X tools and saves the API v2 response:
    {"data": [posts], "includes": {"users": [...], "media": [...]}}

This module reads that file and returns post items.
"""
import html
import json
import re


def clean(t: str) -> str:
    """Remove t.co links and normalize whitespace."""
    t = html.unescape(t or "")
    t = re.sub(r"https://t\.co/\S+", "", t)
    return re.sub(r"[ \t]+", " ", t).strip()


def from_timeline(path: str, section: str = "") -> tuple[dict, list[dict]]:
    """Read X timeline JSON and return post items."""
    with open(path, encoding="utf-8") as f:
        tl = json.load(f)
    
    inc = tl.get("includes", {})
    users = {u["id"]: u for u in inc.get("users", [])}
    media = {m["media_key"]: m for m in inc.get("media", [])}
    posts = {p["id"]: p for p in inc.get("tweets", inc.get("posts", []))}
    
    items = []
    seen = set()
    
    for t in tl.get("data", []):
        # Handle retweets/reposts
        refs = {r["type"]: r["id"] for r in t.get("referenced_tweets", [])}
        src = t
        repost_id = refs.get("retweeted") or refs.get("reposted")
        if repost_id:
            src = posts.get(repost_id)
            if not src:
                continue
        
        # Skip short replies and duplicates
        if "replied_to" in refs and len(clean(t["text"])) < 40:
            continue
        if src["id"] in seen:
            continue
        seen.add(src["id"])
        
        # Extract post data
        u = users.get(src["author_id"], {})
        text = clean(src.get("note_tweet", {}).get("text") or src["text"])
        if len(text) < 20:
            continue
        
        # Get image
        img = ""
        for k in (src.get("attachments") or {}).get("media_keys", []):
            m = media.get(k, {})
            img = m.get("url") or m.get("preview_image_url") or ""
            if img:
                break
        
        # Get external link
        link = next((e.get("expanded_url") for e in (src.get("entities") or {}).get("urls", [])
                     if e.get("expanded_url") and "x.com/" not in e["expanded_url"] 
                     and "twitter.com/" not in e["expanded_url"]), "")
        
        handle = u.get("username", "")
        items.append({
            "id": "x-" + src["id"],
            "kind": "post",
            "source": "x-" + handle.lower(),
            "source_name": "X",
            "section": section,
            "title": "",
            "text": text[:600],
            "image": img,
            "url": f"https://x.com/{handle}/status/{src['id']}",
            "link_out": link,
            "published": src.get("created_at", ""),
            "author": u.get("name", handle),
            "handle": handle,
            "author_photo": (u.get("profile_image_url") or "").replace("_normal", "_200x200"),
            "via": users.get(t["author_id"], {}).get("name") if src is not t else ""
        })
    
    return {"x": {"ok": True, "read": len(tl.get("data", [])), "kept": len(items)}}, items
