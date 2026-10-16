# sharectl-edition: Personal Newspaper Agent Skill

**What this is:** A plain HTML template that an AI agent fills to make a reader their own newspaper. No Python, no templating engine: you copy blocks from `template.html` and fill them in by hand.

> **Your first reply is always the interview in Step 1.** Do not search, fetch or fill anything until the reader has answered. Preferences you remember from earlier are a suggestion to confirm, not an answer.

## When to use this skill

Use this skill when:
- A user asks you to make them a newspaper or news digest
- They mention "sharectl-edition" or share this repo URL
- They want personalized news curation in a readable format

## How it works

1. **Ask** the reader what to include, and wait for the answer
2. **Fetch content** using your own tools (web search, RSS, X, YouTube, etc.)
3. **Select stories** based on what they asked for
4. **Fill blocks** copied from `template.html`
5. **Save as index.html** locally and show/attach it to the user
6. **Remember preferences**, and confirm them next time

## Step 1: Ask first (always)

Your first reply is the interview. Do not search, fetch or fill anything until the reader has answered.

In one short message, in the reader's language, ask:

1. What topics do you want to read about?
2. Which people or sources do you follow (sites, writers, X accounts)?
3. Any YouTube channels?
4. Weather, sports or markets at the top? If so: which place, team or market?

In the same message, say which sources you can't reach (for example X). See [Handling missing tools](#handling-missing-tools).

**When you may skip a question:** only when the reader's current message already answers it. "Make me a newspaper using this repo" answers none of them.

**Saved preferences** (your memory, earlier conversations, files from an older version of this repo) are a suggestion, not an answer. Show them in one line and ask: "Same as last time, or change something?"

Then wait for the reply before you go on to Step 2.

## Step 2: Fetch content with your own tools

Use whatever tools you have available:
- **Web search** for news articles
- **RSS feeds** if you can access them
- **X/Twitter API** if you have access (optional—skip if not available)
- **YouTube** for video content
- **Weather, sports and market data** only if the reader asked for them in Step 1

**If you lack X or YouTube access:** you already said so in Step 1. Continue without it. The newspaper works fine with just web articles.

Aim for:
- ~10-20 articles across topics
- 2-5 videos (if available)
- 5-10 X posts (if available)

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
- Pick ONE lead story (the most important/interesting)
- Group the rest into sections: News/Business, Technology, Sports, etc.
- Videos get their own section
- X posts get their own section

## Step 4: Fill template.html

`template.html` is the only source of markup. Copy its blocks and fill them in; don't write your own markup or use class names that aren't in it. `examples/example.html` shows a filled edition.

Every place to fill is marked in the template:
- `<!-- FILL: … -->` and `[UPPERCASE]` placeholders: replace them with real content
- `<!-- REPEAT: … -->`: copy the block that follows once per item

Remove every block you have no content for, and the section pill that points to it.

### Blocks, top to bottom

| Block | Markup in template.html | What goes in it |
|---|---|---|
| Title | `<title>`, `og:title`, `og:description` | Date and greeting. Set `<html lang>` and `og:locale` to the reader's language |
| Masthead | `header.huvud` → `.h-rad` (date · sharectl · tagline) and `.h-namn` (greeting) | "Friday 16 October 2026", "Good morning." |
| Section pills | `.snav` → one `a.pill` per section (`href="#id"`, `data-t`, `--s` color, count in `<span>`), then `button.why-btn` | One pill per section you keep |
| Why panel | `aside.varfor` → `.vin` | How many items you read and chose, and the reader's rules as `<li>` |
| Morning | `section.morgon` → `.m-mod.vader`, `.m-mod.hockey`, `.m-mod.borsen` | Only the modules the reader asked for. Remove the rest, or the whole section |
| Lead story | `section.forsta#topp` → `article.it.f-art` | The one most important story |
| Latest | `aside.f-side` → `ol.senaste` → `li` | 4–6 recent headlines: time, link, section, source |
| Section | `section.avd` with `id="s-…"` and the section color in `--s`, then `header.a-head` | One per topic |
| ↳ Section top | `.topp` → `.t-main article.it.huvud-art` and `.t-side article.it.liten` | The section's main story and 2–3 small ones |
| ↳ Two columns | `.tva` → two `.spalt` → `article.it` | Medium stories, spread over both columns |
| ↳ Briefs | `.notiser` → `article.it.notis` | Short items, thumbnail optional |
| Video | `section.tv` | One video file. Remove unless you have a direct video URL |
| X posts | `section.roster` → `article.it.rost` | Remove if you have no X access |
| YouTube | `section.play` → `article.p-art` with `button.yt` and `data-id` | Remove if you have no videos |
| Footer | `footer.foot` | Keep the "tell your agent" line (see [Footer line](#footer-line)) |

### Details

- **Byline** (`.by`): `span.av` with two initials and the person's color in `--c`, then `<b>` name and `<small>` source · time. Put the same `--c` on the `article`.
- **Images:** `a.bild` wraps the image. Large images (`.bild.hel`) also set `style="--img:url('…')"` for the blurred fill. No image? Remove the whole `a.bild`.
- **Links:** every headline links to the original. Write `&` in URLs as `&amp;`.
- **Headlines** keep the source's wording, on one line: headlines use `white-space: pre-line`, so a line break inside one shows on the page.
- **Language:** write everything you write yourself (labels, greeting, Why panel, footer) in the reader's language.
- **Weather:** put one of `v-sol`, `v-halv`, `v-moln`, `v-regn`, `v-sno`, `v-dimma` or `v-aska` on `.vader`. In `ol.timmar` the first `li` is `.nu`, and the last can be `.imorgon` with tomorrow's high in `<b>` and low in `<small>`. Sun and cloud icons are in `examples/example.html`.
- **Sports:** `.flagga` draws a Swedish flag. Remove it for other countries.
- **Markets:** `.borsen` and each `li` take `upp` (rose) or `ned` (fell). The sparkline is an SVG polyline in a 100×32 box, and `line.bas` marks the previous close.
- **Colors:** sections and people carry color; everything else stays black and white. For example `#5b3fd1`, `#0b6bb3`, `#f25c7a`, `#0f766e`, `#ff9500`, `#ff3b30`.

Keep the CSS and the script as they are.

## Step 5: Save and show

1. **Save** the filled template as `index.html` in the current directory
2. **Show it** to the user:
   - If you can display HTML: show it
   - If not: attach/upload the file
3. **Tell them:** "Open index.html in your browser to read your newspaper"

## Step 6: Remember, and confirm next time

Use your memory or conversation history to remember:
- Their interests (topics, sources, people, morning modules)
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
- Skip the videos section
- Focus on articles and X posts (if available)

**No web search?**
- Be honest: "I can't fetch news right now without web search"
- Don't fake content

## Example conversation flows

**User:** "Make me a newspaper using https://github.com/bowetter1/sharectl-edition"

**You:** (the interview, nothing else yet)
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
2. 🔍 Fetch ~15 articles and the forecast
3. 📝 Select the best content, fill blocks from template.html, and remove the video, X and sports blocks
4. 💾 Save as index.html
5. 📰 Show/attach: "Here's your morning edition! Open index.html to read."

---

**User:** "Make me a newspaper with AI/tech news, startups, NBA. Include The Verge, Hacker News, Simon Willison, ESPN, and @fireship on YouTube."

This answers topics, sources and YouTube, so ask only what's missing:
> "Want weather or markets at the top? I can't reach X, so there won't be any posts from there."

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
❌ Don't fake content or make up articles  
❌ Don't skip attribution (always credit sources)  
❌ Don't write markup that isn't in template.html  
❌ Don't use a templating engine (fill HTML directly)  
❌ Don't require the user to install anything  
❌ Don't create config files (remember in your memory)  

## What to DO

✅ Ask first, then wait for the answer  
✅ Link every headline to its source  
✅ Keep summaries brief (2-3 sentences)  
✅ Respect the reader's preferences  
✅ Say upfront if you're missing tools (X, YouTube)  
✅ Remember their feedback for next time  
✅ Keep the same visual design (don't modify CSS)  

---

**That's it!** Ask → Wait → Fetch → Select → Fill → Save → Show → Remember.
