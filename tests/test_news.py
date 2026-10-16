import copy
import email.message
import io
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


class MetaTests(unittest.TestCase):
    def test_quotes_inside_a_value_do_not_cut_it_short(self):
        cases = [
            ('<meta property="og:title" content="Trump\'s new plan won\'t pass">', 'og:title', "Trump's new plan won't pass"),
            ('<meta property=\'og:description\' content=\'He said "no" today\'>', 'og:description', 'He said "no" today'),
            ('<meta content="Biden\'s reply" property="og:title">', 'og:title', "Biden's reply"),
            ('<meta name="description" content="">', 'description', ''),
        ]
        for page, prop, expected in cases:
            with self.subTest(page=page):
                self.assertEqual(news._meta(page, prop), expected)


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, content_type: str):
        super().__init__(body)
        self.headers = email.message.Message()
        self.headers['Content-Type'] = content_type


LATIN1_FEED = ('<?xml version="1.0" encoding="ISO-8859-1"?><rss><channel><item><title>Rösträkning i Göteborg</title>'
               '<link>https://example.se/a</link></item></channel></rss>').encode('latin-1')


class EncodingTests(unittest.TestCase):
    def fetch(self, body, content_type):
        with patch('urllib.request.urlopen', return_value=FakeResponse(body, content_type)):
            return net.get('https://example.se/feed')

    def test_feed_declaring_its_encoding_keeps_its_letters(self):
        for content_type in ('application/rss+xml', 'text/xml; charset=ISO-8859-1'):
            with self.subTest(content_type=content_type):
                items = news.parse_feed(self.fetch(LATIN1_FEED, content_type))
                self.assertEqual(items[0]['title'], 'Rösträkning i Göteborg')

    def test_html_meta_charset_is_used_without_a_header_charset(self):
        page = '<html><head><meta charset="iso-8859-1"><title>Smörgåsbord</title>'.encode('latin-1')
        self.assertIn('Smörgåsbord', self.fetch(page, 'text/html'))

    def test_server_charset_wins_and_unknown_names_fall_back_to_utf8(self):
        self.assertEqual(net.decode('Malmö'.encode(), 'utf-8'), 'Malmö')
        self.assertEqual(net.decode(b'<?xml version="1.0" encoding="no-such-codec"?><a/>', None),
                         '<?xml version="1.0" encoding="no-such-codec"?><a/>')


if __name__ == '__main__':
    unittest.main()
