import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from sharectl_edition.fetch import x

HERE = os.path.dirname(__file__)


class XTests(unittest.TestCase):
    def setUp(self):
        self.timeline = json.loads(Path(HERE, 'fixtures', 'x_timeline.json').read_text())

    def import_timeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'timeline.json'
            path.write_text(json.dumps(self.timeline))
            return x.from_timeline(str(path))

    def test_timeline_to_items(self):
        st, items = x.from_timeline(os.path.join(HERE, "fixtures", "x_timeline.json"))
        self.assertEqual([i["handle"] for i in items], ["ada", "cy"])  # short post dropped, repost unwrapped
        self.assertEqual(items[0]["link_out"], "https://example.com/agent")
        self.assertNotIn("t.co", items[0]["text"])
        self.assertEqual(items[1]["via"], "Ben Example")
        self.assertTrue(items[0]["author_photo"].endswith("_200x200.jpg"))

    def test_repost_uses_expanded_original_details(self):
        original = self.timeline['includes']['tweets'][0]
        original.update(attachments={'media_keys': ['photo']}, public_metrics={'like_count': 42},
                        entities={'urls': [{'expanded_url': 'https://example.com/original'}]})
        self.timeline['includes']['media'] = [{'media_key': 'photo', 'url': 'https://example.com/photo.jpg'}]
        _, items = self.import_timeline()
        repost = next(item for item in items if item['id'] == 'x-3')
        self.assertEqual(repost['text'], original['text'])
        self.assertEqual(repost['author'], 'Cy Example')
        self.assertEqual(repost['via'], 'Ben Example')
        self.assertEqual(repost['url'], 'https://x.com/cy/status/3')
        self.assertEqual(repost['published'], original['created_at'])
        self.assertEqual(repost['image'], 'https://example.com/photo.jpg')
        self.assertEqual(repost['link_out'], 'https://example.com/original')
        self.assertEqual(repost['likes'], 42)

    def test_repeated_reposts_and_original_are_only_imported_once(self):
        repost = copy.deepcopy(self.timeline['data'][1])
        repost.update(id='5', author_id='u1')
        self.timeline['data'].extend([repost, self.timeline['includes']['tweets'][0]])
        _, items = self.import_timeline()
        self.assertEqual([item['id'] for item in items], ['x-1', 'x-3'])
        self.assertEqual(items[1]['via'], 'Ben Example')

    def test_missing_repost_expansion_is_skipped(self):
        self.timeline['includes']['tweets'] = []
        self.timeline['data'][1]['text'] = 'RT @cy: This truncated repost should not be credited to Ben.'
        _, items = self.import_timeline()
        self.assertEqual([item['id'] for item in items], ['x-1'])

    def test_legacy_saved_timeline_still_imports(self):
        self.timeline['includes']['posts'] = self.timeline['includes'].pop('tweets')
        self.timeline['data'][1]['referenced_tweets'][0]['type'] = 'reposted'
        _, items = self.import_timeline()
        self.assertEqual([item['id'] for item in items], ['x-1', 'x-3'])
        self.assertEqual(items[1]['via'], 'Ben Example')


if __name__ == "__main__":
    unittest.main()
