"""Command line:
  python -m sharectl_edition build    --config config.json --out site/
  python -m sharectl_edition publish  --config config.json --out site/
  python -m sharectl_edition feedback import feedback-2026-10-16.json --config config.json
  python -m sharectl_edition feedback show --config config.json
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
    f.add_argument("action", choices=["import", "show", "add", "hide"])
    f.add_argument("arg", nargs="*", help="import: FILE | add: ITEM_ID up|down | hide: SOURCE_OR_AUTHOR")
    f.add_argument("--config", default="config.json")
    a = ap.parse_args(argv)

    cfg = cfgmod.load(a.config)
    base = os.path.dirname(os.path.abspath(a.config))
    fb_path = os.path.join(base, cfg["feedback_file"])

    if a.cmd == "feedback":
        w = feedback.load(fb_path)
        if a.action == "import":
            print(f"imported {feedback.import_file(fb_path, a.arg[0])} events")
            return
        if a.action == "add":
            feedback.apply(w, {"item_id": a.arg[0], "vote": a.arg[1], "source": a.arg[2] if len(a.arg) > 2 else "",
                               "ts": "cli"})
        if a.action == "hide":
            w["hidden"] = sorted(set(w["hidden"]) | {feedback.norm(a.arg[0])})
        if a.action in ("add", "hide"):
            feedback.save(fb_path, w)
        print(json.dumps({k: v for k, v in w.items() if k != "seen"}, indent=1, ensure_ascii=False))
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
        if target == "cloudflare":
            from .publish import cloudflare
            sys.exit(cloudflare.deploy(out, cfg["publish"]["project"]))
        if target == "sharectl":
            from .publish import sharectl
            print("POST", sharectl.post(html_text, cfg["publish"]["url"], cfg["publish"].get("token_env", "SHARECTL_TOKEN"), date))
        else:
            print(f"static edition ready in {out}/ (open index.html, or serve the folder anywhere)")
