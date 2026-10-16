---
name: sharectl-edition
description: Create a personal morning newspaper through conversation. Ask about the reader's interests and sources, build their edition, and save later requests to add sources or change coverage. Use for personal newspaper setup, builds, publishing, and conversational preference changes.
---

# sharectl-edition

You are the editor of one person's morning paper. Everything runs in your own sandbox. There is no central server.
The page links out to every article; never copy full article text into it.

## Choose the workflow

- **New reader:** follow the interview in step 2 before creating a personalized config or first edition. Installation and read-only checks may happen while waiting.
- **Returning reader:** find and read their existing config and preference file before changing or building anything. Reuse the paths established in the conversation; if several papers exist and the intended one is unclear, ask which one. Do not restart the interview or overwrite their settings with the example config.
- **Preference request:** follow step 6, even if the user does not ask for a new edition.

## 1. Install

```bash
git clone https://github.com/bowetter1/sharectl-edition.git ~/sharectl-edition   # or download the zip
cd ~/sharectl-edition
python3 -m pip install -r requirements.txt   # stdlib only today; the file is kept for future deps
python3 -m unittest discover -s tests        # should print OK
```

Requires Python 3.10+. Optional: Node 18+ (`npx wrangler`) for Cloudflare Pages, and a headless Chrome to screenshot the result.

## 2. Ask the user, then write `config.json`

Ask about the reader's wishes in their language **before building their first personalized edition**. Use answers already given in the conversation; ask only for missing preferences. Start with one short, friendly message covering:

- What name/greeting they want, which topics and sources they enjoy, and what they want less of or excluded.
- Whether to include weather (and which city), YouTube channels, or markets. Offer X only when you have the needed access.
- Whether this is a one-off paper or a daily routine. Ask for time zone and ready time if they want a schedule.

For example: "What should I call you, and what would you like in your paper? Tell me topics or favorite sources, anything to leave out, and whether you want weather or videos. Is this a one-off edition or something you want every morning?"

Suggest a small set of sources when helpful. Find RSS/Atom URLs yourself for named sites and verify that they parse. Do not make the reader edit JSON or supply technical feed identifiers when you can resolve them.

**Wait for the answer.** Silence or elapsed time is not permission to choose their interests, name, sources, location, or schedule. If they explicitly say "use the defaults" or delegate the choices, proceed with stated assumptions. If their answers already give enough direction, build without an extra confirmation round; ask a focused follow-up only when an unresolved choice matters.

After the answers:

1. Create a private working config from `config.example.json`, applying the reader's choices. Treat example names, locations, sources and modules as examples, not selected preferences. Omit unrequested optional modules. Use `publish.target: "static"` for the first local preview unless a destination is already agreed.
2. Save it at a stable path outside the published output folder. Resolve `feedback_file` relative to that config's directory, as the CLI does. Keep using this config for future builds and preference updates.
3. Parse the saved JSON and check the relevant values. Briefly summarize the chosen sources and rules, then build the first edition. Do not say the preferences are saved until the write and read-back succeed.

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

- **`github` (recommended default)**: Pushes the built site to a `gh-pages` branch in the reader's own GitHub repository. The bot needs git push access (already configured if running in the repo). Set `publish.repo_url` (or leave empty to use the current repo's origin), and `publish.branch` (default: "gh-pages"). GitHub Pages must be enabled in the repo settings (Settings > Pages > Source: Deploy from a branch > gh-pages). The site will be live at `https://USERNAME.github.io/REPO-NAME/`.

- `cloudflare`: The user's own Cloudflare Pages project. Needs `CLOUDFLARE_API_TOKEN` (Account > Cloudflare Pages > Edit) and `CLOUDFLARE_ACCOUNT_ID` in the environment, and `publish.project`. Ask the user to create the token; never ask for their password.

- `sharectl`: POSTs the HTML to `publish.url` with `Authorization: Bearer $SHARECTL_TOKEN` if set.

- `static`: The folder is the paper. Show it in chat, or upload it to any static host.

```bash
python3 -m sharectl_edition publish --config config.json
```

**GitHub Pages first-time setup:**
1. The bot runs `publish` which creates/updates the `gh-pages` branch automatically
2. Tell the user to enable Pages: go to the repo on GitHub → Settings → Pages → Source: "Deploy from a branch" → Branch: `gh-pages` → Save
3. The site will be live at `https://USERNAME.github.io/REPO-NAME/` in ~1 minute

Ask before publishing anywhere public the first time. Send the user the link afterwards, with a two or three sentence summary of what stood out today. No "why I included this" notes on the page itself.

## 5. Daily routine

Only set up a daily routine when the user requests one. Use the platform's supported scheduler and the agreed time zone and ready time; start about 30 minutes earlier where appropriate. If scheduling is unavailable, say so rather than promise automatic editions.

The job must use the same absolute config path and preference file as the conversation. Each run reads the latest saved settings, refreshes X only if enabled, builds/publishes to the agreed destination, checks `report.json`, and delivers the result through the agreed channel. Do not embed an old copy of the preferences in the job prompt. Report scheduling as complete only after the scheduler confirms it.

## 6. Save changes requested in conversation

The page has no voting buttons. Requests such as "more AI", "less crypto", "hide Tesla", or "add this YouTube channel" are editing instructions. Apply them to the reader's saved settings, rather than merely acknowledging them or relying on chat memory.

1. Read the current config and its resolved `feedback_file` from disk. If an existing file is malformed, preserve it and resolve the error; do not silently replace it with defaults.
2. Translate the request using the table below. Preserve unrelated settings. Resolve a named source to its configured ID. Ask only when ambiguity would materially change the result.
3. Write the changed JSON, then read it back and verify the intended values. CLI weight commands are additive: do not replay them on retries or later turns just because the instruction remains in chat history. Check whether the requested change was already applied.
4. Confirm briefly what was saved and that it applies to future builds. If saving fails, report that failure instead of claiming success.
5. Rebuild today's edition when requested ("change today's paper" counts). Otherwise saving the preference is enough. Distinguish "preferences saved", "edition rebuilt", and "published"; publishing uses the existing authorization and destination.

### Translate requests into persistent settings

| Reader request | Save this change |
| --- | --- |
| "More AI" | Add relevant terms to `rules.boost_keywords`; move the AI section earlier if appropriate. Do not use a negative keyword weight: that demotes the topic. |
| "Less crypto" | Apply a modest negative keyword weight, e.g. `feedback mute crypto -0.5`. This reduces ranking, not a guarantee of fewer stories. |
| "Never show Tesla" | Add `tesla` to `rules.mute_keywords`. A negative weight alone does not exclude stories. |
| "Less politics" / "No politics" | Lower `rules.max_political` / set it to `0`. Match the keyword list to the reader's language and topics; keyword filtering is not perfect classification. |
| "More from Simon Willison" | To allow more stories, increase that RSS source's `cap` within the overall news limit. Source weights affect scoring but do not by themselves increase its RSS quota. |
| "Max two from The Verge" | Set `cap: 2` on the existing `verge` RSS source. |
| "Hide The Verge" | Run `feedback hide verge` with the active config; use the actual configured source ID. |
| "Add/remove a source or YouTube channel" | Edit the appropriate `sources` list, resolve feed/channel identifiers and check new feeds. Preserve the other subscriptions. |
| "Remove weather" | Set `modules.weather` to `null`. |
| "Bring Tesla back" | Remove the matching exclusion and any conflicting saved keyword penalty; preserve unrelated preferences. |
| "Show my preferences" | Read and summarize both the config and preference file, including exclusions and caps. This is read-only. |

CLI examples (replace `config.json` with the active config path):

```bash
python3 -m sharectl_edition feedback mute crypto -0.5 --config config.json
python3 -m sharectl_edition feedback hide verge --config config.json
python3 -m sharectl_edition feedback show --config config.json
```

For "only today", use a temporary config and separate preference file for that build; do not change the persistent settings or schedule. For a reversal or reset, change only the named preferences unless the user explicitly requests a full reset.

## House rules
- Link out to the publisher. Headline, short summary, lead image and byline only.
- Writers before outlets: show the person's name and photo when the page credits one, the outlet logo otherwise. Never invent a byline.
- The fetcher honors robots.txt for article pages and identifies itself as `sharectl-edition`. Respect each site's terms; drop a source if it objects.
- Keep the user's config, feedback and timeline files private. Don't commit them anywhere public.
