"""One AI correction attempt, then a dated previous edition or a labelled latest-items reserve."""
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
import os
import tempfile

from . import feedback
from .build import CandidateError, SelectionError, load_candidates, load_selection, render_selection
from .render import labels, template


class RetrySelection(SelectionError):
    """Ask the calling AI to correct the selection once and run the command again."""


def state_path(config_path, out):
    config_path, out = os.path.realpath(config_path), os.path.realpath(out)
    directory = os.path.join(os.path.dirname(config_path), '.edition-state')
    if os.path.commonpath([directory, out]) == out:
        raise CandidateError('Keep the config and .edition-state directory outside the published output')
    key = hashlib.sha256((config_path + '\0' + out).encode()).hexdigest()
    return os.path.join(directory, key + '.json')


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _load(path):
    try:
        with open(path, encoding='utf-8') as f:
            state = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        raise CandidateError('Cannot read private recovery state; repair it before retrying') from exc
    if not isinstance(state, dict) or state.get('version') != 1:
        raise CandidateError('Invalid private recovery state')
    return state


def _save(path, state):
    directory = os.path.dirname(path)
    os.makedirs(directory, mode=0o700, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory, delete=False) as f:
            name = f.name
            json.dump({'version': 1, **state}, f, ensure_ascii=False)
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def remember(path, packet, html_text, report):
    """Only a successfully written AI edition becomes the previous-edition snapshot."""
    if report.get('editor') == 'ai' and not report.get('recovery'):
        snapshot = {'reader_id': _digest(packet['reader']), 'html': html_text, 'report': report}
        _save(path, {'previous': snapshot, 'checksum': _digest(snapshot)})


def _limit(value, name):
    if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
        raise CandidateError(f'{name} must be a non-negative integer or null')
    return value


def latest_selection(cfg, packet):
    """Chronological reserve with literal exclusion filters; no semantic AI ranking."""
    rules = cfg['rules']
    hidden = {feedback.norm(value) for value in packet['reader']['feedback'].get('hidden', [])}
    muted = [word.casefold() for word in rules.get('mute_keywords', []) if word.strip()]
    political = [word.casefold() for word in rules.get('political_keywords', []) if word.strip()]
    political_cap = _limit(rules.get('max_political'), 'max_political')
    totals = {kind: _limit(rules.get(key, default), key) for kind, key, default in
              [('news', 'max_news', 24), ('video', 'max_videos', 6), ('post', 'max_posts', 20)]}
    per_source = {kind: _limit(rules.get(key, default), key) for kind, key, default in
                  [('news', 'max_per_source', 3), ('video', 'max_per_channel', 2), ('post', 'max_per_x_account', 2)]}
    caps = {source['id']: _limit(source['cap'], 'source cap') for source in cfg['sources']['rss']
            if source.get('cap') is not None}
    caps.update({'yt-' + channel['handle'].lstrip('@').lower(): _limit(channel['cap'], 'channel cap')
                 for channel in cfg['sources'].get('youtube', []) if channel.get('cap') is not None})
    sections = cfg['sections'] or [{'key': 'news', 'title': 'News'}]
    now = datetime.fromisoformat(packet['date'])
    days = rules.get('fresh_days', 14)
    if days is not None and (isinstance(days, bool) or not isinstance(days, (int, float)) or days < 0):
        raise CandidateError('fresh_days must be non-negative or null')
    counts, sources, skipped = Counter(), Counter(), Counter()
    selected, seen_urls, politics = [], set(), 0
    dated = []
    for item in packet['items']:
        try:
            date = datetime.fromisoformat(item.get('published', '').replace('Z', '+00:00'))
            if date.tzinfo is None or date > now or (days is not None and now - date > timedelta(days=days)):
                raise ValueError()
        except (TypeError, ValueError):
            skipped['outside freshness window'] += 1
            continue
        dated.append((date, item))
    for _, item in sorted(dated, key=lambda row: row[0], reverse=True):
        kind, source = item['kind'], item['source']
        identities = [source, item['source_name'], item.get('author', ''), item.get('handle', '')]
        identities.extend(item.get('coauthors', []))
        text = ' '.join([item['title'], item['text']] + identities).casefold()
        allowed = [s for s in sections if kind in s.get('kinds', ['news', 'post', 'video'])]
        section = next((s for s in allowed if s['key'] == item.get('section')), None)
        section = section or next((s for s in allowed if any(word.casefold() in text for word in s.get('keywords', []) if word)), None)
        section = section or (allowed[0] if allowed else None)
        is_political = kind == 'news' and any(word in text for word in political)
        cap = caps.get(source, per_source[kind])
        if any(feedback.norm(value) in hidden for value in identities):
            reason = 'hidden by you'
        elif any(word in text for word in muted):
            reason = 'muted keyword'
        elif rules.get('require_image') and not item.get('image'):
            reason = 'no image'
        elif kind == 'news' and political_cap is not None and not political:
            # Without a keyword list a simple reserve cannot safely classify political news.
            reason = 'political filter unavailable'
        elif is_political and political_cap is not None and politics >= political_cap:
            reason = 'politics cap'
        elif cap is not None and sources[source] >= cap:
            reason = 'max per source'
        elif totals[kind] is not None and counts[kind] >= totals[kind]:
            reason = 'no room in the edition'
        elif item['url'] in seen_urls:
            reason = 'same story as another source'
        elif section is None:
            reason = 'no matching section'
        else:
            selected.append({'id': item['id'], 'section': section['key']})
            counts[kind] += 1
            sources[source] += 1
            seen_urls.add(item['url'])
            politics += is_political
            continue
        skipped[reason] += 1
    if not selected:
        raise CandidateError('No eligible articles for a fallback edition; saved exclusions and limits were preserved')
    candidates = {item['id']: item for item in packet['items']}
    lead = next((entry['id'] for entry in selected if candidates[entry['id']]['kind'] != 'video'), None)
    return {'batch_id': packet['batch_id'], 'lead_id': lead, 'items': selected}, dict(skipped)


def build(cfg, base_dir, items_path, selection_path, path):
    """Return HTML/report/packet; only selection failures advance the recovery chain."""
    packet = load_candidates(cfg, base_dir, items_path)
    try:
        html_text, report = render_selection(cfg, packet, load_selection(selection_path))
    except SelectionError as exc:
        state = _load(path)
        if state.get('retry_batch_id') != packet['batch_id']:
            _save(path, {**state, 'retry_batch_id': packet['batch_id']})
            raise RetrySelection(f'{exc}\nCorrect selection.json once and rerun the same command. '
                                 'If that attempt also fails, a labelled fallback will be used.') from exc
        previous = state.get('previous')
        if previous is not None:
            if not isinstance(previous, dict) or state.get('checksum') != _digest(previous):
                raise CandidateError('Invalid previous-edition snapshot')
            if previous['reader_id'] == _digest(packet['reader']):
                strings = labels.get(cfg.get('language'), cfg.get('strings'))
                report = {**previous['report'], 'recovery': {'mode': 'previous', 'attempted_date': packet['date']}}
                message = strings['fallback_previous'].format(date=report['date'])
                return template.with_notice(previous['html'], message), report, packet
        selection, skipped = latest_selection(cfg, packet)
        html_text, report = render_selection(cfg, packet, selection, editor='fallback', skipped=skipped)
    return html_text, report, packet
