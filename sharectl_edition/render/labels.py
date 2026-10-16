"""Simple English UI strings. Minimal translation support via config.strings override."""

STRINGS = {
    "html_lang": "en",
    "tagline": "Edited by your AI, by your rules",
    "top_story": "Top story",
    "more_news": "More news",
    "voices": "Voices from X",
    "read_more": "Read on {site}",
    "via": "via {name}",
    "why": "Why?",
    "why_title": "Why am I seeing this?",
    "why_ai_intro": "Your AI editor selected {kept} items using your saved reading preferences.",
    "sources_today": "In today's edition",
    "the_end": "That was everything worth seeing today.",
    "footer": "Built by your own AI with sharectl-edition. Headlines link to the publishers.",
    "tell_agent": "Want changes? Just tell your AI.",
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "months": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December"],
    "date": "{day}, {month} {d}, {y}",
    "time": "%-I:%M %p",
}


def get(overrides: dict | None = None) -> dict:
    """Return English strings with optional config.strings overrides."""
    table = STRINGS.copy()
    if overrides:
        table.update(overrides)
    return table
