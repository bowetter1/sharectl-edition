"""New readers must not inherit someone else's editorial preferences."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from sharectl_edition import config, feedback, select
from sharectl_edition.build import build

ROOT = Path(__file__).resolve().parents[1]


class NeutralDefaultsTests(unittest.TestCase):
    def test_starter_and_missing_settings_have_no_personal_choices(self):
        for cfg in (config.DEFAULTS, config.load(str(ROOT / 'config.example.json'))):
            with self.subTest(cfg=cfg):
                self.assertEqual(cfg['sources']['rss'], [])
                self.assertEqual(cfg['sources']['youtube'], [])
                self.assertFalse(cfg['sources']['x']['enabled'])
                self.assertEqual(cfg['sections'], [])
                self.assertEqual(cfg['rules']['boost_keywords'], [])
                self.assertEqual(cfg['rules']['mute_keywords'], [])
                self.assertIsNone(cfg['rules']['max_political'])
                self.assertEqual(cfg['modules'], {'weather': None, 'markets': None})
                self.assertEqual(cfg['publish']['target'], 'static')
                self.assertEqual(cfg['timezone'], 'UTC')

    def test_politics_is_allowed_unless_reader_sets_a_news_cap(self):
        items = [dict(id=str(i), kind='news', source=str(i), title=title, text='')
                 for i, title in enumerate(['Senate approves budget', 'Election results announced',
                                           'Governor visits coastal village'])]
        rules = copy.deepcopy(config.DEFAULTS['rules'])
        weights = copy.deepcopy(feedback.EMPTY)
        for limit, expected in [(None, 3), (0, 0), (1, 1)]:
            rules['max_political'] = limit
            kept, _ = select.pick_news(items, rules, weights)
            self.assertEqual(len(kept), expected)
        del rules['max_political']
        self.assertEqual(len(select.pick_news(items, rules, weights)[0]), 3)

    def test_video_topic_filter_requires_explicit_keywords(self):
        now = datetime.now(timezone.utc)
        video = dict(id='v', kind='video', source='channel', title='Election results explained',
                     published=now.isoformat())
        rules = copy.deepcopy(config.DEFAULTS['rules'])
        weights = copy.deepcopy(feedback.EMPTY)
        self.assertEqual(len(select.pick_videos([video], rules, weights, now)), 1)
        rules['mute_keywords'] = ['election']
        self.assertEqual(select.pick_videos([video], rules, weights, now), [])

    def test_existing_reader_preferences_are_preserved(self):
        chosen = {'timezone': 'Europe/Stockholm', 'name': 'Test reader',
                  'rules': {'max_political': 0, 'boost_keywords': ['gardening']}}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'config.json'
            p.write_text(json.dumps(chosen))
            cfg = config.load(str(p))
        self.assertEqual(cfg['rules']['max_political'], 0)
        self.assertEqual(cfg['rules']['boost_keywords'], ['gardening'])
        self.assertEqual(cfg['timezone'], chosen['timezone'])

    def test_empty_starter_builds_without_external_sources(self):
        cfg = config.load(str(ROOT / 'config.example.json'))
        with tempfile.TemporaryDirectory() as tmp:
            html, report = build(cfg, tmp)
        self.assertEqual(report['counts'], {'news': 0, 'posts': 0, 'videos': 0})
        self.assertNotIn('politics capped', html)
        self.assertNotIn('New York', html)
