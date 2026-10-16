"""Collect candidates for an AI editor, then render its explicit selection."""
import copy
import hashlib
import json
import os
from datetime import datetime
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from . import feedback
from .fetch import markets, news, weather, x, youtube
from .render import template


def reader_settings(cfg, base_dir):
    """Keep existing preferences; exclude publishing credentials and private paths."""
    keys = ('name', 'greeting', 'timezone', 'language', 'strings', 'sources', 'sections', 'rules', 'modules')
    reader = {key: copy.deepcopy(cfg.get(key)) for key in keys}
    reader['sources'].get('x', {}).pop('timeline_file', None)
    reader['feedback'] = feedback.load(os.path.join(base_dir, cfg['feedback_file']))
    return reader


def batch_id(packet):
    payload = {key: value for key, value in packet.items() if key != 'batch_id'}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def collect(cfg, base_dir='.', offline_items=None):
    """No editorial filtering: the AI receives candidates and saved preferences."""
    sources = {}
    if offline_items:
        with open(offline_items, encoding='utf-8') as f:
            raw = json.load(f)
    else:
        sources, articles = news.run(cfg['sources']['rss'])
        stats, videos = youtube.run(cfg['sources'].get('youtube', []))
        sources.update(stats)
        posts = []
        xcfg = cfg['sources'].get('x') or {}
        if xcfg.get('enabled'):
            path = xcfg.get('timeline_file')
            if not path:
                raise ValueError('X is enabled but timeline_file is missing')
            stats, posts = x.from_timeline(os.path.join(base_dir, path), xcfg.get('section', ''))
            sources.update(stats)
        mods = cfg.get('modules') or {}
        raw = {'news': articles, 'videos': videos, 'posts': posts,
               'weather': weather.fetch(mods['weather'], cfg['timezone']) if mods.get('weather') else None,
               'markets': markets.fetch(mods['markets']) if mods.get('markets') else None}
    items = raw['news'] + raw['posts'] + raw['videos']
    ids = [item['id'] for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate candidate IDs; check source IDs and subscriptions')
    packet = {'version': 1, 'date': datetime.now(ZoneInfo(cfg['timezone'])).isoformat(),
              'reader': reader_settings(cfg, base_dir), 'sources': sources, 'items': items,
              'weather': raw.get('weather'), 'markets': raw.get('markets')}
    packet['batch_id'] = batch_id(packet)
    return packet


def build(cfg, base_dir='.', items_path=None, selection_path=None):
    """Validate an AI selection and fill the template with original candidate data."""
    if not items_path or not selection_path:
        raise ValueError('Fetch candidates first; build requires --items and --selection from the AI editor')
    with open(items_path, encoding='utf-8') as f:
        packet = json.load(f)
    with open(selection_path, encoding='utf-8') as f:
        selection = json.load(f)
    if packet.get('version') != 1 or packet.get('batch_id') != batch_id(packet):
        raise ValueError('Invalid candidate packet; run fetch again')
    if selection.get('batch_id') != packet['batch_id']:
        raise ValueError('Selection belongs to a different candidate batch')
    if packet['reader'] != reader_settings(cfg, base_dir):
        raise ValueError('Reader preferences changed; fetch and select again')
    chosen = selection.get('items')
    if not isinstance(chosen, list) or not chosen:
        raise ValueError('AI selection must contain at least one item; previous edition is untouched')
    definitions = cfg['sections'] or [{'key': 'news', 'title': 'News'}]
    sections = {s['key']: {**s, 'items': []} for s in definitions}
    candidates = {it['id']: it for it in packet['items']}
    seen = set()
    counts = {'news': 0, 'posts': 0, 'videos': 0}
    for entry in chosen:
        if not isinstance(entry, dict) or set(entry) != {'id', 'section'}:
            raise ValueError('Each selection entry must contain only id and section')
        ident, section = entry['id'], entry['section']
        if not isinstance(ident, str) or not isinstance(section, str):
            raise ValueError('Item IDs and section keys must be strings')
        if ident not in candidates or ident in seen:
            raise ValueError(f'Unknown or duplicate selected ID: {ident}')
        if section not in sections:
            raise ValueError(f'Unknown section: {section}')
        item = copy.deepcopy(candidates[ident])
        url = urlsplit(item['url'])
        if url.scheme not in ('https', 'http') or not url.netloc:
            raise ValueError(f'Invalid article URL: {ident}')
        sections[section]['items'].append(item)
        seen.add(ident)
        counts[{'news': 'news', 'post': 'posts', 'video': 'videos'}[item['kind']]] += 1
    lead = selection.get('lead_id')
    if counts['news'] + counts['posts']:
        if not isinstance(lead, str) or lead not in seen or candidates[lead]['kind'] == 'video':
            raise ValueError('lead_id must identify a selected news item or post')
    elif lead is not None:
        raise ValueError('A video-only edition must have a null lead_id')
    tz = ZoneInfo(cfg['timezone'])
    now = datetime.fromisoformat(packet['date']).astimezone(tz)
    report = {'date': now.isoformat(), 'batch_id': packet['batch_id'], 'editor': 'ai',
              'sources': packet['sources'], 'counts': counts,
              'selected_ids': [entry['id'] for entry in chosen], 'lead_id': lead,
              'skipped': {'not selected by editor': len(candidates) - len(seen)}}
    template.set_language(cfg.get('language'), cfg.get('strings'))
    morning = []
    if packet.get('weather'):
        morning.append(template.weather_block(packet['weather']))
    if packet.get('markets'):
        morning.append(template.markets_block(packet['markets'], ((cfg.get('modules') or {}).get('markets') or {}).get('title')))
    return template.page(cfg, [s for s in sections.values() if s['items']], morning, now, tz, report, lead_id=lead), report
