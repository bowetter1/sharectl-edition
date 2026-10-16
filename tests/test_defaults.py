"""New readers must not inherit someone else's editorial preferences."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from sharectl_edition import config, feedback
from sharectl_edition.build import collect

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

    def test_empty_starter_fetches_without_external_sources(self):
        cfg = config.load(str(ROOT / 'config.example.json'))
        with tempfile.TemporaryDirectory() as tmp:
            packet = collect(cfg, tmp)
        self.assertEqual(packet['items'], [])
        self.assertEqual(packet['reader']['rules']['boost_keywords'], [])
