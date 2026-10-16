"""The AI decides; Python validates provenance and renders without reselection."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sharectl_edition import cli, config, feedback, net
from sharectl_edition.build import build, collect


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cfg = copy.deepcopy(config.DEFAULTS)
        self.cfg.update(sections=[{'key': 'news', 'title': 'News'}], language='sv')
        self.cfg['rules'].update(max_news=0, mute_keywords=['Sailing'])
        self.cfg['feedback_file'] = 'saved-feedback.json'
        self.weights = {**copy.deepcopy(feedback.EMPTY), 'sources': {'a': 5}, 'hidden': ['b']}
        (self.root / 'saved-feedback.json').write_text(json.dumps(self.weights))
        self.raw = {'news': [self.item('a'), self.item('b')], 'posts': [], 'videos': []}
        self.raw_path = self.root / 'raw.json'
        self.raw_path.write_text(json.dumps(self.raw))
        self.packet = collect(self.cfg, str(self.root), str(self.raw_path))
        self.items = self.root / 'candidates.json'
        self.items.write_text(json.dumps(self.packet))
        self.selection = {'batch_id': self.packet['batch_id'], 'lead_id': 'b',
                          'items': [{'id': 'b', 'section': 'news'}, {'id': 'a', 'section': 'news'}]}
        self.selection_path = self.root / 'selection.json'

    def item(self, ident):
        return {'id': ident, 'kind': 'news', 'source': ident, 'source_name': ident,
                'title': 'Sailing ' + ident, 'text': 'Original summary',
                'url': 'https://example.com/' + ident, 'image': '', 'author': '',
                'published': '2026-10-16T07:00:00+00:00'}

    def render(self):
        self.selection_path.write_text(json.dumps(self.selection))
        return build(self.cfg, str(self.root), str(self.items), str(self.selection_path))

    def test_preferences_and_candidates_survive_without_automatic_filtering(self):
        self.assertEqual(self.packet['reader']['feedback'], self.weights)
        self.assertEqual(self.packet['reader']['rules'], self.cfg['rules'])
        self.assertEqual(self.packet['items'], self.raw['news'])
        self.assertNotIn('publish', self.packet['reader'])
        self.assertNotIn('timeline_file', self.packet['reader']['sources']['x'])
        before = (self.root / 'saved-feedback.json').read_bytes()
        html, report = self.render()
        self.assertEqual(report['selected_ids'], ['b', 'a'])
        self.assertEqual(report['lead_id'], 'b')
        self.assertLess(html.index('Sailing b'), html.index('Sailing a'))
        self.assertIn('Original summary', html)
        self.assertIn('AI-redaktör', html)
        self.assertEqual((self.root / 'saved-feedback.json').read_bytes(), before)

    def test_rejects_invalid_selection_before_writing(self):
        changes = [
            {'items': []},
            {'batch_id': 'another-batch'},
            {'items': [{'id': 'invented', 'section': 'news'}]},
            {'items': [{'id': 'a', 'section': 'unknown'}]},
            {'items': [{'id': 'a', 'section': 'news'}] * 2},
            {'items': [{'id': 'a', 'section': 'news', 'url': 'https://invented.test'}]},
            {'lead_id': 'missing'},
        ]
        original = copy.deepcopy(self.selection)
        for change in changes:
            with self.subTest(change=change):
                self.selection = {**original, **change}
                with self.assertRaises(ValueError):
                    self.render()

    def test_new_preferences_require_a_new_editorial_pass(self):
        feedback.save(str(self.root / 'saved-feedback.json'), {**self.weights, 'hidden': ['a']})
        with self.assertRaisesRegex(ValueError, 'preferences changed'):
            self.render()

    def test_modified_packet_is_rejected(self):
        self.packet['items'][0]['title'] = 'Changed after selection'
        self.items.write_text(json.dumps(self.packet))
        with self.assertRaisesRegex(ValueError, 'Invalid candidate'):
            self.render()

    def test_no_implicit_build_or_network_during_render(self):
        with self.assertRaisesRegex(ValueError, 'Fetch candidates first'):
            build(self.cfg)
        with patch.object(net, 'get', side_effect=AssertionError('render must be offline')):
            self.render()

    def test_video_only_selection(self):
        self.raw['news'] = []
        video = self.item('v')
        video.update(kind='video')
        self.raw['videos'] = [video]
        self.raw_path.write_text(json.dumps(self.raw))
        self.packet = collect(self.cfg, str(self.root), str(self.raw_path))
        self.items.write_text(json.dumps(self.packet))
        self.selection = {'batch_id': self.packet['batch_id'], 'lead_id': None,
                          'items': [{'id': 'v', 'section': 'news'}]}
        html, report = self.render()
        self.assertEqual(report['counts']['videos'], 1)
        self.assertIn('Sailing v', html)

    def test_failed_fetch_cannot_replace_previous_edition(self):
        cfg = self.root / 'config.json'
        self.cfg['sources']['rss'] = [{'id': 'bad', 'name': 'Bad', 'url': 'https://example.com/rss'}]
        cfg.write_text(json.dumps(self.cfg))
        with patch.object(net, 'get', side_effect=net.FetchError('offline')):
            self.assertEqual(cli.main(['fetch', '--config', str(cfg), '--out', str(self.items)]), 1)
        empty = json.loads(self.items.read_text())
        self.selection_path.write_text(json.dumps({'batch_id': empty['batch_id'], 'items': [], 'lead_id': None}))
        out = self.root / 'site'; out.mkdir()
        (out / 'index.html').write_text('Previous edition')
        result = subprocess.run([sys.executable, '-m', 'sharectl_edition', 'build', '--config', str(cfg),
                                 '--items', str(self.items), '--selection', str(self.selection_path), '--out', str(out)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((out / 'index.html').read_text(), 'Previous edition')

    def test_malformed_feedback_is_not_silently_discarded(self):
        (self.root / 'saved-feedback.json').write_text('{broken')
        with self.assertRaises(ValueError):
            collect(self.cfg, str(self.root), str(self.raw_path))


if __name__ == '__main__':
    unittest.main()
