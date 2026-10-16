# sharectl-edition: Personal Newspaper Bot Skill

**What this is:** A simple HTML template for AI bots to create personalized newspapers for their users. No Python, no templating engines—just plain HTML that any bot can fill by hand.

## When to use this skill

Use this skill when:
- A user asks you to make them a newspaper or news digest
- They mention "sharectl-edition" or share this repo URL
- They want personalized news curation in a readable format

## How it works

1. **Interview the reader** about their interests
2. **Fetch content** using your own tools (web search, RSS, X, YouTube, etc.)
3. **Select stories** based on what they asked for
4. **Fill template.html** with the selected content
5. **Save as index.html** locally and show/attach it to the user
6. **Remember preferences** for next time

## Step 1: Interview the reader

Ask what they want to read. Be conversational and brief. Get:
- **Topics**: AI/tech, politics, business, sports, science, culture, etc.
- **People**: Specific journalists, experts, creators they follow
- **Sources**: 
  - News sites (The Verge, Ars Technica, Hacker News, etc.)
  - X/Twitter accounts (@username format)
  - YouTube channels (@channelname or channel URLs)

**Example questions:**
- "What topics interest you?"
- "Any specific people or sources you follow?"
- "YouTube channels you watch?"

If they've already told you their interests in their request, skip this and start fetching.

## Step 2: Fetch content with your own tools

Use whatever tools you have available:
- **Web search** for news articles
- **RSS feeds** if you can access them
- **X/Twitter API** if you have access (optional—skip if not available)
- **YouTube** for video content

**If you lack X or YouTube access:** Say so upfront, then continue without it. The newspaper works fine with just web articles.

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

Open `template.html` and look for HTML comments marked `<!-- FILL: ... -->` and `<!-- REPEAT: ... -->`.

**Key sections to fill:**

### Masthead (top of page):
```html
<p class="date">Good morning, Friday October 16, 2026</p>
<h1>Your Edition</h1>
<p class="intro">Brief greeting or summary</p>
<ul class="rules">
  <li>Topic 1</li>
  <li>Topic 2</li>
</ul>
```

### Lead story (one only):
```html
<article class="lead" style="--c:#f25c7a">
  <div>
    <p class="kick">SECTION NAME</p>
    <h2>Headline</h2>
    <p class="dek">Summary paragraph</p>
    <div class="by">
      <span class="av" style="--c:#f25c7a">IN</span>
      <span>
        <b>Author/Source Name</b>
        <small>Time ago</small>
      </span>
    </div>
    <div class="why">
      <span class="dot"></span>
      <span>Why: [reason you picked this]</span>
    </div>
  </div>
  <a href="URL" class="lph">
    <img src="IMAGE_URL" alt="">
  </a>
</article>
```

### Regular article cards:
```html
<article class="card" style="--c:#0066cc">
  <a href="URL" class="ph">
    <img src="IMAGE_URL" alt="">
  </a>
  <h3><a href="URL">Headline</a></h3>
  <p class="dek">Summary</p>
  <div class="by">
    <span class="av" style="--c:#0066cc">AS</span>
    <span>
      <b>Source</b>
      <small>Time ago</small>
    </span>
  </div>
  <div class="why">
    <span class="dot"></span>
    <span>Reason</span>
  </div>
</article>
```

### Video cards:
```html
<article class="card vid" style="--c:#ff3b30">
  <div class="vwrap">
    <button class="yt" data-id="YOUTUBE_VIDEO_ID" aria-label="Play video" style="background-image:url(THUMBNAIL_URL)">
      <img src="THUMBNAIL_URL" alt="">
      <span class="play">
        <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="#fff"/></svg>
      </span>
    </button>
  </div>
  <div class="vtxt">
    <p class="kick">VIDEO</p>
    <h3><a href="YOUTUBE_URL">Title</a></h3>
    <p class="dek">Description</p>
    <div class="by">
      <span class="av" style="--c:#ff3b30">YT</span>
      <span>
        <b>Channel Name</b>
        <small>YouTube · Time ago</small>
      </span>
    </div>
  </div>
</article>
```

### X/Twitter posts:
```html
<article class="card" style="--c:#1da1f2">
  <div class="post">
    <p class="ptext">Tweet text here</p>
    <!-- Optional image -->
    <a href="X_URL" class="pimg">
      <img src="IMAGE_URL" alt="">
    </a>
    <div class="by">
      <span class="av" style="--c:#1da1f2">UN</span>
      <span>
        <b>@username</b>
        <small>Time ago</small>
      </span>
    </div>
    <a href="X_URL" class="more">View on X →</a>
  </div>
</article>
```

**Avatar colors (--c):** Pick any color. Examples:
- `#f25c7a` (pink)
- `#0066cc` (blue) 
- `#ff9500` (orange)
- `#30d158` (green)
- `#ff3b30` (red)
- `#1da1f2` (twitter blue)

**Avatar initials:** Use 2 letters from source name (e.g., "The Verge" → "TV")

**Images:** If no image available, remove the `<a class="ph">` or `<a class="lph">` wrapper entirely.

## Step 5: Save and show

1. **Save** the filled template as `index.html` in the current directory
2. **Show it** to the user:
   - If you can display HTML: show it
   - If not: attach/upload the file
3. **Tell them:** "Open index.html in your browser to read your newspaper"

## Step 6: Remember for next time

Use your bot's memory/conversation history to remember:
- Their interests (topics, sources, people)
- What they liked or didn't like
- Any adjustments they requested

When they say things like:
- "Less basketball" → remember to reduce sports coverage
- "Add Ars Technica" → add it to their sources
- "More AI news" → prioritize AI stories

Then next time they ask "make me another newspaper," you already know their preferences.

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

## Example conversation flow

**User:** "Make me a newspaper with AI/tech news, startups, NBA. Include The Verge, Hacker News, Simon Willison, ESPN, and @fireship on YouTube."

**You:**
1. ✅ "Got it! Fetching AI/tech, startups, and NBA coverage from those sources..."
2. 🔍 Fetch ~15 articles, 3 videos, 5-10 posts
3. 📝 Select best content, fill template.html
4. 💾 Save as index.html
5. 📰 Show/attach: "Here's your morning edition! Open index.html to read."

**User later:** "Less NBA, add more cybersecurity."

**You:**
1. ✅ "Got it, I'll remember: less basketball, more cybersecurity."
2. 🧠 Store in conversation memory
3. Next edition: adjust accordingly

## Footer line

Always keep this line in the footer:
```html
<p>Want changes? Just tell your bot.</p>
```

This reminds readers they can ask you to adjust the newspaper.

## What NOT to do

❌ Don't republish full article text (just headlines + short summaries)  
❌ Don't fake content or make up articles  
❌ Don't skip attribution (always credit sources)  
❌ Don't use a templating engine (fill HTML directly)  
❌ Don't require the user to install anything  
❌ Don't create config files (remember in your memory)  

## What to DO

✅ Link every headline to its source  
✅ Keep summaries brief (2-3 sentences)  
✅ Respect the reader's preferences  
✅ Say upfront if you're missing tools (X, YouTube)  
✅ Remember their feedback for next time  
✅ Keep the same visual design (don't modify CSS)  

---

**That's it!** Interview → Fetch → Select → Fill → Save → Show → Remember.
