# sharectl-edition

**Your AI agent makes you a personal newspaper.**

Tell any AI agent that can fetch news from the web:

> Make me a newspaper using https://github.com/bowetter1/sharectl-edition

Your agent asks what you want to read, waits for your answer, fetches the content with its own tools, fills the HTML template, and shows you a beautiful newspaper—locally in your browser.

## How it works

1. Your agent asks about topics, sources, and people you follow, and waits for your answer
2. It fetches articles, videos, and posts with its own tools, from RSS feeds and free public APIs
3. It selects the best content and fills `template.html` (plain HTML, no build step)
4. You get `index.html` to open in your browser
5. Tell your agent what to change—it remembers, and checks with you next time

**No Python. No installation. No config files.** Just HTML your agent fills and saves locally.

## For AI agents

Read [`SKILL.md`](SKILL.md) for complete instructions on how to:
- Interview the reader first, before fetching anything
- Fetch content with your own tools: tested feeds and keyless APIs for news, YouTube, weather, sports and markets
- Select and organize stories
- Fill the template (with clear HTML comments showing where)
- Handle missing tools (no X access? no problem)
- Remember preferences for next time

## Example

![Example newspaper with AI/tech news](examples/screenshot.jpg)

View the example: open [`examples/example.html`](examples/example.html) in your browser.

The example contains fictional content to demonstrate the layout. Your agent fills it with real news based on your interests.

## Live demo

See a real edition at [utgava.sharectl.com](https://utgava.sharectl.com/)

## Features

- **Clean, readable design** inspired by Apple's design language
- **Sections**: lead story, news/business, videos, X/Twitter posts
- **Mobile responsive** with a collapsible grid layout
- **No JavaScript required** (except for YouTube embed on click)
- **Plain HTML** so any agent can fill it—no templating engines

## What your agent does

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
- **`SKILL.md`** — Complete instructions for AI agents
- **`examples/example.html`** — Fictional example showing the layout
- **`LICENSE`** — MIT license

## Testing the skill

Test it the way a new reader meets it:

1. Open a new chat in an empty folder, with no memory of you and no earlier `config.json` within reach.
2. Paste: "Make me a newspaper using https://github.com/bowetter1/sharectl-edition"
3. The first reply should be the questions from Step 1, and nothing should be fetched before you answer.
4. Answer, then check the `index.html` against Step 5 of `SKILL.md`, and that numbers and results match their sources.
5. Repeat with the models readers are likely to use, such as Sonnet and Opus. The skill is written for strong models; small ones such as Haiku may skip the questions.

## Part of sharectl

This is the template-only version of sharectl-edition. Headlines link to publishers; full articles are never republished.

Made by [Bo Wetter](https://sharectl.com) and contributors. [MIT license](LICENSE).

---

**Get started:** Just tell your AI agent to make you a newspaper using this repo.
