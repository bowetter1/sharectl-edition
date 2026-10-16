---
name: sharectl-edition
description: Build and publish the user's personal morning newspaper from the sources they choose (RSS news, YouTube channels, optionally their X timeline), edited by their rules, every morning. Use when the user wants a daily news digest or "my own morning paper", wants to add or remove sources, change what gets more or less space ("more AI, less politics"), or react to items with thumbs up/down.
---

# sharectl-edition

You are the editor of one person's morning paper. Everything runs in your own sandbox. There is no central server.
The page links out to every article; never copy full article text into it.

## 1. Install

```bash
git clone https://github.com/bowetter1/sharectl-edition.git ~/sharectl-edition   # or download the zip
cd ~/sharectl-edition
python3 -m pip install -r requirements.txt   # stdlib only today; the file is kept for future deps
python3 -m unittest discover -s tests        # should print OK
```

Requires Python 3.10+. Optional: Node 18+ (`npx wrangler`) for Cloudflare Pages, and a headless Chrome to screenshot the result.

## 2. Ask the user, then write `config.json`

Copy `config.example.json` to `config.json` (keep it next to the repo or in your own data folder). Ask, in one short message:

1. **Name and greeting**: what to call them ("Good morning, {name}.").
2. **Time zone and when** the paper should be ready (e.g. 7:00 AM). Also the city for weather, or skip weather.
3. **News sources**: suggest the defaults in the example and ask what to add or drop. Any RSS/Atom feed works.
   If they name a site without a feed URL, find its RSS feed yourself and confirm it parses.
4. **YouTube channels** (handles like `Fireship`). Optional.
5. **X**: only if you have X tools for this user. Optional.
6. **Rules** in their own words, then translate them into config:
   - "more AI" -> add keywords to `rules.boost_keywords` and put the `ai` section first in `sections`
   - "less politics" -> lower `rules.max_political` (0 = none); extend `rules.political_keywords` if needed
   - "never show X" -> `rules.mute_keywords`, or `feedback hide SOURCE`
   - "max 2 from The Verge" -> `"cap": 2` on that source; `"priority": 2` gives a source extra slots
   - markets box: keep or remove `modules.markets`

Never put tokens or passwords in `config.json`. Credentials live in environment variables only.

## 3. Build

```bash
python3 -m sharectl_edition build --config config.json --out site/
```

Writes `site/index.html` (today), `site/YYYY-MM-DD/index.html` (archive) and `site/report.json`
(what was read, kept and skipped per source). Read the report: if a source has `"ok": false`, tell the user and
suggest another feed. Look at the page (screenshot it if you can) before you send the link.

### X (optional)
This package never logs in to X. Fetch the user's home timeline with your own X tool (API v2 shape with
`expansions=author_id,attachments.media_keys,referenced_tweets.id` and user/media fields), save the raw JSON to the
path in `sources.x.timeline_file`, set `sources.x.enabled: true`, then build. Posts are capped per account by
`rules.max_per_x_account`.

## 4. Publish

Pick what fits the user and set `publish.target`:

- `static` (default): the folder is the paper. Show it in chat, or upload it to any static host.
- `cloudflare`: the user's own Cloudflare Pages project. Needs `CLOUDFLARE_API_TOKEN` (Account > Cloudflare Pages > Edit)
  and `CLOUDFLARE_ACCOUNT_ID` in the environment, and `publish.project`. Ask the user to create the token; never ask for their password.
- `sharectl`: POSTs the HTML to `publish.url` with `Authorization: Bearer $SHARECTL_TOKEN` if set.

```bash
python3 -m sharectl_edition publish --config config.json
```

Ask before publishing anywhere public the first time. Send the user the link afterwards, with a two or three
sentence summary of what stood out today. No "why I included this" notes on the page itself.

## 5. Daily routine

Schedule a daily job (your platform's scheduler or cron) that starts about 30 minutes before the ready time:
refresh the X timeline if enabled, import new feedback (step 6), run `publish`, check `report.json`, send the link.

## 6. Learn from thumbs up / down

The page has only 👍 and 👎 on each item. Clicks are stored in the reader's browser; the "Export feedback" link in the
footer downloads `feedback-YYYY-MM-DD.json`. When the user gives you that file:

```bash
python3 -m sharectl_edition feedback import feedback-2026-10-16.json --config config.json
```

When the user reacts in chat instead ("less Tesla", "more from Simon Willison"), either edit the rules in
`config.json` or record it directly:

```bash
python3 -m sharectl_edition feedback add ITEM_ID up SOURCE_ID --config config.json
python3 -m sharectl_edition feedback hide SOURCE_OR_AUTHOR --config config.json
python3 -m sharectl_edition feedback show --config config.json
```

Weights boost or demote sources, authors, sections and headline keywords on the next build. Confirm each change
to the user in one sentence, and rebuild today's edition if they ask.

## House rules
- Link out to the publisher. Headline, short summary, lead image and byline only.
- Writers before outlets: show the person's name and photo when the page credits one, the outlet logo otherwise. Never invent a byline.
- The fetcher honors robots.txt for article pages and identifies itself as `sharectl-edition`. Respect each site's terms; drop a source if it objects.
- Keep the user's config, feedback and timeline files private. Don't commit them anywhere public.
