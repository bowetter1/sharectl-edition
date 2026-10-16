---
name: sharectl-edition
description: Build a reader's first personal newspaper from RSS, YouTube, and X as local HTML.
---

# sharectl-edition

Build a personalized newspaper from RSS feeds, YouTube channels, and X posts. The AI selects stories based on the reader's preferences.

## 1. Find out what they want to read

Ask one short question:

> What topics or sources would you like to read?

Use any interests already given. If they name topics without sources, find RSS feeds and YouTube channels yourself. For X, explain that you'll need to use your X tools to fetch their timeline. Use UTC timezone for the first preview.

## 2. Clone and configure

Clone the repository:

```bash
git clone https://github.com/bowetter1/sharectl-edition.git
cd sharectl-edition
```

Create `config.json` from `config.example.json`:

- Add RSS sources to `sources.rss`. Each needs `id`, `name`, `url`. Find feed URLs yourself.
- Add YouTube channels to `sources.youtube`. Each needs `handle` (e.g. `@mkbhd`).
- For X: Enable `sources.x.enabled`, set `timeline_file` path, fetch the timeline with your X tools, and save it as JSON.
- Create `sections` for topics, each with `key`, `title`, and optional `keywords`.
- Set `greeting`, `timezone`, `name`.
- Set per-source `cap` limits in `rules` if requested.
- Keep `strings` empty for English; add overrides only if needed.

Example:

```json
{
  "name": "Sam",
  "greeting": "Good morning, {name}.",
  "timezone": "America/New_York",
  "strings": {},
  "sources": {
    "rss": [
      {"id": "verge", "name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "section": "tech"}
    ],
    "youtube": [
      {"handle": "@mkbhd", "section": "tech"}
    ],
    "x": {
      "enabled": true,
      "timeline_file": "x_timeline.json",
      "section": "social"
    }
  },
  "sections": [
    {"key": "tech", "title": "Tech News", "keywords": ["technology", "startup"]},
    {"key": "social", "title": "X", "keywords": []}
  ],
  "rules": {
    "max_per_source": 3,
    "boost_keywords": [],
    "mute_keywords": []
  },
  "feedback_file": "feedback.json"
}
```

### X timeline format

Use your X tools to fetch the home timeline and save as JSON. The file must have this structure:

```json
{
  "data": [{"id": "...", "text": "...", "author_id": "...", ...}],
  "includes": {
    "users": [{"id": "...", "username": "...", "name": "...", ...}],
    "media": [...]
  }
}
```

This is the standard X API v2 timeline response format. Save it to the `timeline_file` path specified in config.

## 3. Fetch, select, and render

Fetch candidates (RSS, YouTube, X):

```bash
python3 -m sharectl_edition fetch --config config.json --out candidates.json
```

Read `candidates.json`. It contains `items` (articles, videos, posts) and `reader` (saved preferences).

**You are the editor.** Select items yourself:

- Respect per-source `cap` limits in `rules`
- Apply saved `boost_keywords` and `mute_keywords`
- Respect `feedback` weights (sources, keywords, hidden items)
- Choose sections using configured `key` values
- Preserve original titles, summaries, URLs, and bylines
- Pick a `lead_id` from selected news or posts (not videos)

Write `selection.json`:

```json
{
  "batch_id": "COPY_FROM_CANDIDATES",
  "lead_id": "verge-abc123",
  "items": [
    {"id": "verge-abc123", "section": "tech"},
    {"id": "yt-dQw4w9WgXcQ", "section": "tech"},
    {"id": "x-1234567890", "section": "social"}
  ]
}
```

Render the page:

```bash
python3 -m sharectl_edition build --config config.json --items candidates.json --selection selection.json --out site/
```

Exit code 0 means success. Exit code 1 means invalid selection or candidates.

Open `site/index.html` in the reader's browser or attach the HTML file.

## 4. Save changes

Read the same config and feedback file, make the requested change, rebuild if requested.

| Request | Action |
| --- | --- |
| Add topic | Add to `rules.boost_keywords` |
| Reduce topic | `feedback mute KEYWORD -0.5` |
| Exclude words | Add to `rules.mute_keywords` |
| Adjust source | Change source `cap` or feedback weight |
| Hide source | `feedback hide SOURCE_ID` |
| Add/remove source | Update `sources.rss` or `sources.youtube` |

Feedback commands: `python3 -m sharectl_edition feedback boost|mute|hide ...`

## Boundaries

- Keep only headlines, summaries, images, and credited bylines
- Link to publishers for full articles
- Keep config, feedback, and X timeline files private
- Respect source access restrictions
