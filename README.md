# sharectl-edition

**Your own bot edits your personal morning paper.**

Part of [sharectl.com](https://sharectl.com) — a people-first personal edition edited by your own AI bot. This is the on-ramp: a zero-dependency Python project that fetches, selects, and publishes your daily newspaper from the sources you choose. No app, no account, no central server.

Tell your bot what you read, and every morning it builds a newspaper just for you: the sources you trust, the YouTube channels you watch, and optionally the people you follow on X. Change the whole paper with one sentence in chat: *"more AI, less politics, max two stories from The Verge."*

![Example edition](examples/screenshot.jpg)

👉 **[Live demo: utgava.sharectl.com](https://utgava.sharectl.com/)**

Install: `git clone https://github.com/bowetter1/sharectl-edition.git && cd sharectl-edition && python3 -m sharectl_edition build --config config.example.json --out site/`

## Quickstart: tell your bot

> Install the sharectl edition skill from https://github.com/bowetter1/sharectl-edition and set up my morning paper.

Your bot reads [`SKILL.md`](SKILL.md), asks you for your sources, rules, name and time zone, builds the first edition
and sets up a daily routine.

## Quickstart: by hand

```bash
git clone https://github.com/bowetter1/sharectl-edition.git && cd sharectl-edition
cp config.example.json config.json        # edit name, sources, rules
python3 -m sharectl_edition build --config config.json --out site/
open site/index.html
```

Python 3.10+, standard library only.

## What's in a paper

- **Morning box**: weather (Open-Meteo, no key) and an optional markets box.
- **Top story** with the latest headlines beside it.
- **Sections** you define (AI, Tech, Business, U.S. & World...): one big story, a column beside it, two-column stories, briefs.
- **Voices from X**: posts from people you follow, if your bot has X access.
- **Video**: new uploads from your YouTube channels, on a black page with round red play buttons.
- **Plain-language feedback**: Tell your bot what you want more or less of ("more AI", "less politics", "hide Tesla"), and it adjusts the paper.

## How selection works

`sharectl_edition/select.py`, in order: hidden sources and muted keywords out; each source's items ranked by your
feedback and boost keywords; near-duplicate headlines across sources removed; politics capped (configurable keyword
list); per-source caps; round-robin across sources so no single outlet takes over. Every decision is in `site/report.json`.

## Commands

```
python -m sharectl_edition build    --config config.json --out site/
python -m sharectl_edition publish  --config config.json          # github (default) | cloudflare | sharectl | static
python -m sharectl_edition feedback show --config config.json
python -m sharectl_edition feedback boost SOURCE 1.0 --config config.json
python -m sharectl_edition feedback mute KEYWORD -0.5 --config config.json
python -m sharectl_edition feedback hide SOURCE --config config.json
```

## Publishing

**GitHub Pages (recommended):** Set `"target": "github"` in `config.json` publish section. The bot pushes to a `gh-pages` branch in your repo. Enable Pages in your repo settings (Settings > Pages > Source: gh-pages branch). Your edition will be live at `https://USERNAME.github.io/REPO-NAME/`.

**Cloudflare Pages:** Set `"target": "cloudflare"` and provide `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` environment variables.

**Static:** Set `"target": "static"` to build locally and serve from any static host.

## Layout

```
SKILL.md                  instructions for the bot
config.example.json       US defaults: AP, The Verge, TechCrunch, Ars Technica, NYT Tech, Hacker News, Simon Willison, Stratechery, AI YouTube
sharectl_edition/
  fetch/                  news.py (RSS/Atom + Open Graph + bylines), youtube.py, x.py, weather.py, markets.py
  select.py               the editorial rules
  feedback.py             thumbs up/down -> weights (local JSON)
  render/                 template.py, edition.css, labels.py (all UI strings)
  publish/                static.py, cloudflare.py, sharectl.py
tests/                    python3 -m unittest discover -s tests
examples/                 a sample edition built from made-up data (examples/items.json)
```

## Being a good citizen

The paper shows a headline, a short summary, the lead image and the byline, and links to the publisher for the rest.
Full articles are never copied. Article pages are only read when robots.txt allows it, and requests identify as
`sharectl-edition`. Each paper is for one reader and is marked `noindex`.

## License

MIT. See [LICENSE](LICENSE).
