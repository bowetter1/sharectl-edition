import json
import tempfile
import unittest
from pathlib import Path

from sharectl_edition.fetch import x


TIMELINE = {
    "data": [
        {
            "id": "1234567890",
            "text": "This is a test post about AI and machine learning",
            "author_id": "user1",
            "created_at": "2026-10-15T12:00:00.000Z",
            "public_metrics": {"like_count": 5}
        }
    ],
    "includes": {
        "users": [
            {
                "id": "user1",
                "username": "testuser",
                "name": "Test User",
                "profile_image_url": "https://example.com/avatar_normal.jpg"
            }
        ]
    }
}


class XTests(unittest.TestCase):
    def test_from_timeline_basic(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(TIMELINE, f)
            path = f.name
        
        try:
            stats, items = x.from_timeline(path, 'social')
            
            self.assertTrue(stats['x']['ok'])
            self.assertEqual(stats['x']['read'], 1)
            self.assertEqual(stats['x']['kept'], 1)
            self.assertEqual(len(items), 1)
            
            item = items[0]
            self.assertEqual(item['kind'], 'post')
            self.assertEqual(item['source'], 'x-testuser')
            self.assertEqual(item['author'], 'Test User')
            self.assertEqual(item['handle'], 'testuser')
            self.assertIn('AI and machine learning', item['text'])
            self.assertIn('testuser/status/1234567890', item['url'])
        finally:
            Path(path).unlink()

    def test_from_timeline_filters_short_posts(self):
        short_timeline = {
            "data": [{"id": "1", "text": "Short", "author_id": "u1"}],
            "includes": {"users": [{"id": "u1", "username": "test", "name": "T"}]}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(short_timeline, f)
            path = f.name
        
        try:
            stats, items = x.from_timeline(path, 'social')
            self.assertEqual(len(items), 0)
        finally:
            Path(path).unlink()


if __name__ == '__main__':
    unittest.main()
