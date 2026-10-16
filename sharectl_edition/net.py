"""Tiny HTTP helper (stdlib only). Identifies itself honestly and never sends cookies or credentials."""
import gzip
import urllib.request
import urllib.robotparser
from functools import lru_cache
from urllib.parse import urlsplit

UA = "sharectl-edition/0.1 (+https://github.com/bowetter1/sharectl-edition; personal news reader)"
# Some sites only serve feeds/OG tags to browser-like agents; we still identify as a reader in a comment.
BROWSER_UA = "Mozilla/5.0 (compatible; sharectl-edition/0.1; personal news reader)"


def get(url: str, timeout: int = 15, browser: bool = False) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": BROWSER_UA if browser else UA,
        "Accept-Encoding": "gzip",
        "Accept-Language": "en-US,en;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(3_000_000)
            if r.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            charset = r.headers.get_content_charset() or "utf-8"
            return data.decode(charset, "replace")
    except Exception:
        return ""


@lru_cache(maxsize=256)
def _robots(host_root: str):
    rp = urllib.robotparser.RobotFileParser()
    txt = get(host_root + "/robots.txt", 8)
    rp.parse(txt.splitlines())
    return rp


def allowed(url: str) -> bool:
    """Respect robots.txt before reading an article page for its headline/image/byline."""
    p = urlsplit(url)
    try:
        return _robots(f"{p.scheme}://{p.netloc}").can_fetch(UA, url)
    except Exception:
        return True
