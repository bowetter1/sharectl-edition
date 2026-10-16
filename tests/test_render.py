import unittest
from datetime import datetime, timezone


def n(src, title, **kw):
    return {"id": f"{src}-{title}", "kind": "news", "source": src, "source_name": src, "title": title, "text": "",
            "url": "https://example.com/" + title.replace(" ", "-"), "image": "", "published": "", "author": "", **kw}


class RenderTests(unittest.TestCase):
    def test_render_escapes_and_no_voting(self):
        from zoneinfo import ZoneInfo
        from sharectl_edition.render import template
        tz = ZoneInfo("America/New_York")
        it = n("a", "<script>alert(1)</script> headline", image="https://example.com/i.jpg", author="Jane Doe",
               published=datetime.now(timezone.utc).isoformat())
        html = template.page({"greeting": "Good morning, {name}.", "name": "Sam"},
                             [{"key": "us", "title": "US", "items": [it, n("b", "Second story")]}], [], datetime.now(tz), tz)
        self.assertNotIn("<script>alert(1)", html)
        self.assertIn("Good morning, Sam.", html)
        self.assertNotIn('data-vote', html)
        self.assertIn("Want changes? Just tell your agent.", html)
        self.assertIn('lang="en"', html)

    def test_render_swedish(self):
        from zoneinfo import ZoneInfo
        from sharectl_edition.render import template
        tz = ZoneInfo("Europe/Stockholm")
        when = datetime(2026, 10, 16, 7, 26, tzinfo=timezone.utc).isoformat()  # 09:26 in Stockholm
        it = n("a", "Rubrik", image="https://example.com/i.jpg", author="Anna Svensson", published=when)
        html = template.page({"greeting": "God morgon, {name}.", "name": "Sam", "language": "sv"},
                             [{"key": "se", "title": "Sverige", "items": [it, n("b", "Andra storyn", published=when)]}], [],
                             datetime(2026, 10, 16, 9, 0, tzinfo=tz), tz)
        self.assertIn('lang="sv"', html)
        self.assertIn("Fredag 16 oktober 2026", html)
        self.assertIn("09:26", html)
        self.assertIn("Det var allt värt att se i dag.", html)
        self.assertIn("Toppnyhet", html)

    def test_render_any_language_from_config_strings(self):
        """A language that is not built in: the agent's translation in config.strings is used, gaps fall back to English."""
        from zoneinfo import ZoneInfo
        from sharectl_edition.render import template
        tz = ZoneInfo("Europe/Berlin")
        when = datetime(2026, 10, 16, 7, 26, tzinfo=timezone.utc).isoformat()
        strings = {"top_story_nav": "Aufmacher", "the_end": "Das war alles für heute.", "time": "%H:%M",
                   "days": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
                   "months": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
                              "Oktober", "November", "Dezember"], "date": "{day}, {d}. {month} {y}",
                   "skip_reasons": {"max per source": "Limit pro Quelle"}}
        it = n("a", "Schlagzeile", image="https://example.com/i.jpg", author="Anna Müller", published=when)
        html = template.page({"greeting": "Guten Morgen, {name}.", "name": "Sam", "language": "de", "strings": strings},
                             [{"key": "de", "title": "Deutschland", "items": [it, n("b", "Zweite", published=when)]}], [],
                             datetime(2026, 10, 16, 9, 0, tzinfo=tz), tz, {"skipped": {"max per source": 4}})
        self.assertIn('lang="de"', html)
        self.assertIn("Freitag, 16. Oktober 2026", html)
        self.assertIn("Aufmacher", html)
        self.assertIn("Das war alles für heute.", html)
        self.assertIn("Limit pro Quelle", html)
        self.assertIn("Latest", html)  # not translated: English fallback

    def test_org_bylines_are_not_people(self):
        from sharectl_edition.fetch import news
        self.assertTrue(news.looks_like_org("Breaking Media AB"))
        self.assertTrue(news.looks_like_org("SVT Nyheter"))
        self.assertFalse(news.looks_like_org("Gabriel Abrahamsson"))
        self.assertFalse(news.looks_like_org("Jane Doe"))


class NetworkErrorTests(unittest.TestCase):
    def test_fetch_error_raised(self):
        from sharectl_edition import net
        with self.assertRaises(net.FetchError):
            net.get("http://invalid-domain-that-does-not-exist-12345.com/")


if __name__ == "__main__":
    unittest.main()
