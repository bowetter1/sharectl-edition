"""All visible UI strings, in one place. The edition is rendered in the reader's language: `config.language`
picks a built-in table (en, sv), and `config.strings` holds the agent's translation for any other language."""
import json

EN = {
    "html_lang": "en",
    "tagline": "Edited by your agent, by your rules",
    "top_story": "Top story",
    "top_story_nav": "Top story",
    "latest": "Latest",
    "voices": "Voices from X",
    "more_news": "More news",
    "weather": "Weather",
    "now": "Now",
    "tomorrow": "Tomorrow",
    "no_rain": "No rain expected.",
    "some_rain": "Slight chance of rain, {p}%.",
    "rain": "{p}% chance of rain.",
    "weather_sub": "High {hi} and low {lo} today. Wind up to {wind} {unit}. {rain}",
    "wx_words": {"sun": "Sunny", "partly": "Partly cloudy", "cloud": "Cloudy", "fog": "Foggy", "snow": "Snow",
                 "storm": "Thunderstorms", "rain": "Rain"},
    "wx_hed": "{word} and {hi}° in {place}",
    "wx_hed_noplace": "{word}, high of {hi}°",
    "markets": "Markets",
    "markets_sub_up": "{up} of {n} closed higher.",
    "mk_rose": "{label} rose {pct}%",
    "mk_fell": "{label} fell {pct}%",
    "videos_sub": "New from the channels you follow.",
    "via": "via {name}",
    "on_x": "on X",
    "read_more": "Read on {site}",
    "why": "Why?",
    "why_title": "Why am I seeing this?",
    "why_intro": "Your agent read {read} items from {n} sources this morning and kept {kept}. The rules are yours: "
                 "at most {per_source} per source, politics capped at {political}, and nothing you have muted.",
    "why_skipped": "Left out today",
    "skip_reasons": {"hidden by you": "hidden by you", "muted keyword": "muted keyword", "no image": "no image",
                     "same story as another source": "same story as another source", "max per source": "max per source",
                     "politics cap": "politics cap", "no room in the edition": "no room in the edition"},
    "sources_today": "In today's edition",
    "the_end": "That was everything worth seeing today.",
    "footer": "Built by your own agent with sharectl-edition. Headlines link to the publishers.",
    "tell_agent": "Want changes? Just tell your agent.",
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "months": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December"],
    "date": "{day}, {month} {d}, {y}",
    "time": "%-I:%M %p",
    "decimal": ".",
    "thousands": ",",
    "percent": "{n}%",
}

SV = {
    "html_lang": "sv",
    "tagline": "Redigerad av din agent, efter dina regler",
    "top_story": "Dagens story",
    "top_story_nav": "Toppnyhet",
    "latest": "Senaste",
    "voices": "Röster från X",
    "more_news": "Fler nyheter",
    "weather": "Vädret",
    "now": "Nu",
    "tomorrow": "I morgon",
    "no_rain": "Inget regn väntas.",
    "some_rain": "Liten risk för regn, {p} %.",
    "rain": "{p} % risk för regn.",
    "weather_sub": "Högst {hi} och lägst {lo} i dag. Vind upp till {wind} {unit}. {rain}",
    "wx_words": {"sun": "Soligt", "partly": "Halvklart", "cloud": "Molnigt", "fog": "Dimma", "snow": "Snö",
                 "storm": "Åska", "rain": "Regn"},
    "wx_hed": "{word} och {hi} grader i {place}",
    "wx_hed_noplace": "{word}, upp till {hi} grader",
    "markets": "Börsen",
    "markets_sub_up": "{up} av {n} stängde på plus.",
    "mk_rose": "{label} steg {pct} %",
    "mk_fell": "{label} föll {pct} %",
    "videos_sub": "Nytt från kanalerna du följer.",
    "via": "via {name}",
    "on_x": "på X",
    "read_more": "Läs på {site}",
    "why": "Varför?",
    "why_title": "Varför ser jag det här?",
    "why_intro": "Din agent läste {read} inslag från {n} källor i morse och behöll {kept}. Reglerna är dina: "
                 "högst {per_source} per källa, politik begränsat till {political}, och inget du har tystat.",
    "why_skipped": "Valdes bort i dag",
    "skip_reasons": {"hidden by you": "dolt av dig", "muted keyword": "tystat ord", "no image": "saknar bild",
                     "same story as another source": "samma story som en annan källa", "max per source": "max per källa",
                     "politics cap": "politiktaket", "no room in the edition": "fick inte plats"},
    "sources_today": "Med i dag",
    "the_end": "Det var allt värt att se i dag.",
    "footer": "Byggd av din egen agent med sharectl-edition. Rubrikerna länkar till utgivarna.",
    "tell_agent": "Vill du ändra något? Säg till din agent.",
    "days": ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"],
    "months": ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober",
               "november", "december"],
    "date": "{day} {d} {month} {y}",
    "time": "%H:%M",
    "decimal": ",",
    "thousands": " ",
    "percent": "{n} %",
}

LANGUAGES = {"en": EN, "sv": SV}


def get(lang: str | None, overrides: dict | None = None) -> dict:
    """Strings for a language code ('sv', 'sv-SE', ...), with the reader's `strings` from config.json on top.

    Built-in languages are complete tables. For any other language the agent translates the English table
    (`python -m sharectl_edition strings`) and puts the result under "strings" in config.json; keys left out
    fall back to the built-in table for that language, else English."""
    code = (lang or "en").lower().split("-")[0]
    table = json.loads(json.dumps(LANGUAGES.get(code, EN)))
    if code not in LANGUAGES and overrides:
        table["html_lang"] = code  # the agent translated the page, so the page says what language it is in
    for k, v in (overrides or {}).items():
        if isinstance(v, dict) and isinstance(table.get(k), dict):
            table[k].update(v)
        elif k in table:
            table[k] = v
    return table
