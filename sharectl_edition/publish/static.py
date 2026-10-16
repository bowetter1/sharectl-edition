"""Write the edition as a static folder: index.html (today) + YYYY-MM-DD/index.html (archive)."""
import os


def write(html_text: str, out: str, date: str) -> str:
    os.makedirs(os.path.join(out, date), exist_ok=True)
    for p in (os.path.join(out, "index.html"), os.path.join(out, date, "index.html")):
        with open(p, "w", encoding="utf-8") as f:
            f.write(html_text)
    return os.path.join(out, "index.html")
