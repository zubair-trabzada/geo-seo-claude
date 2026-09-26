#!/usr/bin/env python3
"""Weekly content generator for Premier Equipment.
Builds: an email-ready inventory newsletter, a blog post for the site, and social drafts.
Run last:  python build.py -> make_brain.py -> add_widget.py -> content.py
Outputs newsletter + social to ./marketing/ and a post to ./site/blog/."""
import json, os, datetime
HERE=os.path.dirname(os.path.abspath(__file__))
DATA=json.load(open(os.path.join(HERE,"inventory.json"),encoding="utf-8"))
CO=DATA["company"]; M=[m for m in DATA["machines"] if m.get("status")=="available"]
TODAY=datetime.date.today(); DSTR=TODAY.strftime("%B %d, %Y"); SLUG=TODAY.isoformat()
MK=os.path.join(HERE,"marketing"); BLOG=os.path.join(HERE,"site","blog")
os.makedirs(MK,exist_ok=True); os.makedirs(BLOG,exist_ok=True)
base=CO["url"].rstrip("/")
feat=M[:5]
def murl(m): import re; return base+"/machine/"+re.sub(r'[^a-z0-9]+','-',f"{m['tonnage']}-ton-{m['brand']}-{m['model']}".lower()).strip('-')+".html"

# ---- NEWSLETTER (inline-styled, email-ready) ----
rows="".join(
 f'<tr><td style="padding:14px 0;border-bottom:1px solid #e6edee">'
 f'<a href="{murl(m)}" style="color:#136055;font:700 16px Arial,sans-serif;text-decoration:none">{m["tonnage"]}-Ton {m["brand"]} {m["model"]}</a>'
 f'<div style="font:400 13px Arial,sans-serif;color:#52606b;margin-top:3px">{m["year"]} &middot; {m["shot_size"]} shot &middot; {m["controller"]} &middot; {m["hours"]:,} hrs &middot; {m["condition"]}</div>'
 f'<div style="font:400 13px Arial,sans-serif;color:#222;margin-top:3px">{m["summary"]}</div></td></tr>' for m in feat)
news=(f'<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif">'
 f'<div style="background:#0C2A2A;padding:22px 24px;border-radius:10px 10px 0 0"><div style="color:#fff;font-weight:800;font-size:18px;letter-spacing:.5px">PREMIER EQUIPMENT</div>'
 f'<div style="color:#9FBDB7;font-size:11px;letter-spacing:1px">YOUR PLASTICS MACHINERY SOURCE</div></div>'
 f'<div style="background:#F26A21;height:4px"></div>'
 f'<div style="padding:24px;background:#fff">'
 f'<h1 style="font-size:22px;color:#13212b;margin:0 0 6px">This Week in Stock</h1>'
 f'<p style="font-size:14px;color:#52606b;margin:0 0 18px">{DSTR} &mdash; {len(M)} machines available now. Inspected, documented, ready to ship.</p>'
 f'<table width="100%" cellpadding="0" cellspacing="0">{rows}</table>'
 f'<div style="text-align:center;margin-top:24px"><a href="{base}/inventory.html" style="background:#F26A21;color:#fff;font-weight:700;font-size:15px;padding:13px 24px;border-radius:8px;text-decoration:none">See All {len(M)} Machines</a></div>'
 f'<p style="font-size:13px;color:#52606b;margin-top:22px">Looking for a specific tonnage? Reply to this email or call <b>{CO["phone"]}</b> and we will pull it for you.</p>'
 f'</div><div style="background:#0C1F1E;color:#9FBDB7;font-size:11px;padding:16px 24px;border-radius:0 0 10px 10px">{CO["name"]} &middot; {CO["city"]}, {CO["region"]} {CO["postal"]} &middot; {CO["phone"]}</div></div>')
open(os.path.join(MK,f"newsletter-{SLUG}.html"),"w",encoding="utf-8").write(news)

# ---- BLOG POST (on-site, SEO content) ----
post=(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
 f'<title>New In Stock — {DSTR} | {CO["name"]}</title>'
 f'<meta name="description" content="New used injection molding machines in stock at Premier Equipment as of {DSTR}: '+", ".join(f'{m["tonnage"]}-ton {m["brand"]}' for m in feat)+'.">'
 f'<style>body{{font-family:Georgia,serif;max-width:740px;margin:0 auto;padding:40px 22px;color:#1b2b33;line-height:1.7}}'
 f'h1{{font-size:30px}}a{{color:#136055}}.m{{border-left:3px solid #1B8A7A;padding:6px 0 6px 14px;margin:14px 0}}.cta{{background:#F26A21;color:#fff;padding:12px 22px;border-radius:8px;text-decoration:none;display:inline-block;margin-top:18px}}</style></head><body>'
 f'<p><a href="../inventory.html">&larr; Inventory</a></p><h1>New In Stock &mdash; {DSTR}</h1>'
 f'<p>Here is what just landed and passed inspection at {CO["name"]} in {CO["city"]}, {CO["region"]}. Every machine includes a documented condition report and true hours.</p>'
 + "".join(f'<div class="m"><a href="{murl(m)}"><b>{m["tonnage"]}-Ton {m["brand"]} {m["model"]}</b></a><br>{m["year"]} &middot; {m["shot_size"]} shot &middot; {m["controller"]} &middot; {m["hours"]:,} hrs &middot; {m["condition"]}.<br>{m["summary"]}</div>' for m in feat)
 + f'<a class="cta" href="../inventory.html">Browse all {len(M)} machines</a>'
 f'<p style="font-size:14px;color:#52606b;margin-top:24px">Questions on tonnage or shipping? Call {CO["phone"]}.</p></body></html>')
open(os.path.join(BLOG,f"{SLUG}-new-inventory.html"),"w",encoding="utf-8").write(post)

# ---- SOCIAL DRAFTS ----
top=feat[0]
soc=f"""# Premier Equipment — Social Drafts ({DSTR})

## LinkedIn
{len(M)} used injection molding machines in stock and inspected this week at Premier Equipment (Beachwood, OH).

Highlights:
""" + "".join(f"• {m['tonnage']}-ton {m['brand']} {m['model']} — {m['condition']}, {m['hours']:,} hrs\n" for m in feat) + f"""
Every machine ships with a documented condition report and true hours. Need a specific tonnage? We'll pull it. 📞 {CO['phone']}
{base}/inventory.html
#injectionmolding #plastics #usedmachinery #manufacturing

## Facebook
🏭 New in stock at Premier Equipment! {len(M)} inspected injection molding machines ready to ship nationwide — from {min(m['tonnage'] for m in M)} to {max(m['tonnage'] for m in M)} tons. Documented condition reports, true hours, no surprises. Call {CO['phone']} or browse: {base}/inventory.html

## X / Twitter (single)
{len(M)} used injection molding machines in stock & inspected at Premier Equipment. {top['tonnage']}-ton {top['brand']} {top['model']} just landed. Ships nationwide. {base}/inventory.html

## X / Twitter (thread)
1/ {len(M)} used injection molding machines in stock this week at Premier Equipment (Beachwood, OH) 🧵
""" + "".join(f"{i+2}/ {m['tonnage']}-ton {m['brand']} {m['model']}: {m['year']}, {m['shot_size']} shot, {m['controller']}, {m['hours']:,} hrs, {m['condition']}. {m['summary']}\n" for i,m in enumerate(feat)) + f"{len(feat)+2}/ All inspected with documented condition reports. Call {CO['phone']} or see them all: {base}/inventory.html\n"
open(os.path.join(MK,f"social-{SLUG}.md"),"w",encoding="utf-8").write(soc)

print(f"Generated: marketing/newsletter-{SLUG}.html, marketing/social-{SLUG}.md, site/blog/{SLUG}-new-inventory.html")
