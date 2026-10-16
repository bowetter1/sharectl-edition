"""Exercise correction, previous-edition recovery and conservative first-edition fallback."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sharectl_edition import cli, config, feedback, net, recovery
from sharectl_edition.build import batch_id, collect


class RecoveryFixture:
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cfg = copy.deepcopy(config.DEFAULTS)
        self.cfg.update(language='sv', sections=[{'key': 'news', 'title': 'Nyheter'}])
        self.cfg['sources']['rss'] = [{'id': 'alpha', 'name': 'Alpha', 'url': 'https://example.com/rss'}]
        self.config = self.root / 'config.json'
        self.items = self.root / 'candidates.json'
        self.selection = self.root / 'selection.json'
        self.out = self.root / 'site'
        self.state = Path(recovery.state_path(str(self.config), str(self.out)))
        self.write_packet([self.item('first'), self.item('second', published='2026-10-16T09:00:00+00:00')])
        self.selection.write_text('{broken')

    def item(self, ident, **extra):
        return {'id': ident, 'kind': 'news', 'source': 'alpha', 'source_name': 'Alpha',
                'title': 'Headline ' + ident, 'text': 'Original summary', 'url': 'https://example.com/' + ident,
                'image': '', 'author': '', 'published': '2026-10-16T10:00:00+00:00', **extra}

    def write_packet(self, items, date='2026-10-16T12:00:00+00:00'):
        self.config.write_text(json.dumps(self.cfg))
        raw = {'news': [it for it in items if it['kind'] == 'news'],
               'posts': [it for it in items if it['kind'] == 'post'],
               'videos': [it for it in items if it['kind'] == 'video']}
        raw_path = self.root / 'raw.json'
        raw_path.write_text(json.dumps(raw))
        self.packet = collect(self.cfg, str(self.root), str(raw_path))
        self.packet['date'] = date
        self.save_packet()

    def save_packet(self):
        self.packet['batch_id'] = batch_id(self.packet)
        self.items.write_text(json.dumps(self.packet))

    def choose(self, ident='first'):
        self.selection.write_text(json.dumps({'batch_id': self.packet['batch_id'], 'lead_id': ident,
                                              'items': [{'id': ident, 'section': 'news'}]}))

    def command(self, command='build'):
        return [command, '--config', str(self.config), '--items', str(self.items),
                '--selection', str(self.selection), '--out', str(self.out)]

    def run_command(self, command='build'):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr), patch.object(net, 'get', side_effect=AssertionError('must stay offline')):
            result = cli.main(self.command(command))
        self.stderr = stderr.getvalue()
        return result

    def report(self):
        return json.loads((self.out / 'report.json').read_text())

    def reserve(self):
        self.assertEqual(self.run_command(), 2)
        self.assertIn('Correct selection.json once', self.stderr)
        self.assertEqual(self.run_command(), 0, self.stderr)
        self.assertIn('WARNING', self.stderr)
        return self.report()


class RecoveryTests(RecoveryFixture, unittest.TestCase):
    def test_first_failure_requests_one_correction_without_writing_a_paper(self):
        self.assertEqual(self.run_command(), 2)
        self.assertFalse(self.out.exists())
        state = json.loads(self.state.read_text())
        self.assertEqual(state['retry_batch_id'], self.packet['batch_id'])
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o600)
        self.assertFalse(self.state.is_relative_to(self.out))

    def test_corrected_selection_builds_normally_and_resets_the_retry(self):
        self.assertEqual(self.run_command(), 2)
        self.choose()
        self.assertEqual(self.run_command(), 0)
        self.assertEqual(self.report()['editor'], 'ai')
        self.assertNotIn('recovery', self.report())
        self.assertNotIn('role="status"', (self.out / 'index.html').read_text())
        self.assertNotIn('retry_batch_id', json.loads(self.state.read_text()))
        self.selection.write_text('{broken again')
        self.assertEqual(self.run_command(), 2)

    def test_second_failure_builds_a_labelled_local_reserve(self):
        report = self.reserve()
        self.assertEqual(report['editor'], 'fallback')
        self.assertEqual(report['recovery']['mode'], 'latest')
        self.assertEqual(report['selected_ids'], ['first', 'second'])
        html = (self.out / 'index.html').read_text()
        self.assertIn('AI-urvalet misslyckades', html)
        self.assertIn('Reservutgåva', html)
        self.assertIn('utan AI-redaktörens prioritering', html)
        self.assertNotIn('Din AI-redaktör valde', html)
        self.assertTrue((self.out / '2026-10-16' / 'index.html').is_file())
        self.assertNotIn('previous', json.loads(self.state.read_text()))
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), ['2026-10-16', 'index.html', 'report.json'])

    def test_retry_survives_a_new_cli_process(self):
        for expected in (2, 0):
            result = subprocess.run([sys.executable, '-m', 'sharectl_edition', *self.command()], capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stderr)
        self.assertEqual(self.report()['editor'], 'fallback')

    def test_previous_success_is_reused_with_original_date_and_archive(self):
        self.choose()
        self.run_command()
        original = (self.out / 'index.html').read_text()
        archive = self.out / '2026-10-16' / 'index.html'
        snapshot = json.loads(self.state.read_text())['previous']
        self.write_packet([self.item('new', published='2026-10-17T10:00:00+00:00')], date='2026-10-17T12:00:00+00:00')
        self.selection.write_text('{broken')
        self.assertEqual(self.run_command(), 2)
        self.assertEqual((self.out / 'index.html').read_text(), original)
        self.assertEqual(self.run_command(), 0)
        report = self.report()
        self.assertEqual(report['recovery']['mode'], 'previous')
        self.assertEqual(report['date'], '2026-10-16T12:00:00+00:00')
        self.assertEqual(report['selected_ids'], ['first'])
        html = (self.out / 'index.html').read_text()
        self.assertIn('senaste fungerande tidningen från 2026-10-16', html)
        self.assertNotIn('Headline new', html)
        self.assertEqual(archive.read_text(), original)
        self.assertFalse((self.out / '2026-10-17').exists())
        self.assertEqual(json.loads(self.state.read_text())['previous'], snapshot)
        self.assertEqual(self.run_command(), 0)
        self.assertEqual((self.out / 'index.html').read_text().count('role="status"'), 1)

    def test_snapshot_from_different_preferences_is_not_reused(self):
        self.choose()
        self.run_command()
        feedback.save(str(self.root / 'feedback.json'), {**feedback.EMPTY, 'hidden': ['alpha']})
        self.write_packet([self.item('first'), self.item('other', source='beta', source_name='Beta')])
        self.selection.write_text('{broken')
        report = self.reserve()
        self.assertEqual(report['recovery']['mode'], 'latest')
        self.assertEqual(report['selected_ids'], ['other'])
        self.assertNotIn('Headline first', (self.out / 'index.html').read_text())

    def test_each_new_batch_gets_one_new_correction_attempt(self):
        self.reserve()
        self.write_packet([self.item('new')])
        before = (self.out / 'index.html').read_text()
        self.assertEqual(self.run_command(), 2)
        self.assertEqual((self.out / 'index.html').read_text(), before)
        self.assertEqual(self.run_command(), 0)
        self.assertEqual(self.report()['selected_ids'], ['new'])

    def test_invalid_selection_shapes_recover_without_relaxing_candidate_validation(self):
        values = [[], None, {}, {'items': []},
                  {'items': [{'id': 'invented', 'section': 'news'}]},
                  {'items': [{'id': 'first', 'section': 'missing'}]},
                  {'items': [{'id': 'first', 'section': 'news'}] * 2},
                  {'lead_id': 'invented', 'items': [{'id': 'first', 'section': 'news'}]},
                  {'items': [{'id': 'first', 'section': 'news', 'title': 'invented'}]},
                  {'batch_id': 'yesterday', 'items': [{'id': 'first', 'section': 'news'}]}]
        for index, value in enumerate(values):
            with self.subTest(value=value):
                self.write_packet([self.item('first', text='batch ' + str(index))])
                if isinstance(value, dict):
                    value = {'batch_id': self.packet['batch_id'], 'lead_id': 'first', **value}
                self.selection.write_text(json.dumps(value))
                self.reserve()

    def test_missing_selection_file_also_gets_a_retry_and_reserve(self):
        self.selection.unlink()
        self.reserve()

    def test_corrupt_candidate_packets_stop_without_retry_or_replacement(self):
        self.out.mkdir()
        (self.out / 'index.html').write_text('Existing paper')
        original = copy.deepcopy(self.packet)
        invalid = [None, {'version': 1}, {**original, 'batch_id': 'invalid'},
                   {**original, 'date': 'not-a-date'}, {**original, 'date': '2026-10-16'},
                   {**original, 'sources': []},
                   {**original, 'items': [original['items'][0]] * 2},
                   {**original, 'items': [self.item('bad', image=[])]},
                   {**original, 'items': [self.item('bad', url='javascript:alert(1)')]},
                   {**original, 'items': [self.item('bad', kind='unknown')]}]
        for packet in invalid:
            with self.subTest(packet=packet):
                if isinstance(packet, dict) and 'date' in packet and packet.get('batch_id') != 'invalid':
                    packet['batch_id'] = batch_id(packet)
                self.items.write_text(json.dumps(packet))
                self.assertEqual(self.run_command(), 1)
                self.assertEqual(self.run_command(), 1)
                self.assertFalse(self.state.exists())
                self.assertEqual((self.out / 'index.html').read_text(), 'Existing paper')

    def test_changed_preferences_stop_before_recovery(self):
        for change in ('config', 'feedback'):
            with self.subTest(change=change):
                if change == 'config':
                    cfg = {**self.cfg, 'name': 'Changed reader'}
                    self.config.write_text(json.dumps(cfg))
                else:
                    self.config.write_text(json.dumps(self.cfg))
                    feedback.save(str(self.root / 'feedback.json'), {**feedback.EMPTY, 'hidden': ['alpha']})
                self.assertEqual(self.run_command(), 1)
                self.assertIn('preferences changed', self.stderr)
                self.assertFalse(self.state.exists())
                self.assertFalse(self.out.exists())

    def test_empty_or_fully_filtered_candidates_do_not_replace_an_existing_paper(self):
        self.out.mkdir()
        (self.out / 'index.html').write_text('Existing paper')
        self.cfg['rules']['max_news'] = 0
        self.write_packet([self.item('first')])
        self.assertEqual(self.run_command(), 2)
        self.assertEqual(self.run_command(), 1)
        self.assertIn('No eligible articles', self.stderr)
        self.assertEqual((self.out / 'index.html').read_text(), 'Existing paper')
        self.assertFalse((self.out / 'report.json').exists())

    def test_tampered_previous_snapshot_is_not_reused(self):
        self.choose()
        self.run_command()
        original = (self.out / 'index.html').read_text()
        state = json.loads(self.state.read_text())
        state['previous']['html'] = 'Changed snapshot'
        self.state.write_text(json.dumps(state))
        self.selection.write_text('{broken')
        self.assertEqual(self.run_command(), 2)
        self.assertEqual(self.run_command(), 1)
        self.assertIn('Invalid previous-edition snapshot', self.stderr)
        self.assertEqual((self.out / 'index.html').read_text(), original)

    def test_malformed_private_state_stops_without_replacing_output(self):
        self.state.parent.mkdir()
        self.state.write_text('{broken')
        self.assertEqual(self.run_command(), 1)
        self.assertIn('private recovery state', self.stderr)
        self.assertFalse(self.out.exists())

    def test_publish_does_not_deploy_before_retry_then_deploys_the_labelled_reserve(self):
        self.cfg['publish'] = {'target': 'github', 'repo_url': 'https://github.com/example/paper.git'}
        self.write_packet([self.item('first')])
        with patch('sharectl_edition.publish.github.deploy', return_value=0) as deploy:
            self.assertEqual(self.run_command('publish'), 2)
            deploy.assert_not_called()
            with self.assertRaises(SystemExit) as result:
                self.run_command('publish')
            self.assertEqual(result.exception.code, 0)
            deploy.assert_called_once()
        self.assertEqual(self.report()['editor'], 'fallback')

    def test_recovery_state_cannot_be_published(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(self.command()[:-1] + [str(self.root)]), 1)
        self.assertFalse((self.root / 'index.html').exists())

    def test_english_reserve_is_labelled(self):
        self.cfg['language'] = 'en'
        self.write_packet([self.item('first')])
        self.reserve()
        html = (self.out / 'index.html').read_text()
        self.assertIn('AI selection failed', html)
        self.assertIn('without AI editorial ranking', html)


class FallbackFilterTests(RecoveryFixture, unittest.TestCase):
    def test_reserve_deduplicates_links_and_uses_only_configured_sections(self):
        self.cfg['sections'] = [{'key': 'tech', 'title': 'Tech', 'keywords': ['robots']},
                                {'key': 'news', 'title': 'News'}]
        self.write_packet([self.item('first', section='news'),
                           self.item('repeat', url='https://example.com/first', source='beta'),
                           self.item('tech', title='Robots in the garden', section='unknown')])
        selection, skipped = recovery.latest_selection(self.cfg, self.packet)
        self.assertEqual(selection['items'], [{'id': 'first', 'section': 'news'}, {'id': 'tech', 'section': 'tech'}])
        self.assertEqual(skipped['same story as another source'], 1)

    def test_filters_hidden_sources_authors_handles_and_muted_words_in_all_formats(self):
        self.cfg['rules']['mute_keywords'] = ['EXCLUDE']
        feedback.save(str(self.root / 'feedback.json'), {**feedback.EMPTY, 'hidden': ['beta', 'jane doe', '@bob']})
        self.write_packet([self.item('source', source='beta'), self.item('author', author='Jane Doe'),
                           self.item('coauthor', coauthors=['Jane Doe']), self.item('handle', kind='post', handle='bob'),
                           self.item('muted-news', title='Please exclude this'),
                           self.item('muted-post', kind='post', text='Please Exclude this'),
                           self.item('muted-video', kind='video', text='Please exclude this'), self.item('allowed')])
        selection, skipped = recovery.latest_selection(self.cfg, self.packet)
        self.assertEqual([entry['id'] for entry in selection['items']], ['allowed'])
        self.assertEqual(skipped, {'hidden by you': 4, 'muted keyword': 3})

    def test_caps_zero_overrides_and_totals_are_respected_in_newest_first_order(self):
        self.cfg['sources']['rss'].extend([{'id': 'blocked', 'cap': 0}, {'id': 'beta', 'cap': 1}])
        self.cfg['rules'].update(max_per_source=2, max_news=3)
        self.write_packet([self.item('alpha-old', published='2026-10-16T08:00:00+00:00'),
                           self.item('alpha-new'), self.item('alpha-middle', published='2026-10-16T09:00:00+00:00'),
                           self.item('blocked', source='blocked'), self.item('beta-new', source='beta'),
                           self.item('beta-old', source='beta', published='2026-10-16T07:00:00+00:00'),
                           self.item('gamma', source='gamma', published='2026-10-16T06:00:00+00:00')])
        selection, _ = recovery.latest_selection(self.cfg, self.packet)
        self.assertEqual([entry['id'] for entry in selection['items']], ['alpha-new', 'beta-new', 'alpha-middle'])

    def test_dates_images_and_political_caps_are_respected(self):
        self.cfg['rules'].update(require_image=True, fresh_days=2, max_political=1, political_keywords=['senate'])
        items = [self.item('good', image='https://example.com/i.jpg'),
                 self.item('political', title='Senate votes', image='https://example.com/i.jpg'),
                 self.item('political-extra', title='SENATE votes again', image='https://example.com/i.jpg'),
                 self.item('no-image')]
        for index, date in enumerate(['', 'bad', '2026-10-16T09:00:00', '2026-10-17T09:00:00+00:00', '2026-10-01T09:00:00+00:00']):
            items.append(self.item('date-' + str(index), published=date, image='https://example.com/i.jpg'))
        self.write_packet(items)
        selection, skipped = recovery.latest_selection(self.cfg, self.packet)
        self.assertEqual([entry['id'] for entry in selection['items']], ['good', 'political'])
        self.assertEqual(skipped['outside freshness window'], 5)
        self.assertEqual(skipped['no image'], 1)
        self.assertEqual(skipped['politics cap'], 1)

    def test_political_exclusion_without_keywords_does_not_guess(self):
        self.cfg['rules']['max_political'] = 0
        self.write_packet([self.item('news'), self.item('post', kind='post', source='x-ada')])
        selection, skipped = recovery.latest_selection(self.cfg, self.packet)
        self.assertEqual([entry['id'] for entry in selection['items']], ['post'])
        self.assertEqual(skipped['political filter unavailable'], 1)

    def test_video_and_account_limits_and_video_only_lead(self):
        self.cfg['rules'].update(max_videos=2, max_per_channel=1, max_posts=1, max_per_x_account=1)
        self.cfg['sources']['youtube'] = [{'handle': '@blocked', 'cap': 0}]
        self.cfg['sections'] = [{'key': 'video', 'title': 'Video', 'kinds': ['video']},
                                {'key': 'posts', 'title': 'Posts', 'kinds': ['post']}]
        self.write_packet([self.item('v1', kind='video', source='yt-a'), self.item('v2', kind='video', source='yt-a'),
                           self.item('v3', kind='video', source='yt-b'), self.item('v4', kind='video', source='yt-c'),
                           self.item('v5', kind='video', source='yt-blocked'),
                           self.item('p1', kind='post', source='x-a', published='2026-10-16T09:00:00+00:00'),
                           self.item('p2', kind='post', source='x-a', published='2026-10-16T08:00:00+00:00'),
                           self.item('p3', kind='post', source='x-b', published='2026-10-16T07:00:00+00:00')])
        selection, _ = recovery.latest_selection(self.cfg, self.packet)
        self.assertEqual(selection['items'], [{'id': 'v1', 'section': 'video'}, {'id': 'v3', 'section': 'video'},
                                              {'id': 'p1', 'section': 'posts'}])
        self.cfg['rules']['max_posts'] = 0
        self.write_packet(self.packet['items'])
        report = self.reserve()
        self.assertIsNone(report['lead_id'])
        self.assertEqual(report['counts'], {'news': 0, 'posts': 0, 'videos': 2})


if __name__ == '__main__':
    unittest.main()
