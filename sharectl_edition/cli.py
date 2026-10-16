"""Command line:
  python -m sharectl_edition fetch    --config config.json --out candidates.json
  python -m sharectl_edition build --config config.json --items candidates.json --selection selection.json --out site/
  python -m sharectl_edition publish --config config.json --items candidates.json --selection selection.json --out site/
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
    fetch = sub.add_parser("fetch", help="collect candidates and saved preferences for the AI editor")
    fetch.add_argument("--config", default="config.json")
    fetch.add_argument("--out", required=True, help="private candidate JSON, outside the published folder")
    fetch.add_argument("--from-items", help="import raw offline items, such as the fictional demo")
    for name in ("build", "publish"):
        p = sub.add_parser(name)
        p.add_argument("--config", default="config.json")
        p.add_argument("--out", default=None)
        p.add_argument("--items", required=True, help="candidate JSON from fetch")
        p.add_argument("--selection", required=True, help="AI selection JSON")
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

    from .build import CandidateError, collect
    if a.cmd == "fetch":
        packet = collect(cfg, base, a.from_items)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(packet, fh, ensure_ascii=False, indent=2)
        print(f"wrote {a.out}: {len(packet['items'])} candidates; AI selection required")
        return 0 if packet['items'] else 1

    from .publish import static
    from . import recovery

    target = cfg["publish"].get("target", "static")
    if a.cmd == "publish" and target == "github" and not cfg["publish"].get("repo_url"):
        from .publish import github
        raise ValueError(github.MISSING_REPO)

    out = a.out or os.path.join(base, cfg["publish"].get("out", "site"))
    try:
        state = recovery.state_path(a.config, out)
        html_text, report, packet = recovery.build(cfg, base, a.items, a.selection, state)
    except recovery.RetrySelection as exc:
        print(f"AI selection needs correction: {exc}", file=sys.stderr)
        return 2
    except CandidateError as exc:
        print(f"Cannot build edition: {exc}", file=sys.stderr)
        return 1
    date = report["date"][:10]
    if report.get('recovery', {}).get('mode') == 'previous':
        os.makedirs(out, exist_ok=True)
        path = os.path.join(out, 'index.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(html_text)
    else:
        path = static.write(html_text, out, date)
    with open(os.path.join(out, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    recovery.remember(state, packet, html_text, report)
    print(f"wrote {path}  {report['counts']}")
    if report.get('recovery'):
        print(f"WARNING: AI selection failed; using {report['recovery']['mode']} edition dated {report['date']}", file=sys.stderr)

    if a.cmd == "publish":
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
    return 0
