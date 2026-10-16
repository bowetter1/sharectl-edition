# sharectl-edition

**Your AI bot makes you a personal newspaper.**

Tell any AI bot that can fetch news from the web:

> Make me a newspaper using https://github.com/bowetter1/sharectl-edition

Your bot asks what you want to read, fetches the content with its own tools, fills the HTML template, and shows you a beautiful newspaper—locally in your browser.

## How it works

1. Your bot interviews you about topics, sources, and people you follow
2. It fetches articles, videos, and posts using its own web tools
3. It selects the best content and fills `template.html` by hand (plain HTML, no build step)
4. You get `index.html` to open in your browser
5. Tell your bot what to change—it remembers for next time

**No Python. No installation. No config files.** Just HTML your bot fills and saves locally.

## For AI bots

Read [`SKILL.md`](SKILL.md) for complete instructions on how to:
- Interview the reader
- Fetch content with your own tools (web search, RSS, X, YouTube)
- Select and organize stories
- Fill the template (with clear HTML comments showing where)
- Handle missing tools (no X access? no problem)
- Remember preferences for next time

## Example

![Example newspaper with AI/tech news](examples/screenshot.jpg)

View the example: open [`examples/example.html`](examples/example.html) in your browser.

The example contains fictional content to demonstrate the layout. Your bot fills it with real news based on your interests.

## Live demo

See a real edition at [utgava.sharectl.com](https://utgava.sharectl.com/)

## Features

- **Clean, readable design** inspired by Apple's design language
- **Sections**: lead story, news/business, videos, X/Twitter posts
- **Mobile responsive** with a collapsible grid layout
- **No JavaScript required** (except for YouTube embed on click)
- **Plain HTML** so any bot can fill it—no templating engines

## What your bot does

✅ Fetches headlines and summaries (never full articles)  
✅ Links everything to original sources  
✅ Respects your interests and feedback  
✅ Works without X or YouTube if those tools aren't available  
✅ Saves your preferences in its conversation memory  

## What it doesn't do

❌ No web scraping of full articles (just headlines + links)  
❌ No API keys or accounts required  
❌ No installation or setup steps for you  
❌ No config files to edit manually  

## Files

- **`template.html`** — The newspaper template (HTML + inline CSS)
- **`SKILL.md`** — Complete instructions for AI bots
- **`examples/example.html`** — Fictional example showing the layout
- **`LICENSE`** — MIT license

## Part of sharectl

This is the template-only version of sharectl-edition. Headlines link to publishers; full articles are never republished.

Made by [Bo Wetter](https://sharectl.com) and contributors. [MIT license](LICENSE).

---

**Get started:** Just tell your AI bot to make you a newspaper using this repo.
