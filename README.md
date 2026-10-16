# sharectl-edition

**Tell your AI what you want to read. Get your first personal newspaper.**

Copy this into an AI chat that can run Python and show an HTML file:

> Make me a newspaper using https://github.com/bowetter1/sharectl-edition

Your AI asks what topics or sources you want, selects the stories, and shows your paper. If you already included your interests, it starts right away. No installation or config editing needed.

![Example edition](examples/screenshot.jpg)

## How it works

1. **Fetch:** RSS feeds, YouTube channels, X posts → `candidates.json`
2. **Select:** AI picks stories, writes `selection.json`
3. **Render:** Python fills the template → `site/index.html`

```bash
python3 -m sharectl_edition fetch --config config.json --out candidates.json
# AI reads candidates.json and writes selection.json
python3 -m sharectl_edition build --config config.json --items candidates.json --selection selection.json --out site/
```

The local paper has headlines, summaries, images, and bylines from news, X posts, and videos. Headlines link to publishers; full articles live on their sites.

Read it, then tell your AI what to change: add a source, adjust coverage, or leave something out. It saves your choices and rebuilds when you want to see them.

## For AI agents

[`SKILL.md`](SKILL.md) — interview, build, and show the first edition.

[`config.example.json`](config.example.json) — minimal starter.

Python 3.10+ with standard library only. No credentials needed for RSS and YouTube. X posts require the AI to fetch the timeline with its own X tools.

Part of [sharectl.com](https://sharectl.com) · [MIT license](LICENSE)
