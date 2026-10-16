import unittest
from datetime import datetime, timezone


def n(src, title, **kw):
    return {"id": f"{src}-{title}", "kind": "news", "source": src, "source_name": src, "title": title, "text": "",
            "url": "https://example.com/" + title.replace(" ", "-"), "image": "", "published": "", "author": "", **kw}


class RenderTests(unittest.TestCase):
    def test_render_escapes_html(self):
        from zoneinfo import ZoneInfo
        from sharectl_edition.render import template
        tz = ZoneInfo("UTC")
        it = n("a", "<script>alert(1)</script> headline", image="https://example.com/i.jpg", author="Jane Doe",
               published=datetime.now(timezone.utc).isoformat())
        html = template.page({"greeting": "Good morning, {name}.", "name": "Sam", "timezone": "UTC"},
                             [{"key": "news", "title": "News", "items": [it, n("b", "Second story")]}],
                             datetime.now(tz), tz)
        self.assertNotIn("<script>alert(1)", html)
        self.assertIn("Good morning, Sam.", html)
        self.assertIn("Want changes? Just tell your AI.", html)
        self.assertIn('lang="en"', html)

    def test_org_bylines(self):
        from sharectl_edition.fetch import news
        self.assertTrue(news.looks_like_org("Breaking Media AB"))
        self.assertTrue(news.looks_like_org("SVT Nyheter"))
        self.assertFalse(news.looks_like_org("Gabriel Abrahamsson"))
        self.assertFalse(news.looks_like_org("Jane Doe"))


if __name__ == "__main__":
    unittest.main()
