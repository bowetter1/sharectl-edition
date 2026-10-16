# sharectl-edition

**Tell your AI what you want to read. Get your first personal newspaper.**

Copy this into an AI chat that can run Python, edit files, and show or attach an HTML file:

> Make me a newspaper using https://github.com/bowetter1/sharectl-edition

Your AI asks what topics or sources you want to read, builds your paper, and opens it for you. If you already included your interests in the request, it can start straight away. You do not need to install anything yourself or edit a configuration file.

Your first edition is a local web page with headlines, short summaries, images, bylines, and links to the original articles. The interface uses your language; headlines and summaries keep the source's language.

Read it, then tell the same AI what to change: add a source, adjust coverage, or leave something out. It saves your choices for the next edition. Ask it to rebuild when you want to see the changes immediately.

**Start by reading.** Hosting and automatic daily editions can wait until you ask for them.

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
