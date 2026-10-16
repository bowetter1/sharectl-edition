import os
import unittest

from sharectl_edition.fetch import x

HERE = os.path.dirname(__file__)


class XTests(unittest.TestCase):
    def test_timeline_to_items(self):
        st, items = x.from_timeline(os.path.join(HERE, "fixtures", "x_timeline.json"))
        self.assertEqual([i["handle"] for i in items], ["ada", "cy"])  # short post dropped, repost unwrapped
        self.assertEqual(items[0]["link_out"], "https://example.com/agent")
        self.assertNotIn("t.co", items[0]["text"])
        self.assertEqual(items[1]["via"], "Ben Example")
        self.assertTrue(items[0]["author_photo"].endswith("_200x200.jpg"))


if __name__ == "__main__":
    unittest.main()
