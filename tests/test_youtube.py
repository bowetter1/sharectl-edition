import unittest
from unittest.mock import patch

from sharectl_edition import net
from sharectl_edition.fetch import youtube


FEED = '''<?xml version="1.0"?><feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
<title>Test Channel</title>
<entry>
<yt:videoId>dQw4w9WgXcQ</yt:videoId>
<title>Test Video</title>
<published>2026-10-15T12:00:00+00:00</published>
<media:group><media:description>Test description</media:description></media:group>
</entry>
</feed>'''


class YouTubeTests(unittest.TestCase):
    @patch.object(net, 'get')
    def test_fetch_channel_from_rss(self, get):
        def mock_get(url, timeout, browser=False):
            if '@testchannel' in url:
                return ('<meta property="og:title" content="Test Channel">'
                       '<meta property="og:image" content="https://example.com/avatar.jpg">'
                       'rel="canonical" href="https://www.youtube.com/channel/UCtest123456789012345678"')
            else:
                return FEED
        
        get.side_effect = mock_get
        
        stats, items = youtube.fetch_channel({'handle': '@testchannel', 'section': 'video'})
        
        self.assertTrue(stats['ok'])
        self.assertEqual(stats['videos'], 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['kind'], 'video')
        self.assertEqual(items[0]['title'], 'Test Video')
        self.assertEqual(items[0]['source'], 'yt-testchannel')
        self.assertIn('dQw4w9WgXcQ', items[0]['url'])

    @patch.object(net, 'get')
    def test_fetch_channel_scrapes_page_on_rss_failure(self, get):
        get.side_effect = [
            '<meta property="og:title" content="Test Channel">',
            net.FetchError('RSS unavailable')
        ]
        
        stats, items = youtube.fetch_channel({'handle': '@test', 'section': 'video'})
        
        # Should attempt both RSS and scraping but both fail
        self.assertFalse(stats['ok'])
        self.assertEqual(len(items), 0)


if __name__ == '__main__':
    unittest.main()
