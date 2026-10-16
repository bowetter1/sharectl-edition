"""Collect RSS candidates for AI editor, then render its explicit selection."""
import copy
import hashlib
import json
from datetime import datetime
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from . import feedback
from .fetch import news, x, youtube
from .render import template


class CandidateError(ValueError):
    """The fetched material or saved preferences cannot be used."""


class SelectionError(ValueError):
    """The AI's selection is invalid."""


def reader_settings(cfg, base_dir):
    """Keep preferences, exclude private paths."""
    keys = ('name', 'greeting', 'timezone', 'sources', 'sections', 'rules')
    reader = {key: copy.deepcopy(cfg.get(key)) for key in keys}
    import os
    # Remove X timeline file path (private)
    if 'x' in reader['sources']:
        reader['sources']['x'].pop('timeline_file', None)
    reader['feedback'] = feedback.load(os.path.join(base_dir, cfg['feedback_file']))
    return reader


def batch_id(packet):
    payload = {key: value for key, value in packet.items() if key != 'batch_id'}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def collect(cfg, base_dir='.'):
    """Fetch RSS, YouTube, X; return candidates with reader preferences."""
    sources, articles = news.run(cfg['sources']['rss'])
    
    # YouTube videos
    yt_stats, videos = youtube.run(cfg['sources'].get('youtube', []))
    sources.update(yt_stats)
    
    # X posts
    posts = []
    xcfg = cfg['sources'].get('x') or {}
    if xcfg.get('enabled'):
        path = xcfg.get('timeline_file')
        if not path:
            raise ValueError('X is enabled but timeline_file is missing')
        import os
        x_stats, posts = x.from_timeline(os.path.join(base_dir, path), xcfg.get('section', ''))
        sources.update(x_stats)
    
    items = articles + videos + posts
    ids = [item['id'] for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate candidate IDs; check source IDs')
    
    packet = {
        'version': 1,
        'date': datetime.now(ZoneInfo(cfg['timezone'])).isoformat(),
        'reader': reader_settings(cfg, base_dir),
        'sources': sources,
        'items': items
    }
    packet['batch_id'] = batch_id(packet)
    return packet


def load_candidates(cfg, base_dir, items_path):
    """Validate candidates before rendering."""
    try:
        with open(items_path, encoding='utf-8') as f:
            packet = json.load(f)
    except (OSError, ValueError) as exc:
        raise CandidateError(f'Cannot read candidates: {exc}') from exc
    
    if not isinstance(packet, dict):
        raise CandidateError('Invalid candidate packet')
    if packet.get('version') != 1 or packet.get('batch_id') != batch_id(packet):
        raise CandidateError('Invalid candidate packet')
    if packet.get('reader') != reader_settings(cfg, base_dir):
        raise CandidateError('Reader preferences changed; fetch again')
    
    try:
        date = datetime.fromisoformat(packet['date'])
        if date.tzinfo is None:
            raise ValueError()
        ids = set()
        for item in packet['items']:
            for key in ('id', 'kind', 'source', 'source_name', 'title', 'text', 'url'):
                if not isinstance(item[key], str):
                    raise ValueError()
            url = urlsplit(item['url'])
            if item['id'] in ids or item['kind'] not in ('news', 'video', 'post') or url.scheme not in ('https', 'http'):
                raise ValueError()
            ids.add(item['id'])
    except (KeyError, TypeError, ValueError):
        raise CandidateError('Invalid candidate data')
    
    return packet


def load_selection(selection_path):
    try:
        with open(selection_path, encoding='utf-8') as f:
            selection = json.load(f)
    except (FileNotFoundError, ValueError) as exc:
        raise SelectionError(f'Cannot read AI selection: {exc}') from exc
    if not isinstance(selection, dict):
        raise SelectionError('AI selection must be a JSON object')
    return selection


def render_selection(cfg, packet, selection):
    """Render explicit references, preserving source material."""
    if selection.get('batch_id') != packet['batch_id']:
        raise SelectionError('Selection belongs to a different batch')
    
    chosen = selection.get('items')
    if not isinstance(chosen, list) or not chosen:
        raise SelectionError('Selection must contain at least one item')
    
    definitions = cfg['sections'] or [{'key': 'news', 'title': 'News'}]
    sections = {s['key']: {**s, 'items': []} for s in definitions}
    candidates = {it['id']: it for it in packet['items']}
    seen = set()
    counts = {'news': 0, 'video': 0, 'post': 0}
    
    for entry in chosen:
        if not isinstance(entry, dict) or set(entry) != {'id', 'section'}:
            raise SelectionError('Each entry must contain only id and section')
        ident, section = entry['id'], entry['section']
        if not isinstance(ident, str) or not isinstance(section, str):
            raise SelectionError('IDs and section keys must be strings')
        if ident not in candidates or ident in seen:
            raise SelectionError(f'Unknown or duplicate ID: {ident}')
        if section not in sections:
            raise SelectionError(f'Unknown section: {section}')
        
        item = copy.deepcopy(candidates[ident])
        sections[section]['items'].append(item)
        seen.add(ident)
        counts[item['kind']] += 1
    
    lead = selection.get('lead_id')
    if lead is not None:
        if not isinstance(lead, str) or lead not in seen:
            raise SelectionError('lead_id must identify a selected item')
        if candidates[lead]['kind'] == 'video':
            raise SelectionError('lead_id cannot be a video')
    elif counts['news'] + counts['post']:
        raise SelectionError('lead_id required when news or posts are selected')
    
    tz = ZoneInfo(cfg['timezone'])
    now = datetime.fromisoformat(packet['date']).astimezone(tz)
    report = {
        'date': now.isoformat(),
        'batch_id': packet['batch_id'],
        'sources': packet['sources'],
        'counts': counts,
        'selected_ids': [entry['id'] for entry in chosen],
        'lead_id': lead
    }
    
    return template.page(cfg, [s for s in sections.values() if s['items']], now, tz, report, lead_id=lead), report
