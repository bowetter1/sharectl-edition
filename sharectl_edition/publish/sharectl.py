"""Optional: POST the edition to a sharectl publisher (any HTTP endpoint that accepts an HTML body).

Config: {"target": "sharectl", "url": "https://.../edition", "token_env": "SHARECTL_TOKEN"}
The token is read from the environment, never from the config file.
"""
import os
import urllib.request


def post(html_text: str, url: str, token_env: str = "SHARECTL_TOKEN", date: str = "") -> int:
    headers = {"Content-Type": "text/html; charset=utf-8", "X-Edition-Date": date}
    if os.environ.get(token_env):
        headers["Authorization"] = "Bearer " + os.environ[token_env]
    req = urllib.request.Request(url, data=html_text.encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status
