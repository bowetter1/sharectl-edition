"""Optional: deploy the static folder to GitHub Pages.

Pushes the built site to a gh-pages branch in the reader's own repository.
No credentials needed if the bot already has git push access to the repo.
"""
import os
import subprocess
import shutil
import tempfile

MISSING_REPO = ('publish.repo_url is required for GitHub Pages: the URL of the reader\'s own repository. '
                'The current checkout\'s origin is never assumed, since it is usually this tool\'s public repository.')


def deploy(out: str, repo_url: str, branch: str = "gh-pages") -> int:
    """Push the static site to GitHub Pages.

    Args:
        out: Path to the built site directory
        repo_url: Git repository URL of the reader's own repository (required)
        branch: Target branch (default: gh-pages)

    Returns:
        0 on success, non-zero on failure
    """
    if not repo_url:
        print(f"Error: {MISSING_REPO}")
        return 1

    if not os.path.isdir(out):
        print(f"Error: Output directory {out} does not exist")
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        deploy_dir = os.path.join(tmpdir, "deploy")
        
        print(f"Cloning {repo_url} (branch: {branch})...")
        clone_result = subprocess.run(
            ["git", "clone", "--depth=1", "--branch", branch, repo_url, deploy_dir],
            capture_output=True, text=True
        )
        
        if clone_result.returncode != 0:
            print(f"Branch {branch} does not exist yet, creating orphan branch...")
            os.makedirs(deploy_dir)
            subprocess.run(["git", "init"], cwd=deploy_dir, check=True)
            subprocess.run(["git", "checkout", "--orphan", branch], cwd=deploy_dir, check=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=deploy_dir, check=True)
        
        for item in os.listdir(deploy_dir):
            if item != ".git":
                item_path = os.path.join(deploy_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        
        for item in os.listdir(out):
            src = os.path.join(out, item)
            dst = os.path.join(deploy_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        subprocess.run(["git", "add", "-A"], cwd=deploy_dir, check=True)
        
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=deploy_dir
        )
        
        if not status.stdout.strip():
            print(f"No changes to deploy to {branch}")
            return 0
        
        subprocess.run(
            ["git", "config", "user.name", "sharectl-edition"],
            cwd=deploy_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "bot@sharectl.local"],
            cwd=deploy_dir, check=True
        )
        
        from datetime import datetime
        commit_msg = f"Deploy edition {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=deploy_dir, check=True)
        
        print(f"Pushing to {branch}...")
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=deploy_dir
        )
        
        if push_result.returncode == 0:
            print(f"✓ Deployed to {branch} branch")
            repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
            owner = repo_url.rstrip("/").split("/")[-2].split(":")[-1]
            print(f"  View at: https://{owner}.github.io/{repo_name}/")
        
        return push_result.returncode
