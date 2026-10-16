# sharectl-edition

**Tell your AI what you want to read. Get your first personal newspaper.**

Copy this into an AI chat that can run Python, edit files, and show or attach an HTML file:

> Make me a newspaper using https://github.com/bowetter1/sharectl-edition

Your AI asks what topics or sources you want to read, selects the stories, and opens your paper. Python fetches the material and fills the existing template. If you already included your interests in the request, it can start straight away. You do not need to install anything yourself or edit a configuration file.

Your first edition is a local web page with headlines, short summaries, images, bylines, and links to the original articles. The interface uses your language; headlines and summaries keep the source's language.

Read it, then tell the same AI what to change: add a source, adjust coverage, or leave something out. It saves your choices for the next edition. Ask it to rebuild when you want to see the changes immediately.

**Start by reading.** After showing your first paper, your AI asks whether you want a web address and automatic daily editions. You can choose either, both, or keep reading locally. If you opt in, it helps you choose hosting and a delivery time.

## How it works

1. **Fetch:** Python saves candidate articles and the reader's current preferences to a private JSON file.
2. **Edit:** your AI chooses stories, removes duplicates, assigns sections and picks the lead story by ID.
3. **Render:** Python validates those references and fills the HTML template with the original headlines, summaries, links and bylines.

Existing `config.json` and `feedback.json` files are reused without migration. Rules and feedback are instructions for the AI editor, not an automatic ranking algorithm. No model API or API key is built into the package; the AI chat or scheduled agent performs the editorial step.

```bash
python3 -m sharectl_edition fetch --config config.json --out candidates.json
# The AI reads candidates.json and writes selection.json; see SKILL.md for the schema.
python3 -m sharectl_edition build --config config.json --items candidates.json --selection selection.json --out site/
```

Keep both JSON files private, outside `site/`. For publishing, use `publish` with the same arguments. Automatic daily editions require an AI-agent schedule running all three steps. Previous one-step `build` commands must be updated; rendering never silently falls back to rule-based selection.

For offline layout testing, `fetch --from-items examples/items.json` imports the fictional demo data into a candidate packet; an explicit selection is still required.

## See the layout

[View the demo](https://utgava.sharectl.com/).

The screenshot and files in `examples/` are a fictional layout demo, not default interests or subscriptions.

![Fictional example edition](examples/screenshot.jpg)

## For agents and developers

- [`SKILL.md`](SKILL.md): ask, save, build, and show the first edition.
- [`config.example.json`](config.example.json): neutral starter with no sources, topic preferences, weather, or markets selected.
- `sharectl_edition/`: the builder, using Python 3.10+ and the standard library. No package installation is required.

The AI handles setup in its own environment. If it cannot run Python or deliver HTML, it should explain that limitation rather than promise a working paper.

Part of [sharectl.com](https://sharectl.com). Headlines link to publishers; full articles are never republished. [MIT license](LICENSE).
