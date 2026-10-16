import copy
import tempfile
import unittest
from unittest.mock import patch

from sharectl_edition import config, net
from sharectl_edition.build import collect
from sharectl_edition.fetch import news


FEED = '''<rss><channel>
<item><title>First story</title><link>https://example.com/first</link><description>Original summary</description></item>
<item><title>Repeated story</title><link>https://example.com/first</link><description>Repeated summary</description></item>
<item><title>Second story</title><link>https://example.com/second</link></item>
</channel></rss>'''
SOURCE = {'id': 'example', 'name': 'Example', 'url': 'https://example.com/rss', 'enrich': False}


class NewsTests(unittest.TestCase):
    @patch.object(net, 'get', return_value=FEED)
    def test_repeated_links_do_not_use_up_candidate_slots(self, get):
        stats, items = news.fetch_source(SOURCE, candidates=2)
        self.assertTrue(stats['ok'])
        self.assertEqual(stats['read'], 2)
        self.assertEqual([item['url'] for item in items],
                         ['https://example.com/first', 'https://example.com/second'])
        self.assertEqual(items[0]['title'], 'First story')
        self.assertEqual(items[0]['text'], 'Original summary')
        self.assertEqual(len({item['id'] for item in items}), 2)

    @patch.object(net, 'get', return_value=FEED)
    def test_collect_accepts_a_feed_with_repeated_articles(self, get):
        cfg = copy.deepcopy(config.DEFAULTS)
        cfg['sources']['rss'] = [SOURCE]
        with tempfile.TemporaryDirectory() as tmp:
            packet = collect(cfg, tmp)
        self.assertEqual(len(packet['items']), 2)
        self.assertEqual(packet['sources']['example']['read'], 2)

    @patch.object(net, 'get', return_value=FEED)
    def test_same_article_from_different_sources_is_left_for_the_editor(self, get):
        cfg = copy.deepcopy(config.DEFAULTS)
        cfg['sources']['rss'] = [SOURCE, {**SOURCE, 'id': 'other', 'name': 'Other'}]
        with tempfile.TemporaryDirectory() as tmp:
            packet = collect(cfg, tmp)
        self.assertEqual(len(packet['items']), 4)
        self.assertEqual(len({item['id'] for item in packet['items']}), 4)


if __name__ == '__main__':
    unittest.main()
