#!/usr/bin/env python3
"""
One-command build + deploy orchestrator for the Premier Equipment site.

  python run.py            # build only (= the 4 steps in order)
  python run.py --deploy   # build + deploy Pages
  python run.py --worker   # build + deploy Worker (cd worker && wrangler deploy)
  python run.py --all      # build + deploy both Pages and Worker

This wraps the steps documented in CLAUDE.md so Nicole / Missy never have to
remember the order. Every step prints what it ran and stops on the first error.
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("Build static site",  [sys.executable, "build.py"]),
    ("Build AI brain",     [sys.executable, "make_brain.py"]),
    ("Inject chat widget", [sys.executable, "add_widget.py"]),
    ("Generate content",   [sys.executable, "content.py"]),
]

def run(label, cmd, cwd=HERE):
    print(f"\n>> {label}")
    print(f"   $ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        print(f"\n!! {label} failed (exit {r.returncode})")
        sys.exit(r.returncode)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deploy", action="store_true", help="deploy site/ to Cloudflare Pages")
    ap.add_argument("--worker", action="store_true", help="deploy the Worker (worker/)")
    ap.add_argument("--all",    action="store_true", help="deploy both Pages and Worker")
    args = ap.parse_args()

    for label, cmd in STEPS:
        run(label, cmd)

    if args.all or args.deploy:
        run("Deploy Cloudflare Pages",
            ["npx", "--yes", "wrangler", "pages", "deploy", "site", "--project-name=premier-equipment"])
    if args.all or args.worker:
        run("Deploy Worker", ["npx", "--yes", "wrangler", "deploy"], cwd=os.path.join(HERE, "worker"))

    print("\nDone.")

if __name__ == "__main__":
    main()
