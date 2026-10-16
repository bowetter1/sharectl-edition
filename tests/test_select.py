import unittest
from datetime import datetime, timedelta, timezone

from sharectl_edition import feedback, select

RULES = {"max_per_source": 2, "max_news": 10, "max_political": 1, "political_keywords": [], "boost_keywords": [],
         "mute_keywords": ["horoscope"], "require_image": False, "max_videos": 3, "max_per_channel": 1, "fresh_days": 14}


def n(src, title, **kw):
    return {"id": f"{src}-{title}", "kind": "news", "source": src, "source_name": src, "title": title, "text": "",
            "url": "https://example.com/" + title.replace(" ", "-"), "image": "", "published": "", "author": "", **kw}


def empty():
    return feedback.load("/nonexistent/feedback.json")


class SelectTests(unittest.TestCase):
    def test_per_source_cap(self):
        items = [n("a", f"Story number {i} about gardening tools") for i in range(5)]
        out, skipped = select.pick_news(items, RULES, empty())
        self.assertLessEqual(len(out), 2)

    def test_near_duplicate_headlines(self):
        self.assertTrue(select.same_story("OpenAI releases new reasoning model for developers",
                                          "OpenAI announces new reasoning model for developers today"))
        self.assertFalse(select.same_story("Fed holds interest rates steady", "Apple unveils new iPad lineup"))
        self.assertFalse(select.same_story("Tesla stock rises today", "Google announces new Pixel phone"))
        self.assertFalse(select.same_story("New AI model", "Different product launch"))
        out, sk = select.pick_news([n("a", "OpenAI releases new reasoning model for developers"),
                                    n("b", "OpenAI announces new reasoning model for developers today")], RULES, empty())
        self.assertEqual(len(out), 1)
        self.assertEqual(sk["same story as another source"], 1)

    def test_political_cap_and_mute(self):
        items = [n("a", "Senate passes budget bill"), n("b", "Congress debates election rules"),
                 n("c", "Your daily horoscope"), n("d", "New battery chemistry doubles range")]
        out, sk = select.pick_news(items, RULES, empty())
        titles = [i["title"] for i in out]
        self.assertEqual(sk["politics cap"], 1)
        self.assertNotIn("Your daily horoscope", titles)
        self.assertIn("New battery chemistry doubles range", titles)

    def test_feedback_reorders_and_hides(self):
        w = empty()
        feedback.bump(w, "sources", "b", 1.0)
        items = [n("a", "Alpha story on farming"), n("b", "Beta story on sailing")]
        out, _ = select.pick_news(items, {**RULES, "max_news": 10}, w)
        self.assertEqual(len(out), 2)
        feedback.hide(w, "a")
        out, sk = select.pick_news(items, RULES, w)
        self.assertEqual([i["source"] for i in out], ["b"])

    def test_feedback_keywords(self):
        w = empty()
        feedback.bump(w, "keywords", "roadster", -1.0)
        self.assertLess(feedback.score({"title": "Roadster prototype spotted", "source": "z", "text": ""}, w), 0)

    def test_sections_by_keyword(self):
        secs = [{"key": "ai", "title": "AI", "keywords": ["openai", "llm"]}, {"key": "us", "title": "US", "keywords": []}]
        out = select.assign_sections([n("a", "OpenAI ships an update", section="us"), n("b", "Hurricane season ends", section="us")], secs)
        self.assertEqual([(s["key"], len(s["items"])) for s in out], [("ai", 1), ("us", 1)])

    def test_videos_fresh_and_capped(self):
        now = datetime.now(timezone.utc)
        v = lambda ch, d: {"id": f"{ch}{d}", "kind": "video", "source": ch, "title": f"Video {ch} {d}",
                           "published": (now - timedelta(days=d)).isoformat()}
        out = select.pick_videos([v("c1", 1), v("c1", 2), v("c2", 3), v("c3", 40)], RULES, empty(), now)
        self.assertEqual(sorted(i["source"] for i in out), ["c1", "c2"])

    def test_priority_sources_count_toward_cap(self):
        items = [n("prio", f"Priority story {i}", priority=2) for i in range(5)]
        items += [n("regular", f"Regular story {i}") for i in range(5)]
        rules = {**RULES, "max_news": 6}
        out, _ = select.pick_news(items, rules, empty())
        prio_count = sum(1 for i in out if i["source"] == "prio")
        self.assertLessEqual(len(out), 6)
        self.assertGreater(prio_count, 0)


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
        self.assertIn("Want changes? Just tell your bot.", html)


class NetworkErrorTests(unittest.TestCase):
    def test_fetch_error_raised(self):
        from sharectl_edition import net
        with self.assertRaises(net.FetchError):
            net.get("http://invalid-domain-that-does-not-exist-12345.com/")


if __name__ == "__main__":
    unittest.main()
