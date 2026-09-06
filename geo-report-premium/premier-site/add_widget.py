#!/usr/bin/env python3
"""Inject the AI chat widget into every generated page.
Run order:  python build.py  ->  python make_brain.py  ->  python add_widget.py
Set API to your deployed Worker URL to switch the chat from local answers to live AI + lead storage."""
import os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
API = ""  # e.g. "https://premier-equipment.<you>.workers.dev"  — leave "" to use built-in local answers

count = 0
SKIP_PREFIXES = ("admin" + os.sep,)  # admin pages get their own gated UI; no public chat widget
for path in glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True):
    rel = os.path.relpath(path, SITE)
    if rel.startswith(SKIP_PREFIXES):
        continue
    prefix = "../" * (rel.count(os.sep))   # machine/ pages need ../
    html = open(path, encoding="utf-8").read()
    if "pe-chat-injected" in html:
        continue
    snippet = (f'<script id="pe-chat-injected">window.PREMIER_API="{API}";'
               f'window.PREMIER_BRAIN_URL="{prefix}assets/brain.json";</script>'
               f'<script src="{prefix}assets/chat.js" defer></script>')
    html = html.replace("</body>", snippet + "</body>")
    open(path, "w", encoding="utf-8").write(html)
    count += 1
print(f"Chat widget injected into {count} pages. API={'(local answers)' if not API else API}")
