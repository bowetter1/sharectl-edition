"""The AI decides; Python validates and renders."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sharectl_edition import config, feedback, net
from sharectl_edition.build import collect, render_selection, load_candidates, load_selection


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cfg = copy.deepcopy(config.DEFAULTS)
        self.cfg.update(sections=[{'key': 'news', 'title': 'News'}])
        self.cfg['sources'].update({'youtube': [], 'x': {'enabled': False, 'timeline_file': '', 'section': ''}})
        self.cfg['rules'].update(mute_keywords=['Sailing'])
        self.cfg['feedback_file'] = 'feedback.json'
        self.weights = {**copy.deepcopy(feedback.EMPTY), 'sources': {'a': 5}, 'hidden': ['b']}
        (self.root / 'feedback.json').write_text(json.dumps(self.weights))
        
        items = [self.item('a'), self.item('b')]
        # reader_settings removes timeline_file (private path)
        reader_sources = copy.deepcopy(self.cfg['sources'])
        reader_sources['x'].pop('timeline_file', None)
        
        self.packet = {
            'version': 1,
            'date': '2026-10-16T07:00:00+00:00',
            'reader': {'feedback': self.weights, 'rules': self.cfg['rules'], 
                       'sources': reader_sources, 'sections': self.cfg['sections'],
                       'name': 'Reader', 'greeting': 'Good morning, {name}.', 'timezone': 'UTC'},
            'sources': {'a': {'ok': True, 'read': 1}, 'b': {'ok': True, 'read': 1}},
            'items': items
        }
        import hashlib
        payload = {key: value for key, value in self.packet.items() if key != 'batch_id'}
        self.packet['batch_id'] = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        
        self.items_path = self.root / 'candidates.json'
        self.items_path.write_text(json.dumps(self.packet))
        
        self.selection = {'batch_id': self.packet['batch_id'], 'lead_id': 'b',
                          'items': [{'id': 'b', 'section': 'news'}, {'id': 'a', 'section': 'news'}]}
        self.selection_path = self.root / 'selection.json'

    def item(self, ident):
        return {'id': ident, 'kind': 'news', 'source': ident, 'source_name': ident,
                'title': 'Story ' + ident, 'text': 'Summary for ' + ident,
                'url': 'https://example.com/' + ident, 'image': '', 'author': '',
                'published': '2026-10-16T07:00:00+00:00'}

    def render(self):
        self.selection_path.write_text(json.dumps(self.selection))
        packet = load_candidates(self.cfg, str(self.root), str(self.items_path))
        selection = load_selection(str(self.selection_path))
        return render_selection(self.cfg, packet, selection)

    def test_render_preserves_source_material(self):
        html, report = self.render()
        self.assertEqual(report['selected_ids'], ['b', 'a'])
        self.assertEqual(report['lead_id'], 'b')
        self.assertIn('Story b', html)
        self.assertIn('Story a', html)
        self.assertIn('Summary for', html)

    def test_rejects_invalid_selection(self):
        changes = [
            {'items': []},
            {'batch_id': 'wrong-batch'},
            {'items': [{'id': 'invented', 'section': 'news'}]},
            {'items': [{'id': 'a', 'section': 'unknown'}]},
            {'items': [{'id': 'a', 'section': 'news'}] * 2},
            {'lead_id': 'missing'},
        ]
        original = copy.deepcopy(self.selection)
        for change in changes:
            with self.subTest(change=change):
                self.selection = {**original, **change}
                with self.assertRaises(ValueError):
                    self.render()

    def test_render_is_offline(self):
        with patch.object(net, 'get', side_effect=AssertionError('render must be offline')):
            self.render()


if __name__ == '__main__':
    unittest.main()
