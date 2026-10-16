"""Command line:
  python -m sharectl_edition fetch --config config.json --out candidates.json
  python -m sharectl_edition build --config config.json --items candidates.json --selection selection.json --out site/
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
    
    fetch = sub.add_parser("fetch", help="collect RSS candidates for AI selection")
    fetch.add_argument("--config", default="config.json")
    fetch.add_argument("--out", required=True, help="candidate JSON file")
    
    build = sub.add_parser("build", help="render AI selection to local HTML")
    build.add_argument("--config", default="config.json")
    build.add_argument("--out", default="site")
    build.add_argument("--items", required=True, help="candidate JSON from fetch")
    build.add_argument("--selection", required=True, help="AI selection JSON")
    
    f = sub.add_parser("feedback")
    f.add_argument("action", choices=["show", "boost", "mute", "hide"])
    f.add_argument("arg", nargs="*")
    f.add_argument("--config", default="config.json")
    
    a = ap.parse_args(argv)

    cfg = cfgmod.load(a.config)
    base = os.path.dirname(os.path.abspath(a.config))
    fb_path = os.path.join(base, cfg["feedback_file"])

    if a.cmd == "feedback":
        w = feedback.load(fb_path)
        if a.action == "boost":
            if len(a.arg) < 2:
                print("usage: feedback boost IDENTIFIER AMOUNT")
                return 1
            feedback.bump(w, "sources", a.arg[0], float(a.arg[1]))
            feedback.save(fb_path, w)
        elif a.action == "mute":
            if len(a.arg) < 2:
                print("usage: feedback mute KEYWORD AMOUNT")
                return 1
            feedback.bump(w, "keywords", a.arg[0], float(a.arg[1]))
            feedback.save(fb_path, w)
        elif a.action == "hide":
            if not a.arg:
                print("usage: feedback hide IDENTIFIER")
                return 1
            feedback.hide(w, a.arg[0])
            feedback.save(fb_path, w)
        print(json.dumps(w, indent=1, ensure_ascii=False))
        return

    from .build import CandidateError, collect
    if a.cmd == "fetch":
        packet = collect(cfg)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(packet, fh, ensure_ascii=False, indent=2)
        print(f"wrote {a.out}: {len(packet['items'])} candidates")
        return 0 if packet['items'] else 1

    if a.cmd == "build":
        try:
            html_text, report = build_from_files(cfg, base, a.items, a.selection)
        except (CandidateError, SelectionError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        
        date = report["date"][:10]
        os.makedirs(a.out, exist_ok=True)
        path = os.path.join(a.out, 'index.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(html_text)
        with open(os.path.join(a.out, "report.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
        print(f"wrote {path}  {report['counts']}")
    return 0


class SelectionError(ValueError):
    """AI selection is invalid."""


def build_from_files(cfg, base_dir, items_path, selection_path):
    """Load candidates and selection, then render."""
    from .build import load_candidates, load_selection, render_selection
    packet = load_candidates(cfg, base_dir, items_path)
    selection = load_selection(selection_path)
    return render_selection(cfg, packet, selection)
