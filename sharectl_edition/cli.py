"""Command line:
  python -m sharectl_edition build    --config config.json --out site/
  python -m sharectl_edition publish  --config config.json --out site/
  python -m sharectl_edition feedback show --config config.json
  python -m sharectl_edition strings  --lang en     # the UI strings as JSON, for translating into the reader's language
"""
import argparse
import json
import os
import sys

from . import config as cfgmod
from . import feedback


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sharectl_edition")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "publish"):
        p = sub.add_parser(name)
        p.add_argument("--config", default="config.json")
        p.add_argument("--out", default=None)
        p.add_argument("--from-items", default=None, help="re-render from a saved items.json (no network)")
        p.add_argument("--save-items", default=None, help="save fetched items to this JSON file")
    f = sub.add_parser("feedback")
    f.add_argument("action", choices=["show", "boost", "mute", "hide"])
    f.add_argument("arg", nargs="*", help="boost/mute: IDENTIFIER AMOUNT | hide: IDENTIFIER")
    f.add_argument("--config", default="config.json")
    s = sub.add_parser("strings", help="print the UI strings for a language as JSON (translate, then put under 'strings' in config.json)")
    s.add_argument("--lang", default="en")
    a = ap.parse_args(argv)

    if a.cmd == "strings":
        from .render import labels
        print(json.dumps(labels.get(a.lang), indent=1, ensure_ascii=False))
        return

    cfg = cfgmod.load(a.config)
    base = os.path.dirname(os.path.abspath(a.config))
    fb_path = os.path.join(base, cfg["feedback_file"])

    if a.cmd == "feedback":
        w = feedback.load(fb_path)
        if a.action == "boost":
            if len(a.arg) < 2:
                print("usage: feedback boost IDENTIFIER AMOUNT")
                return 1
            cat = "sources" if not a.arg[0].startswith("@") else "authors"
            feedback.bump(w, cat, a.arg[0], float(a.arg[1]))
            feedback.save(fb_path, w)
        elif a.action == "mute":
            if len(a.arg) < 2:
                print("usage: feedback mute IDENTIFIER AMOUNT")
                return 1
            cat = "keywords"
            feedback.bump(w, cat, a.arg[0], float(a.arg[1]))
            feedback.save(fb_path, w)
        elif a.action == "hide":
            if not a.arg:
                print("usage: feedback hide IDENTIFIER")
                return 1
            feedback.hide(w, a.arg[0])
            feedback.save(fb_path, w)
        print(json.dumps(w, indent=1, ensure_ascii=False))
        return

    from .build import build
    from .publish import static

    out = a.out or os.path.join(base, cfg["publish"].get("out", "site"))
    html_text, report = build(cfg, base, a.from_items)
    if a.save_items and "raw" in report:
        with open(a.save_items, "w", encoding="utf-8") as fh:
            json.dump(report["raw"], fh, ensure_ascii=False, indent=1)
    report.pop("raw", None)
    date = report["date"][:10]
    path = static.write(html_text, out, date)
    with open(os.path.join(out, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(f"wrote {path}  {report['counts']}")

    if a.cmd == "publish":
        target = cfg["publish"].get("target", "static")
        if target == "github":
            from .publish import github
            repo = cfg["publish"].get("repo_url")
            branch = cfg["publish"].get("branch", "gh-pages")
            sys.exit(github.deploy(out, repo, branch))
        elif target == "cloudflare":
            from .publish import cloudflare
            sys.exit(cloudflare.deploy(out, cfg["publish"]["project"]))
        elif target == "sharectl":
            from .publish import sharectl
            print("POST", sharectl.post(html_text, cfg["publish"]["url"], cfg["publish"].get("token_env", "SHARECTL_TOKEN"), date))
        else:
            print(f"static edition ready in {out}/ (open index.html, or serve the folder anywhere)")
