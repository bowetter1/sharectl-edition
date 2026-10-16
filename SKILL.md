# sharectl-edition: Personal Newspaper Agent Skill

**What this is:** A plain HTML template that an AI agent fills to make a reader their own newspaper. No Python, no packages to install: you copy blocks from `template.html` and fill them in.

> **Ask before you fetch (Step 1).** Fetch nothing until the reader has told you, in this conversation, what to include. Preferences you remember from earlier are a suggestion to confirm, not an answer.

## When to use this skill

Use this skill when:
- A user asks you to make them a newspaper or news digest
- They mention "sharectl-edition" or share this repo URL
- They want personalized news curation in a readable format

## How it works

1. **Ask** the reader what to include, and wait for the answer
2. **Fetch** content with your own tools, feeds first
3. **Select** stories
4. **Fill** blocks copied from `template.html`
5. **Check, save and show** `index.html`
6. **Remember** preferences, and confirm them next time

## Step 1: Ask before you fetch

Before you fetch anything, you need the reader's answer to four things:

1. **Topics:** what do you want to read about?
2. **People and sources:** which sites, writers or X accounts do you follow?
3. **YouTube:** any channels?
4. **Top of the page:** weather, sports or markets? If so, which place, team or league, or market?

Your first reply asks, in one short message and in the reader's language, for whichever of these their message hasn't answered. In the same message, say which sources you can't reach (for example X). See [Handling missing tools](#handling-missing-tools).

- If their message answers all four, start fetching. "Make me a newspaper using this repo" answers none of them.
- "None", "no" and "you choose" are answers. Don't ask again.
- **Saved preferences** (your memory, earlier conversations, files from an older version of this repo) are a suggestion, not an answer. Show them in one line and ask: "Same as last time, or change something?"
- If you can't tell the reader's time zone (for example from the weather place), ask for it too.
- If you can't talk to the reader directly (another program started you), return your questions as your result and stop.

Wait for the reply before you go on to Step 2.

## Step 2: Fetch content

**Feeds first.** Almost every news site, blog and YouTube channel has an RSS or Atom feed. A feed gives you dated headlines, links, authors, summaries and often images in one request. Web search is a last resort: it is poor at "today's news" and often returns old or unrelated pages.

**If your fetch tool refuses a site**, request the same URL with another HTTP tool such as `curl`. Many sites block one but not the other.

### Where to get things

All of these are free and need no API key:

| What | Where |
|---|---|
| News site or blog | Its feed. Look for `<link rel="alternate" type="application/rss+xml">` in the homepage, or try `/feed`, `/rss`, `/rss.xml`, `/feed.xml`, `/atom.xml`, `/rss/index.xml`. Examples: `https://www.theverge.com/rss/index.xml`, `https://feeds.arstechnica.com/arstechnica/index`, `https://simonwillison.net/atom/everything/`, `https://www.svt.se/nyheter/rss.xml`, `https://www.di.se/rss` |
| Hacker News | `https://hnrss.org/frontpage` |
| YouTube channel | `https://www.youtube.com/feeds/videos.xml?channel_id=UC…`. Find the `channel_id` in the channel page's source (`channel_id=` or `"externalId"`). The feed has video IDs, titles, dates and thumbnails |
| Weather, any place | Open-Meteo: find coordinates with `https://geocoding-api.open-meteo.com/v1/search?name=Oslo&count=1`, then `https://api.open-meteo.com/v1/forecast?latitude=…&longitude=…&hourly=temperature_2m,weather_code,precipitation_probability&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto&forecast_days=2` |
| Weather, Nordics | MET Norway `https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=…&lon=…` (send a User-Agent), or SMHI for Sweden |
| Sports results | ESPN: `https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates=YYYYMMDD`, for example `basketball/nba`, `hockey/nhl`, `football/nfl`, `soccer/eng.1`. NHL player stats: `https://api-web.nhle.com/v1/score/YYYY-MM-DD` and `/v1/gamecenter/{id}/boxscore` |
| Markets | Yahoo: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d` for the daily change, and `?range=1d&interval=15m` for the sparkline. Symbols include `^GSPC`, `^IXIC`, `^DJI`, `^OMX`, `^FTSE`, `^GDAXI`, `^N225`, `^HSI`, `^KS11` and `000001.SS` |
| Article images | The feed's `media:content`, `media:thumbnail` or `enclosure`, otherwise the article page's `og:image` |

**Market changes:** compute the daily change from the last two daily closes (`range=5d&interval=1d`). Don't use `chartPreviousClose` from the 1-day chart: for some exchanges it is a close from two sessions back, and the sign of the change comes out wrong.

**Sports:** results APIs list both teams. Check which one is home before you write "A beat B 4–3".

Aim for:
- ~10-20 articles across topics
- 2-5 videos (if available)
- 5-10 X posts (if available)

### When something is missing

- **A source gives you nothing:** leave it out of the page and tell the reader in your reply. Never publish an empty section, or a note on the page about what couldn't be fetched.
- **Requested results don't exist** (no games last night, a market holiday): say so in one line in that module. Optionally show what's next, labelled as upcoming. Never invent results.
- **Fewer than ~5 articles in total:** tell the reader before you build, and suggest sources to add.
- **You can't read an article page:** write the summary from the feed text and headline only, and don't add facts they don't state.

## Step 3: Select content (editorial rules)

**Respect what they asked for:**
- Prioritize people over outlets (if they follow someone, include them)
- Match their topics
- Mix sources (don't over-weight one outlet)

**Quality over quantity:**
- Headlines + short summaries only (2-3 sentences)
- Never republish full articles
- Always link to the original
- Prefer recent content (today/yesterday)

**Structure:**
- Pick ONE lead story: the most important one, and preferably one with an image
- Group the rest into sections: News/Business, Technology, Sports, etc.
- Videos get their own section
- X posts get their own section

## Step 4: Fill template.html

`template.html` is the only source of markup. Copy its blocks and fill them in, by hand or with a short script of your own. Don't invent markup. Use only class names that appear in `template.html` (markup or CSS) or `examples/example.html`, which shows a filled edition.

Every place to fill is marked in the template:
- `<!-- FILL: … -->` and `[UPPERCASE]` placeholders: replace them with real content
- `<!-- REPEAT: … -->`: copy the block that follows once per item

Remove every block you have no content for, and the section pill that points to it.

### Blocks, top to bottom

| Block | Markup in template.html | What goes in it |
|---|---|---|
| Title | `<title>`, `og:title`, `og:description` | Date and greeting. Set `<html lang>` and `og:locale` to the reader's language |
| Masthead | `header.huvud` → `.h-rad` (date · sharectl · tagline) and `.h-namn` (greeting) | "Friday 16 October 2026", "Good morning." |
| Section pills | `.snav` → one `a.pill` per section you keep (`href="#id"`, `data-t`, `--s` color) | Top story, each topic section, Video, X, YouTube |
| Morning | `section.morgon` → `.m-mod.vader`, `.m-mod.hockey`, `.m-mod.borsen` | Only the modules the reader asked for. Remove the rest, or the whole section |
| Lead story | `section.forsta#topp` → `article.it.f-art` | The one most important story |
| Latest | `aside.f-side` → `ol.senaste` → `li` | 4–6 recent headlines: time, link, section, source |
| Section | `section.avd` with `id="s-…"` and the section color in `--s`, then `header.a-head` | One per topic |
| ↳ Section top | `.topp` → `.t-main article.it.huvud-art` and `.t-side article.it.liten` | The section's main story and 2–3 small ones |
| ↳ Two columns | `.tva` → two `.spalt` → `article.it` | Medium stories, spread over both columns |
| ↳ Briefs | `.notiser` → `article.it.notis` | Short items, thumbnail optional |
| Video | `section.tv#video` | One video file. Remove unless you have a direct video URL |
| X posts | `section.roster#x` → `article.it.rost` | Remove if you have no X access |
| YouTube | `section.play#youtube` → `article.p-art` with `button.yt` and `data-id` | Remove if you have no videos |
| Footer | `footer.foot` | Keep the "tell your agent" line (see [Footer line](#footer-line)) |

### Morning modules

- **Weather** (`.m-mod.vader`): put one of `v-sol`, `v-halv`, `v-moln`, `v-regn`, `v-sno`, `v-dimma` or `v-aska` on it. In `ol.timmar`, the first `li` is `.nu` (now), and the last can be `.imorgon` with tomorrow's high in `<b>` and low in `<small>`. Copy icons from the `ICONS` comment in the template: sun, half, cloud, rain, snow, thunder, fog and night.
- **Sports** (`.m-mod.hockey`, for any sport): for a team or a country's players, use one `li` per player (name and team, stats, game score). For league results, use one `li` per game: `<b>` both teams, `<small>` the status (Final, OT, or the start time), `.p` the score, `.r` a short note. `.flagga` draws a Swedish flag, so remove it for other countries.
- **Markets** (`.m-mod.borsen`): put `upp` (rose) or `ned` (fell) on the module and on each `li`. The sparkline is an SVG polyline in a 100×32 box: x runs 0–100 across the session, y = 30 − 28 × (value − low) ÷ (high − low). `line.bas` marks the previous close at the same scale.

### Details

- **Byline** (`.by`): `span.av` with two initials and a color in `--c`, then `<b>` name and `<small>` source · time. Use the author's initials, or the publisher's when there is no author ("The Verge" → "TV"). Put the same `--c` on the `article`.
- **Images** are optional. `a.bild` wraps the image. Large images (`.bild.hel`) also set `style="--img:url('…')"` for the blurred fill. No image? Remove the whole `a.bild`.
- **Links:** every headline links to the original. Write `&` in URLs as `&amp;`.
- **Headlines** keep the source's wording, on one line: headlines use `white-space: pre-line`, so a line break inside one shows on the page.
- **Times** are in the reader's local time. Pick the greeting from it ("Good morning", "Good evening").
- **Language:** write everything you write yourself in the reader's language. That includes the fixed labels in the template: "Your Edition", "Edited by your agent", "Top Story", "Latest", "Weather", "Stock Markets", "VIDEO", "Voices from X", "Videos", "Watch" and "Made with".
- **Colors:** sections and people carry color; everything else stays black and white. For example `#5b3fd1`, `#0b6bb3`, `#f25c7a`, `#0f766e`, `#ff9500`, `#ff3b30`.

Keep the CSS and the script as they are.

## Step 5: Check, save and show

Before you show it, check that:
- No `[UPPERCASE]` placeholder is left, including in `<title>` and the `og:` tags
- Every pill points to a section that exists
- No block is empty, and the page has no notes about content you couldn't fetch
- Every headline links to the original
- The CSS and the script are the same as in `template.html`

Then:
1. **Save** it as `index.html` in the folder your host gives you, otherwise in the current directory
2. **Show it** to the user:
   - If you can display HTML: show it
   - If not: attach/upload the file
3. **Tell them:** "Open index.html in your browser to read your newspaper", plus anything you left out and why

## Step 6: Remember, and confirm next time

Use your memory or conversation history to remember:
- Their interests (topics, sources, people, morning modules, time zone)
- What they liked or didn't like
- Any adjustments they requested

When they say things like:
- "Less basketball" → remember to reduce sports coverage
- "Add Ars Technica" → add it to their sources
- "More AI news" → prioritize AI stories

Next time they ask for a newspaper, still start with Step 1: show what you remember in one line and ask "Same as last time, or change something?" Fetch only after they answer.

## Handling missing tools

**No X/Twitter access?**
- Say: "I don't have X access, so I'll focus on web articles and videos"
- Continue with what you have

**No YouTube access?**
- Try the channel's feed first (see [Where to get things](#where-to-get-things))
- If that fails too, skip the videos section

**No web access at all?**
- Be honest: "I can't fetch news right now without web access"
- Don't fake content

## Example conversation flows

**User:** "Make me a newspaper using https://github.com/bowetter1/sharectl-edition"

**You:** (the questions, nothing else yet)
> "Happy to. A few quick questions first:
> 1. What topics do you want to read about?
> 2. Any people or sources you follow?
> 3. YouTube channels?
> 4. Weather, sports or markets at the top? Which place, team or market?
>
> I can't reach X, so there won't be any posts from there."

**User:** "AI and climate. The Verge and Simon Willison. No YouTube. Weather for Oslo."

**You:**
1. ✅ "Got it! Fetching AI and climate from The Verge and Simon Willison, plus the weather in Oslo..."
2. 🔍 Fetch the two feeds and the Oslo forecast
3. 📝 Select the best content, fill blocks from template.html, and remove the video, X, YouTube and sports blocks
4. ✔️ Run the checks in Step 5, then save as index.html
5. 📰 Show/attach: "Here's your edition! Open index.html to read."

---

**User:** "Make me a newspaper with AI/tech news, startups, NBA. Include The Verge, Hacker News, Simon Willison, ESPN, and @fireship on YouTube."

This answers topics, sources and YouTube, so ask only what's missing:
> "Want weather, NBA results or markets at the top? I can't reach X, so there won't be any posts from there."

**User later:** "Less NBA, add more cybersecurity."

**You:**
1. ✅ "Got it, I'll remember: less basketball, more cybersecurity."
2. 🧠 Store in conversation memory
3. Next edition: confirm in one line, then adjust accordingly

## Footer line

Always keep this line in the footer, in the reader's language:
```html
<p>Want changes? Just tell your agent.</p>
```

This reminds readers they can ask you to adjust the newspaper.

## What NOT to do

❌ Don't fetch anything before the reader has answered Step 1  
❌ Don't reuse remembered preferences without asking  
❌ Don't republish full article text (just headlines + short summaries)  
❌ Don't fake content, results or numbers  
❌ Don't publish empty sections or notes about missing content  
❌ Don't skip attribution (always credit sources)  
❌ Don't write markup that isn't in template.html  
❌ Don't require the user to install anything  
❌ Don't create config files (remember in your memory)  

## What to DO

✅ Ask first, then wait for the answer  
✅ Use feeds before web search  
✅ Link every headline to its source  
✅ Keep summaries brief (2-3 sentences)  
✅ Respect the reader's preferences  
✅ Say upfront if you're missing tools (X, YouTube)  
✅ Remember their feedback for next time  
✅ Keep the same visual design (don't modify CSS)  

---

**That's it!** Ask → Wait → Fetch → Select → Fill → Check → Save → Show → Remember.
