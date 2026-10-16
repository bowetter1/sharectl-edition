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
                                          "OpenAI's new reasoning model released to developers today"))
        self.assertFalse(select.same_story("Fed holds interest rates steady", "Apple unveils new iPad lineup"))
        out, sk = select.pick_news([n("a", "OpenAI releases new reasoning model for developers"),
                                    n("b", "OpenAI's new reasoning model released to developers today")], RULES, empty())
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
        feedback.apply(w, {"item_id": "x", "vote": "up", "source": "b", "title": "", "ts": 1})
        items = [n("a", "Alpha story on farming"), n("b", "Beta story on sailing")]
        out, _ = select.pick_news(items, {**RULES, "max_news": 10}, w)
        self.assertEqual(len(out), 2)
        w["hidden"].append("a")
        out, sk = select.pick_news(items, RULES, w)
        self.assertEqual([i["source"] for i in out], ["b"])

    def test_feedback_keywords(self):
        w = empty()
        feedback.apply(w, {"item_id": "1", "vote": "down", "title": "Roadster launch delayed again", "ts": 1})
        self.assertLess(feedback.score({"title": "Roadster prototype spotted", "source": "z"}, w), 0)
        self.assertFalse(feedback.apply(w, {"item_id": "1", "vote": "down", "title": "Roadster launch delayed again", "ts": 1}))

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


class RenderTests(unittest.TestCase):
    def test_render_escapes_and_has_thumbs_only(self):
        from zoneinfo import ZoneInfo
        from sharectl_edition.render import template
        tz = ZoneInfo("America/New_York")
        it = n("a", "<script>alert(1)</script> headline", image="https://example.com/i.jpg", author="Jane Doe",
               published=datetime.now(timezone.utc).isoformat())
        html = template.page({"greeting": "Good morning, {name}.", "name": "Sam"},
                             [{"key": "us", "title": "US", "items": [it, n("b", "Second story")]}], [], datetime.now(tz), tz)
        self.assertNotIn("<script>alert(1)", html)
        self.assertIn("Good morning, Sam.", html)
        self.assertIn('data-vote="up"', html)
        self.assertNotIn('class="why', html)
        self.assertNotIn("data-vote=\"more", html)


if __name__ == "__main__":
    unittest.main()
