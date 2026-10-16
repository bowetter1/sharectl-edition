---
name: sharectl-edition
description: Build a reader's first personal newspaper from RSS feeds as local HTML.
---

# sharectl-edition

Build a personalized newspaper from RSS feeds. The AI selects stories based on the reader's preferences.

## 1. Find out what they want to read

Ask one short question:

> What topics or sources would you like to read?

Use any interests already given. If they name topics without sources, find RSS feeds yourself and state your choices. Use UTC timezone for the first preview.

## 2. Clone and configure

Clone the repository:

```bash
git clone https://github.com/bowetter1/sharectl-edition.git
cd sharectl-edition
```

Create `config.json` from `config.example.json`:

- Add RSS sources to `sources.rss`. Each needs `id`, `name`, `url`. Find feed URLs yourself.
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
      {"id": "verge", "name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
      {"id": "hn", "name": "Hacker News", "url": "https://news.ycombinator.com/rss"}
    ]
  },
  "sections": [
    {"key": "tech", "title": "Tech News", "keywords": ["technology", "startup"]}
  ],
  "rules": {
    "max_per_source": 3,
    "boost_keywords": [],
    "mute_keywords": []
  },
  "feedback_file": "feedback.json"
}
```

## 3. Fetch, select, and render

Fetch RSS candidates:

```bash
python3 -m sharectl_edition fetch --config config.json --out candidates.json
```

Read `candidates.json`. It contains `items` (the articles) and `reader` (saved preferences).

**You are the editor.** Select articles yourself:

- Respect per-source `cap` limits in `rules`
- Apply saved `boost_keywords` and `mute_keywords`
- Respect `feedback` weights (sources, keywords, hidden items)
- Choose sections using configured `key` values
- Preserve original titles, summaries, URLs, and bylines
- Pick a `lead_id` from selected items (must have an image)

Write `selection.json`:

```json
{
  "batch_id": "COPY_FROM_CANDIDATES",
  "lead_id": "verge-abc123",
  "items": [
    {"id": "verge-abc123", "section": "tech"},
    {"id": "hn-def456", "section": "tech"}
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
| Add/remove source | Update `sources.rss` |

Feedback commands: `python3 -m sharectl_edition feedback boost|mute|hide ...`

## Boundaries

- Keep only headlines, summaries, images, and credited bylines
- Link to publishers for full articles
- Keep config and feedback files private
- Respect source access restrictions
