"""Optional: deploy the static folder to the reader's own Cloudflare Pages project with wrangler.

Needs `npx wrangler` and the env vars CLOUDFLARE_API_TOKEN (Pages: Edit) and CLOUDFLARE_ACCOUNT_ID.
The token belongs to the reader and is never written to the repo or config.
"""
import os
import subprocess


def deploy(out: str, project: str) -> int:
    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        raise SystemExit("CLOUDFLARE_API_TOKEN is not set. Ask your user to create a Pages:Edit token.")
    cmd = ["npx", "--yes", "wrangler@3", "pages", "deploy", out, "--project-name", project, "--branch", "main",
           "--commit-dirty=true"]
    return subprocess.run(cmd).returncode
