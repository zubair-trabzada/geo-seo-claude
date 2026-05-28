#!/usr/bin/env python3
"""
Premier Equipment static-site generator.
Reads inventory.json (single source of truth) and writes a full SEO + GEO site to ./site/.
Run:  python build.py     then deploy ./site with Cloudflare Pages (see DEPLOY.md).
No Replit. No database needed for v1 — the inventory file IS the database.
"""
import json, os, re, shutil, datetime, stat

def _force_writable(func, path, _exc):
    # Windows: read-only files refuse to be deleted/overwritten. Strip the bit and retry.
    try: os.chmod(path, stat.S_IWRITE)
    except Exception: pass
    func(path)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "inventory.json"), encoding="utf-8"))
OUT  = os.path.join(HERE, "site")
CO   = DATA["company"]
STATS = DATA.get("stats", {})
CERTS = DATA.get("certifications", [])
SERVICES = DATA.get("services", [])
TODAY = datetime.date.today().isoformat()

def slug(m): return re.sub(r'[^a-z0-9]+','-', f"{m['tonnage']}-ton-{m['brand']}-{m['model']}".lower()).strip('-')
def murl(m): return f"machine/{slug(m)}.html"
def avail(): return [m for m in DATA["machines"] if m.get("status")=="available"]

STYLE = """
*{margin:0;padding:0;box-sizing:border-box}html{scroll-behavior:smooth}
body{font-family:'Plus Jakarta Sans',system-ui,sans-serif;color:#13212B;background:#fff;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
.serif{font-family:'Fraunces',Georgia,serif}
.btn{display:inline-flex;align-items:center;gap:8px;font-weight:700;font-size:15px;padding:12px 20px;border-radius:10px;border:none;cursor:pointer;transition:.18s;text-align:center;justify-content:center}
.btn-primary{background:#F26A21;color:#fff}.btn-primary:hover{background:#d9591a}
.btn-teal{background:#1B8A7A;color:#fff}.btn-teal:hover{background:#136055}
.btn-ghost{background:transparent;border:1.5px solid #E3E9EC}.btn-ghost:hover{border-color:#1B8A7A;color:#1B8A7A}
.btn-dark{background:#0C2A2A;color:#fff}.btn-dark:hover{background:#13524A}
.pill{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#1B8A7A;background:rgba(43,184,163,.12);padding:6px 13px;border-radius:30px}
header{position:sticky;top:0;z-index:50;background:rgba(12,42,42,.94);backdrop-filter:blur(10px);border-bottom:1px solid rgba(255,255,255,.08)}
.nav{display:flex;align-items:center;justify-content:space-between;height:78px}
.brandlogo{height:42px;display:block}
.navlinks{display:flex;gap:22px;font-weight:600;font-size:14.5px;color:#C9DAD6}.navlinks a:hover{color:#2FB8A3}
.navright{display:flex;align-items:center;gap:14px}.navphone{font-weight:700;color:#fff;font-size:14.5px}
.menu-btn{display:none;background:none;border:1px solid rgba(255,255,255,.25);color:#fff;border-radius:8px;width:42px;height:38px;font-size:18px;cursor:pointer}
@media(max-width:980px){.navlinks,.navphone{display:none}.menu-btn{display:inline-block}}
.mobile-nav{display:none;background:#0C2A2A;border-top:1px solid rgba(255,255,255,.08);padding:8px 24px 16px}
.mobile-nav.open{display:block}
.mobile-nav a{display:block;color:#C9DAD6;font-weight:600;padding:10px 0;font-size:15px;border-bottom:1px solid rgba(255,255,255,.06)}
.mobile-nav a:last-child{border-bottom:none}
.hero{background:linear-gradient(160deg,#0C2A2A,#13524A);color:#fff}
.hero .wrap{padding:64px 24px}.hero h1{font-size:46px;line-height:1.06;font-weight:600;letter-spacing:-1px;margin:14px 0 12px}
.hero h1 em{font-style:italic;color:#2FB8A3}.hero p{font-size:18px;color:#C9DAD6;max-width:560px}
.hero .entity{font-size:13px;color:#9FBDB7;font-weight:600;margin:18px 0 22px}
.hero .cta-row{display:flex;gap:12px;flex-wrap:wrap}.hero .btn-ghost{color:#fff;border-color:rgba(255,255,255,.35)}
.hero .btn-ghost:hover{background:rgba(255,255,255,.08);color:#fff}
@media(max-width:640px){.hero h1{font-size:34px}.hero .wrap{padding:46px 20px}}
.stats{background:#0C1F1E;color:#D7F0EB;padding:24px 0}
.stats .row{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;text-align:center}
.stats .v{font-family:'Fraunces',serif;font-size:30px;color:#2FB8A3;display:block;line-height:1.1}
.stats .k{font-size:12px;letter-spacing:.6px;text-transform:uppercase;color:#9FBDB7;margin-top:4px;display:block}
@media(max-width:640px){.stats .row{grid-template-columns:repeat(2,1fr);gap:18px}}
section{padding:64px 0}.sec-head{text-align:center;max-width:680px;margin:0 auto 38px}
.sec-head h2{font-size:34px;font-weight:600;letter-spacing:-.5px;margin:10px 0 8px}.sec-head p{color:#52606B;font-size:16px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}@media(max-width:900px){.grid{grid-template-columns:1fr}}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:22px}@media(max-width:760px){.grid-2{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid #E3E9EC;border-radius:16px;overflow:hidden;transition:.2s;display:flex;flex-direction:column}
.card:hover{box-shadow:0 24px 60px rgba(19,33,43,.14);transform:translateY(-3px);border-color:rgba(43,184,163,.4)}
.card .ph{height:160px;background:linear-gradient(135deg,#1B8A7A,#0C2A2A);position:relative;display:flex;align-items:center;justify-content:center;background-size:cover;background-position:center}
.card .ph .ton{font-family:'Fraunces',serif;font-size:44px;color:rgba(255,255,255,.92)}
.card .ph .badge{position:absolute;top:12px;left:12px;background:#F26A21;color:#fff;font-size:11px;font-weight:700;padding:5px 10px;border-radius:6px}
.card .ph .cond{position:absolute;top:12px;right:12px;background:rgba(255,255,255,.92);color:#136055;font-size:11px;font-weight:700;padding:5px 10px;border-radius:6px}
.card .body{padding:17px 18px;flex:1;display:flex;flex-direction:column}
.card h3{font-size:18px;font-weight:700}.card .lede{font-size:13px;color:#52606B;margin:5px 0 12px}
.specs{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;font-size:12.5px;margin-bottom:14px}
.specs div{display:flex;justify-content:space-between;border-bottom:1px dotted #E3E9EC;padding-bottom:4px}.specs .k{color:#52606B}.specs .v{font-weight:700}
.card .actions{margin-top:auto;display:flex;gap:8px}.card .actions .btn{flex:1;font-size:13px;padding:10px}
.bc{font-size:13px;color:#52606B;padding:18px 0}.bc a{color:#1B8A7A}
.prod{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:start}@media(max-width:900px){.prod{grid-template-columns:1fr}}
.prod .vis{height:340px;border-radius:16px;background:linear-gradient(135deg,#1B8A7A,#0C2A2A);display:flex;align-items:center;justify-content:center;color:#fff;font-family:'Fraunces',serif;font-size:84px;background-size:cover;background-position:center}
.prod .specs{grid-template-columns:1fr;font-size:14.5px;margin:18px 0}
.qa{border:1px solid #E3E9EC;border-radius:12px;margin-bottom:12px;background:#fff}
.qa summary{padding:16px 20px;font-weight:700;font-size:15.5px;cursor:pointer;list-style:none;display:flex;justify-content:space-between}
.qa summary::-webkit-details-marker{display:none}.qa summary::after{content:"+";color:#1B8A7A;font-size:22px}.qa[open] summary::after{content:"\\2013"}
.qa .ans{padding:0 20px 18px;color:#52606B;font-size:14px}
.band{background:linear-gradient(120deg,#136055,#1B8A7A);color:#fff;text-align:center}.band h2{font-size:30px;font-weight:600;margin-bottom:10px}.band p{color:#D7F0EB;margin-bottom:20px;max-width:580px;margin-left:auto;margin-right:auto}
.band .cta-row{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.svc{background:#fff;border:1px solid #E3E9EC;border-radius:16px;padding:24px}
.svc h3{font-family:'Fraunces',serif;font-size:22px;margin-bottom:6px;color:#0C2A2A}
.svc .lede{color:#52606B;font-size:14.5px;margin-bottom:12px}
.svc ul{list-style:none;padding:0}.svc li{padding:7px 0 7px 22px;position:relative;font-size:14px;color:#13212B}
.svc li:before{content:"";position:absolute;left:0;top:14px;width:8px;height:8px;background:#1B8A7A;border-radius:50%}
.form{background:#fff;border:1px solid #E3E9EC;border-radius:16px;padding:24px}
.form .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:640px){.form .row{grid-template-columns:1fr}}
.form label{display:block;font-size:12.5px;font-weight:700;color:#52606B;margin:10px 0 4px;text-transform:uppercase;letter-spacing:.4px}
.form input,.form select,.form textarea{width:100%;padding:11px 12px;border:1.5px solid #e1e7ea;border-radius:9px;font-size:15px;font-family:inherit;background:#fff;color:#13212B}
.form input:focus,.form select:focus,.form textarea:focus{outline:none;border-color:#1B8A7A}
.form .submit-row{display:flex;gap:10px;align-items:center;margin-top:16px;flex-wrap:wrap}
.form .ok{display:none;background:#E6F4F1;color:#136055;border:1px solid #B6DBD2;padding:10px 14px;border-radius:9px;font-size:14px;font-weight:600;margin-top:14px}
.form .err{display:none;background:#FCE9DF;color:#B23E0F;border:1px solid #F2C2A9;padding:10px 14px;border-radius:9px;font-size:14px;font-weight:600;margin-top:14px}
.tile-info{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:18px}
@media(max-width:760px){.tile-info{grid-template-columns:1fr}}
.tile-info .ti{background:#F6F9F9;border-radius:12px;padding:16px}.tile-info .ti h4{font-size:13px;color:#136055;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.tile-info .ti p{font-size:14.5px;color:#13212B}
.cert-row{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:18px}
.cert{background:#F6F9F9;border:1px solid #E3E9EC;border-radius:30px;padding:8px 16px;font-size:13px;font-weight:700;color:#136055}
.cert small{display:block;color:#52606B;font-weight:500;font-size:11px;margin-top:2px}
.mob-cta{display:none;position:fixed;left:0;right:0;bottom:0;z-index:60;background:rgba(12,42,42,.97);backdrop-filter:blur(10px);border-top:1px solid rgba(255,255,255,.08);padding:10px 14px;gap:8px}
.mob-cta a{flex:1;font-size:14px;padding:11px 8px;color:#fff;font-weight:700;border-radius:10px;text-align:center;text-decoration:none}
.mob-cta .a1{background:#F26A21}.mob-cta .a2{background:#1B8A7A}.mob-cta .a3{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2)}
@media(max-width:760px){.mob-cta{display:flex}body{padding-bottom:64px}}
footer{background:#0C1F1E;color:#9FBDB7;padding:50px 0 24px;font-size:14px}
.foot-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:34px;margin-bottom:30px}@media(max-width:900px){.foot-grid{grid-template-columns:1fr 1fr}}
footer h5{color:#fff;font-size:13px;letter-spacing:1px;text-transform:uppercase;margin-bottom:12px}
footer a{display:block;color:#9FBDB7;padding:4px 0}footer a:hover{color:#2FB8A3}
.foot-bot{border-top:1px solid rgba(255,255,255,.1);padding-top:18px;font-size:12.5px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
.foot-bot .lc{color:#52606B}.foot-bot .lc a{display:inline;color:#9FBDB7}
"""

NAV_LINKS = [
    ("inventory.html", "Inventory"),
    ("sell.html", "Sell Your Machine"),
    ("services.html", "Services"),
    ("about.html", "About"),
    ("faq.html", "FAQ"),
    ("contact.html", "Contact"),
]

def header(prefix=""):
    desktop_links = "".join(f'<a href="{prefix}{u}">{t}</a>' for u, t in NAV_LINKS)
    mobile_links  = "".join(f'<a href="{prefix}{u}">{t}</a>' for u, t in NAV_LINKS)
    mobile_links += f'<a href="tel:{CO["phone_e164"]}" style="color:#2FB8A3">Call {CO["phone"]}</a>'
    return ('<header><div class="wrap nav">'
            f'<a class="logo" href="{prefix}index.html"><img class="brandlogo" src="{prefix}premier-logo.svg" alt="Premier Equipment — Your Plastics Machinery Source"></a>'
            f'<nav class="navlinks">{desktop_links}</nav>'
            '<div class="navright">'
            f'<span class="navphone">{CO["phone"]}</span>'
            f'<a class="btn btn-primary" href="{prefix}inventory.html">Browse</a>'
            '<button class="menu-btn" onclick="document.getElementById(\'mnav\').classList.toggle(\'open\')" aria-label="Menu">&#9776;</button>'
            '</div></div>'
            f'<div id="mnav" class="mobile-nav">{mobile_links}</div>'
            '</header>')

def mobile_cta(prefix=""):
    return (f'<div class="mob-cta">'
            f'<a class="a1" href="tel:{CO["phone_e164"]}">&#9742; Call</a>'
            f'<a class="a2" href="sms:{CO["phone_e164"]}">&#9993; Text</a>'
            f'<a class="a3" href="{prefix}contact.html">Quote</a>'
            f'</div>')

def footer(prefix=""):
    return ('<footer><div class="wrap"><div class="foot-grid">'
            f'<div><img class="brandlogo" src="{prefix}premier-logo.svg" style="height:46px;margin-bottom:12px" alt="Premier Equipment">'
            f'<p style="max-width:280px;font-size:13.5px">{CO["name"]} — buying and selling inspected used injection molding machines from {CO["city"]}, {CO["region"]} for {STATS.get("years_in_business",55)}+ years.</p></div>'
            f'<div><h5>Buy</h5><a href="{prefix}inventory.html">All Inventory</a><a href="{prefix}faq.html">Buyer FAQ</a><a href="{prefix}contact.html">Request a Quote</a></div>'
            f'<div><h5>Sell &amp; Services</h5><a href="{prefix}sell.html">Sell Your Machine</a><a href="{prefix}services.html#appraisals">Appraisals</a><a href="{prefix}services.html#rigging">Rigging &amp; Freight</a></div>'
            f'<div><h5>Contact</h5><a href="tel:{CO["phone_e164"]}">{CO["phone"]}</a><a href="mailto:{CO["email"]}">{CO["email"]}</a><a href="{prefix}contact.html">{CO["city"]}, {CO["region"]} {CO["postal"]}</a></div>'
            f'</div><div class="foot-bot"><span>&copy; {datetime.date.today().year} {CO["name"]} &middot; Used Injection Molding Machines &middot; Nationwide Shipping</span><span class="lc">Site by <a href="https://lacrown.ai" target="_blank" rel="noopener">La Crown</a></span></div>'
            '</div></footer>')

def page(path, title, desc, body, jsonld=None, prefix="", script=""):
    canon = CO["url"].rstrip("/") + "/" + path
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    og_image = CO["url"].rstrip("/") + "/og.svg"
    html = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{title}</title><meta name=\"description\" content=\"{desc}\">"
            f"<link rel=\"canonical\" href=\"{canon}\">"
            f"<link rel=\"icon\" type=\"image/svg+xml\" href=\"{prefix}favicon.svg\">"
            f"<meta property=\"og:title\" content=\"{title}\"><meta property=\"og:description\" content=\"{desc}\">"
            f"<meta property=\"og:type\" content=\"website\"><meta property=\"og:url\" content=\"{canon}\">"
            f"<meta property=\"og:image\" content=\"{og_image}\">"
            "<meta name=\"twitter:card\" content=\"summary_large_image\">"
            f"<meta name=\"twitter:image\" content=\"{og_image}\">"
            "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">"
            "<link href=\"https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap\" rel=\"stylesheet\">"
            f"{ld}<style>{STYLE}</style></head><body>"
            f"{header(prefix)}{body}{mobile_cta(prefix)}{footer(prefix)}{script}</body></html>")
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(html)

def org_ld():
    return {"@context":"https://schema.org","@type":["Organization","LocalBusiness"],
        "name":CO["name"],"alternateName":f'Premier Equipment — {CO["tagline"]}',
        "description":"Dealer of used injection molding machines, Beachwood OH. Buy, sell, and appraise plastics machinery.",
        "url":CO["url"],"telephone":CO["phone_e164"],"email":CO["email"],
        "address":{"@type":"PostalAddress","addressLocality":CO["city"],"addressRegion":CO["region"],"postalCode":CO["postal"],"addressCountry":"US"},
        "areaServed":"US","knowsAbout":["used injection molding machines","plastics machinery appraisal","tonnage selection","rigging and freight"],
        "founder":{"@type":"Person","name":CO.get("owner_name","Nicole Haas"),"jobTitle":CO.get("owner_title","Owner"),"sameAs":[CO.get("owner_linkedin")] if CO.get("owner_linkedin") else []},
        "sameAs":["https://www.linkedin.com/company/premier-equipment"] + ([CO["owner_linkedin"]] if CO.get("owner_linkedin") else [])}

def card_photo_style(m):
    p = (m.get("photo") or "").strip()
    return f' style="background-image:linear-gradient(180deg,rgba(12,42,42,0) 55%,rgba(12,42,42,.55)),url(\'{p}\')"' if p else ""

def card(m, prefix=""):
    return (f'<div class="card"><div class="ph"{card_photo_style(m)}><span class="badge">{m["brand"].upper()}</span>'
            f'<span class="cond">{m["condition"]}</span>'
            + ('' if (m.get("photo") or "").strip() else f'<span class="ton">{m["tonnage"]}T</span>')
            + '</div>'
            f'<div class="body"><h3>{m["brand"]} {m["model"]}</h3><p class="lede">{m["summary"]}</p>'
            '<div class="specs">'
            f'<div><span class="k">Tonnage</span><span class="v">{m["tonnage"]} T</span></div>'
            f'<div><span class="k">Year</span><span class="v">{m["year"]}</span></div>'
            f'<div><span class="k">Shot</span><span class="v">{m["shot_size"]}</span></div>'
            f'<div><span class="k">Hours</span><span class="v">{m["hours"]:,}</span></div>'
            '</div><div class="actions">'
            f'<a class="btn btn-teal" href="{prefix}{murl(m)}">View Specs</a>'
            f'<a class="btn btn-ghost" href="tel:{CO["phone_e164"]}">Call</a>'
            '</div></div></div>')

# Reusable form-post JS — posts to window.PREMIER_API/api/lead set by add_widget.py.
# If API is unset, shows a "call or email" fallback so the form still feels responsive.
FORM_JS = """
<script>
(function(){
  function bind(formId,kind){
    var f=document.getElementById(formId); if(!f) return;
    f.addEventListener('submit',function(e){
      e.preventDefault();
      var ok=f.querySelector('.ok'), err=f.querySelector('.err'); ok.style.display='none'; err.style.display='none';
      var data={type:kind}; new FormData(f).forEach(function(v,k){data[k]=v;});
      var api=(window.PREMIER_API||'').replace(/\\/$/,'');
      var done=function(success){
        if(success){ok.style.display='block'; f.reset();} else {err.style.display='block';}
      };
      if(!api){ done(true); return; } // local preview: show success
      fetch(api+'/api/lead',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
        .then(function(r){done(r.ok);}).catch(function(){done(false);});
    });
  }
  bind('sell-form','seller'); bind('contact-form','contact'); bind('quote-form','quote');
})();
</script>
"""

# ---- BUILD ----
if os.path.isdir(OUT): shutil.rmtree(OUT, onerror=_force_writable)
os.makedirs(OUT, exist_ok=True)
logo_src = os.path.join(HERE, "..", "premier-logo.svg")
if os.path.exists(logo_src):
    dst = os.path.join(OUT, "premier-logo.svg")
    shutil.copy(logo_src, dst)
    try: os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
    except Exception: pass

# Favicon (SVG, monogram on teal)
favicon = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" rx="14" fill="#0C2A2A"/>'
           '<text x="32" y="44" text-anchor="middle" font-family="Georgia,serif" font-size="36" font-weight="700" fill="#2FB8A3">P</text>'
           '</svg>')
open(os.path.join(OUT,"favicon.svg"),"w",encoding="utf-8").write(favicon)

# Open Graph image (1200x630 SVG)
og = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630">'
      '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
      '<stop offset="0%" stop-color="#0C2A2A"/><stop offset="100%" stop-color="#13524A"/></linearGradient></defs>'
      '<rect width="1200" height="630" fill="url(#g)"/>'
      '<rect x="0" y="0" width="6" height="630" fill="#F26A21"/>'
      f'<text x="80" y="180" font-family="Georgia,serif" fill="#2FB8A3" font-size="34" font-weight="700">{CO["name"].upper()}</text>'
      f'<text x="80" y="320" font-family="Georgia,serif" fill="#fff" font-size="86" font-weight="700">Used Injection</text>'
      '<text x="80" y="412" font-family="Georgia,serif" fill="#fff" font-size="86" font-weight="700" font-style="italic">Molding Machines.</text>'
      f'<text x="80" y="500" font-family="Helvetica,Arial,sans-serif" fill="#C9DAD6" font-size="28">{CO["city"]}, {CO["region"]} · {STATS.get("years_in_business",55)}+ years · Nationwide shipping</text>'
      f'<text x="80" y="555" font-family="Helvetica,Arial,sans-serif" fill="#9FBDB7" font-size="24">{CO["phone"]} · {CO["email"]}</text>'
      '</svg>')
open(os.path.join(OUT,"og.svg"),"w",encoding="utf-8").write(og)

A = avail()

def stats_strip():
    items = [
        (f'{STATS.get("years_in_business",55)}+', 'Years in plastics machinery'),
        (f'{len(A)}', STATS.get("machines_in_stock_label","live inventory")),
        (f'{STATS.get("states_shipped",48)}', 'States shipped to'),
        (STATS.get("tonnage_range","100 – 1,500 tons"), 'Tonnage range we handle'),
    ]
    cells = "".join(f'<div><span class="v">{v}</span><span class="k">{k}</span></div>' for v,k in items)
    return f'<section class="stats"><div class="wrap"><div class="row">{cells}</div></div></section>'

def cert_row():
    if not CERTS: return ""
    inner = "".join(f'<span class="cert">{c["name"]}<small>{c["full"]}</small></span>' for c in CERTS)
    return f'<div class="cert-row">{inner}</div>'

# ============================================================ INDEX
hero = (f'<section class="hero"><div class="wrap"><span class="pill">Used Injection Molding Machines</span>'
        f'<h1 class="serif">Inspected, ready to ship, <em>priced to move.</em></h1>'
        f'<p>{CO["name"]} is your nationwide source to <strong>buy and sell</strong> used injection molding machines &mdash; every unit inspected, documented, and backed by {STATS.get("years_in_business",55)}+ years in plastics machinery.</p>'
        f'<div class="entity">{CO["name"]} &middot; {CO["city"]}, {CO["region"]} &middot; Buying &amp; selling plastics machinery nationwide</div>'
        f'<div class="cta-row"><a class="btn btn-primary" href="inventory.html">Browse Inventory</a>'
        f'<a class="btn btn-ghost" href="sell.html">Sell Us Your Machine</a>'
        f'<a class="btn btn-ghost" href="tel:{CO["phone_e164"]}">Call {CO["phone"]}</a></div></div></section>')

feat = '<section id="inventory"><div class="wrap"><div class="sec-head"><span class="pill">Featured Inventory</span><h2 class="serif">In stock and inspected</h2><p>Every machine includes a documented condition report, true hours, and full specs.</p></div><div class="grid">' + "".join(card(m) for m in A[:6]) + '</div><div style="text-align:center;margin-top:34px"><a class="btn btn-ghost" href="inventory.html">View all '+str(len(A))+' machines &rarr;</a></div></div></section>'

twohalves = (
    '<section style="background:#F6F9F9"><div class="wrap"><div class="grid-2">'
    '<div class="svc"><span class="pill">Buyers</span>'
    '<h3 class="serif" style="margin-top:8px">Find the right machine — and trust the spec sheet.</h3>'
    '<p class="lede">Every machine on our floor has documented true hours, a written condition report, and a run-off video on request. Inspected machines carry a 30-day functional guarantee. If we wouldn\'t buy it ourselves, we don\'t list it.</p>'
    '<a class="btn btn-teal" href="inventory.html">Browse Inventory</a></div>'
    '<div class="svc"><span class="pill" style="color:#B23E0F;background:rgba(242,106,33,.12)">Sellers</span>'
    '<h3 class="serif" style="margin-top:8px">Have a machine — or a full plant — to sell?</h3>'
    '<p class="lede">Send photos and a tag plate, and we typically return a cash offer within 24 hours. We coordinate teardown, rigging, and freight so you don\'t lift a thing.</p>'
    '<a class="btn btn-primary" href="sell.html">Get a Cash Offer</a></div>'
    '</div></div></section>'
)

how = ('<section id="how"><div class="wrap"><div class="sec-head"><span class="pill">How It Works</span><h2 class="serif">From question to quote &mdash; in minutes</h2></div>'
       '<div class="grid"><div class="card" style="padding:22px;text-align:center">&#128269;<h3 style="margin-top:8px">You ask</h3><p class="lede">Call, text, or message about any machine — we answer 24/7.</p></div>'
       '<div class="card" style="padding:22px;text-align:center">&#129302;<h3 style="margin-top:8px">AI answers instantly</h3><p class="lede">Specs, photos, and availability on demand.</p></div>'
       '<div class="card" style="padding:22px;text-align:center">&#129309;<h3 style="margin-top:8px">We connect</h3><p class="lede">Full spec sheet texted and a call booked with Nicole.</p></div></div></div></section>')

trust = ('<section style="background:#F6F9F9"><div class="wrap"><div class="sec-head"><span class="pill">Why Premier</span>'
         '<h2 class="serif">Certified appraisals. Real condition reports. Honest deals.</h2>'
         '<p>We hold the industry credentials that lenders, insurers, and buyers ask for.</p></div>'
         + cert_row() + '</div></section>')

band = (f'<section class="band"><div class="wrap"><h2 class="serif">Looking for a machine &mdash; or selling one?</h2>'
        f'<p>Tell us what you need. We answer fast.</p>'
        f'<div class="cta-row"><a class="btn btn-primary" href="tel:{CO["phone_e164"]}">Call {CO["phone"]}</a>'
        f'<a class="btn btn-dark" href="contact.html">Send a Message</a></div></div></section>')

page("index.html", f'{CO["name"]} — Used Injection Molding Machines | {CO["city"]}, {CO["region"]}',
     f"Buy and sell inspected used injection molding machines. {CO['name']}, {CO['city']} {CO['region']} — {STATS.get('years_in_business',55)}+ years, certified appraisals, nationwide shipping.",
     hero + stats_strip() + feat + twohalves + how + trust + band, jsonld=org_ld())

# ============================================================ INVENTORY (ItemList)
itemlist = {"@context":"https://schema.org","@type":"ItemList","name":"Used Injection Molding Machines in Stock",
    "itemListElement":[{"@type":"ListItem","position":i+1,"url":CO["url"].rstrip("/")+"/"+murl(m),
        "name":f'{m["tonnage"]}-Ton {m["brand"]} {m["model"]}'} for i,m in enumerate(A)]}
invbody = ('<section><div class="wrap"><div class="bc"><a href="index.html">Home</a> / Inventory</div>'
           '<div class="sec-head"><span class="pill">Full Inventory</span><h2 class="serif">'+str(len(A))+' machines in stock</h2><p>Inspected, documented, ready to ship nationwide. Don\'t see what you need? <a href="contact.html" style="color:#1B8A7A;font-weight:700">Tell us what you\'re looking for &rarr;</a></p></div>'
           '<div class="grid">'+"".join(card(m) for m in A)+'</div></div></section>'
           + band)
page("inventory.html", f'Used Injection Molding Machines In Stock | {CO["name"]}',
     "Browse all used injection molding machines in stock at Premier Equipment, Beachwood OH. Van Dorn, Milacron, Nissei, Toshiba, Engel, Husky and more.",
     invbody, jsonld=itemlist)

# ============================================================ MACHINE PAGES
for m in A:
    prod_ld = {"@context":"https://schema.org","@type":"Product",
        "name":f'{m["tonnage"]}-Ton {m["brand"]} {m["model"]} Injection Molding Machine',
        "brand":{"@type":"Brand","name":m["brand"]},"model":m["model"],
        "category":"Used Injection Molding Machine","itemCondition":"https://schema.org/UsedCondition",
        "productionDate":str(m["year"]),"description":m["summary"],
        "additionalProperty":[
            {"@type":"PropertyValue","name":"Clamp Tonnage","value":f'{m["tonnage"]} tons'},
            {"@type":"PropertyValue","name":"Shot Size","value":m["shot_size"]},
            {"@type":"PropertyValue","name":"Controller","value":m["controller"]},
            {"@type":"PropertyValue","name":"Hours","value":str(m["hours"])},
            {"@type":"PropertyValue","name":"Condition","value":m["condition"]}],
        "offers":{"@type":"Offer","availability":"https://schema.org/InStock","priceCurrency":"USD",
            "url":CO["url"].rstrip("/")+"/"+murl(m),"seller":{"@type":"Organization","name":CO["name"]}}}
    specrows = "".join(f'<div><span class="k">{k}</span><span class="v">{v}</span></div>' for k,v in
        [("Brand",m["brand"]),("Model",m["model"]),("Tonnage",f'{m["tonnage"]} tons'),("Year",m["year"]),
         ("Shot size",m["shot_size"]),("Controller",m["controller"]),("Hours",f'{m["hours"]:,}'),
         ("Condition",m["condition"]),("Price","Request a quote")])
    vis_style = card_photo_style(m).replace('background-image:linear-gradient(180deg,rgba(12,42,42,0) 55%,rgba(12,42,42,.55))', 'background-image:linear-gradient(180deg,rgba(12,42,42,.05),rgba(12,42,42,.45))')
    vis_inner = '' if (m.get("photo") or "").strip() else f'{m["tonnage"]}T'
    body = ('<section><div class="wrap"><div class="bc"><a href="../index.html">Home</a> / <a href="../inventory.html">Inventory</a> / '
            f'{m["brand"]} {m["model"]}</div><div class="prod">'
            f'<div class="vis"{vis_style}>{vis_inner}</div><div>'
            f'<span class="pill">{m["condition"]} Condition</span>'
            f'<h1 class="serif" style="font-size:34px;margin:10px 0 4px">{m["tonnage"]}-Ton {m["brand"]} {m["model"]}</h1>'
            f'<p style="color:#52606B">{m["summary"]} Inspected, documented true hours, and backed by our 30-day functional guarantee.</p>'
            f'<div class="specs">{specrows}</div>'
            f'<div style="display:flex;gap:10px;flex-wrap:wrap"><a class="btn btn-primary" href="tel:{CO["phone_e164"]}">Call {CO["phone"]}</a>'
            f'<a class="btn btn-teal" href="../contact.html?machine={m["tonnage"]}-ton+{m["brand"]}+{m["model"]}">Request Specs</a></div>'
            '<div class="tile-info">'
            '<div class="ti"><h4>Condition Report</h4><p>Documented true hours, full inspection sheet, run-off video on request.</p></div>'
            '<div class="ti"><h4>30-Day Guarantee</h4><p>Functional guarantee on the items listed in the condition report.</p></div>'
            '<div class="ti"><h4>Rigging &amp; Freight</h4><p>We coordinate teardown and nationwide shipping so it arrives ready to set.</p></div>'
            '</div>'
            '</div></div></div></section>'
            # trade-in band
            '<section class="band"><div class="wrap"><h2 class="serif">Have a machine to trade in?</h2>'
            '<p>We buy machines too — single units or full plants. Send photos and the tag plate; we typically return a cash offer within 24 hours.</p>'
            '<div class="cta-row"><a class="btn btn-primary" href="../sell.html">Get a Cash Offer</a>'
            f'<a class="btn btn-dark" href="tel:{CO["phone_e164"]}">Call {CO["phone"]}</a></div></div></section>')
    page(murl(m), f'{m["tonnage"]}-Ton {m["brand"]} {m["model"]} — Used Injection Molding Machine | {CO["name"]}',
         f'{m["tonnage"]}-ton {m["brand"]} {m["model"]} used injection molding machine, {m["year"]}, {m["shot_size"]} shot, {m["controller"]} control, {m["condition"]} condition. Inspected, in stock at Premier Equipment, Beachwood OH.',
         body, jsonld=prod_ld, prefix="../")

# ============================================================ FAQ
faq_ld = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
    {"@type":"Question","name":f["q"],"acceptedAnswer":{"@type":"Answer","text":f["a"]}} for f in DATA["faqs"]]}
faqbody = ('<section><div class="wrap" style="max-width:820px"><div class="bc"><a href="index.html">Home</a> / FAQ</div>'
           '<div class="sec-head"><span class="pill">Buyer &amp; Seller FAQ</span><h2 class="serif">The questions people actually ask</h2></div>'
           + "".join(f'<details class="qa"><summary>{f["q"]}</summary><div class="ans">{f["a"]}</div></details>' for f in DATA["faqs"])
           + '</div></section>' + band)
page("faq.html", f'FAQ — Used Injection Molding Machines | {CO["name"]}',
     "Common questions about buying and selling used injection molding machines from Premier Equipment: inspection, rigging and freight, warranty, tonnage selection, financing, plant liquidations.",
     faqbody, jsonld=faq_ld)

# ============================================================ SELL
sell_ld = {"@context":"https://schema.org","@type":"Service","serviceType":"Used Plastics Machinery Buyer",
    "name":"We Buy Used Injection Molding Machines","provider":{"@type":"Organization","name":CO["name"],"url":CO["url"]},
    "areaServed":"US","description":"Premier Equipment buys single machines, lines, and full plants. Cash offers within 24 hours, rigging and freight handled."}
sellbody = (
    '<section style="background:linear-gradient(160deg,#0C2A2A,#13524A);color:#fff">'
    '<div class="wrap" style="padding:40px 24px 24px"><div class="bc" style="color:#9FBDB7">'
    '<a href="index.html" style="color:#9FBDB7">Home</a> / Sell Your Machine</div>'
    '<span class="pill" style="color:#fff;background:rgba(255,255,255,.15)">For Sellers</span>'
    '<h1 class="serif" style="font-size:42px;margin:10px 0 8px">Have a machine — or a full plant — to sell?</h1>'
    f'<p style="color:#C9DAD6;max-width:640px;font-size:17px">Send photos and a tag plate. We typically return a cash offer within 24 hours and handle teardown, rigging, and freight so you don\'t lift a thing. {STATS.get("years_in_business",55)}+ years in plastics machinery, shipped to {STATS.get("states_shipped",48)} states.</p>'
    '</div></section>'
    '<section><div class="wrap"><div class="grid-2">'
    '<div>'
    '<h2 class="serif" style="font-size:28px;margin-bottom:12px">How it works</h2>'
    '<div class="svc" style="margin-bottom:14px"><h3>1. Tell us what you have</h3><p class="lede">Use the form (or text photos to '+CO["phone"]+'). Tag plate, condition, and a few photos is plenty to start.</p></div>'
    '<div class="svc" style="margin-bottom:14px"><h3>2. Cash offer within 24 hours</h3><p class="lede">We base offers on real recent comps, not lowball guesses. If we need more info or a site visit, we say so up front.</p></div>'
    '<div class="svc" style="margin-bottom:14px"><h3>3. We handle the move</h3><p class="lede">Teardown, rigging, crating, freight — coordinated by Premier. You get paid on pickup.</p></div>'
    '<div class="svc"><h3>Plant liquidations &amp; lender sales</h3><p class="lede">Discreet, professional, USPAP-compliant valuations your bank or court will accept. We can re-market unsold machines through our buyer network.</p></div>'
    '</div>'
    '<div>'
    '<form id="sell-form" class="form">'
    '<h2 class="serif" style="font-size:24px;margin-bottom:6px">Get a cash offer</h2>'
    '<p class="lede" style="color:#52606B;font-size:14px;margin-bottom:10px">We reply within 1 business day.</p>'
    '<div class="row"><div><label>Your name</label><input name="name" required></div>'
    '<div><label>Company</label><input name="company"></div></div>'
    '<div class="row"><div><label>Phone</label><input name="phone" required></div>'
    '<div><label>Email</label><input name="email" type="email"></div></div>'
    '<div class="row"><div><label>Machine brand</label><input name="machine_brand" placeholder="e.g. Van Dorn"></div>'
    '<div><label>Tonnage</label><input name="machine_tonnage" placeholder="e.g. 300"></div></div>'
    '<div class="row"><div><label>Model</label><input name="machine_model"></div>'
    '<div><label>Year</label><input name="machine_year"></div></div>'
    '<label>Anything else? (hours, condition, # of machines, location)</label>'
    '<textarea name="message" rows="3" placeholder="Single machine in Akron, runs daily, around 18,000 hours…"></textarea>'
    '<div class="submit-row"><button type="submit" class="btn btn-primary">Send for cash offer</button>'
    f'<a class="btn btn-ghost" href="tel:{CO["phone_e164"]}">or call {CO["phone"]}</a></div>'
    '<div class="ok">Thanks — Nicole will reach out within 1 business day with next steps.</div>'
    '<div class="err">Something went wrong. Please call '+CO["phone"]+' or email '+CO["email"]+'.</div>'
    '</form>'
    '</div></div></div></section>' + band + FORM_JS
)
page("sell.html", f'Sell Your Used Injection Molding Machine — Cash Offers in 24 Hours | {CO["name"]}',
     f'Sell your used injection molding machine to {CO["name"]}, Beachwood OH. Cash offers within 24 hours. We handle rigging, freight, and plant liquidations nationwide.',
     sellbody, jsonld=sell_ld)

# ============================================================ SERVICES
services_ld = {"@context":"https://schema.org","@graph":[
    {"@type":"Service","name":s["name"],"description":s["lede"],
     "provider":{"@type":"Organization","name":CO["name"],"url":CO["url"]},"areaServed":"US"} for s in SERVICES]}
svc_cards = "".join(
    f'<div id="{s["id"]}" class="svc"><span class="pill">Service</span>'
    f'<h3 class="serif" style="margin-top:8px">{s["name"]}</h3>'
    f'<p class="lede">{s["lede"]}</p>'
    f'<ul>{"".join(f"<li>{b}</li>" for b in s["bullets"])}</ul></div>'
    for s in SERVICES)
svcbody = ('<section><div class="wrap"><div class="bc"><a href="index.html">Home</a> / Services</div>'
           '<div class="sec-head"><span class="pill">What We Do</span>'
           '<h2 class="serif">Buy, sell, appraise, and move plastics machinery — under one roof.</h2>'
           '<p>From a single press to a full plant liquidation, we run the whole job: valuation, paperwork, rigging, and freight.</p></div>'
           + cert_row()
           + '<div style="height:30px"></div>'
           + '<div class="grid-2" style="gap:18px">' + svc_cards + '</div></div></section>'
           + band)
page("services.html", f'Services — Appraisals, Rigging &amp; Freight | {CO["name"]}',
     f'Premier Equipment\'s services: buying used injection molding machines, selling inspected inventory, certified CMEA/USPAP appraisals, and nationwide rigging and freight.',
     svcbody, jsonld=services_ld)

# ============================================================ ABOUT
about_ld = org_ld()
about_ld["@type"] = ["Organization","LocalBusiness","AboutPage"]
aboutbody = (
    '<section style="background:linear-gradient(160deg,#0C2A2A,#13524A);color:#fff">'
    '<div class="wrap" style="padding:48px 24px"><div class="bc" style="color:#9FBDB7">'
    '<a href="index.html" style="color:#9FBDB7">Home</a> / About</div>'
    '<span class="pill" style="color:#fff;background:rgba(255,255,255,.15)">About Premier</span>'
    f'<h1 class="serif" style="font-size:42px;margin:10px 0 8px">{STATS.get("years_in_business",55)}+ years buying, selling, and moving the machines plastics runs on.</h1>'
    f'<p style="color:#C9DAD6;max-width:640px;font-size:17px">{CO["name"]} is a family-built dealer of used injection molding machines based in {CO["city"]}, {CO["region"]}. We buy single machines and full plants, sell inspected inventory nationwide, and provide certified appraisals lenders, insurers, and courts accept.</p>'
    '</div></section>'
    + stats_strip() +
    '<section><div class="wrap"><div class="grid-2" style="align-items:start">'
    '<div>'
    '<span class="pill">Owner</span>'
    f'<h2 class="serif" style="font-size:30px;margin:10px 0 8px">Nicole Haas, Owner</h2>'
    '<p style="color:#52606B;font-size:16px;margin-bottom:14px">Nicole leads Premier Equipment and personally signs off on every inspection. She brings the same standard to a single 150-ton sale that she brings to a full plant liquidation: documented condition, honest pricing, and zero surprises on delivery day.</p>'
    f'<p style="color:#52606B;font-size:16px;margin-bottom:14px">Buyers and sellers reach her directly at <a href="tel:{CO["phone_e164"]}" style="color:#1B8A7A;font-weight:700">{CO["phone"]}</a> or <a href="mailto:{CO["email"]}" style="color:#1B8A7A;font-weight:700">{CO["email"]}</a>.</p>'
    + (f'<a class="btn btn-teal" href="{CO["owner_linkedin"]}" target="_blank" rel="noopener">Connect on LinkedIn</a>' if CO.get("owner_linkedin") else '') +
    '</div>'
    '<div>'
    '<div class="svc"><h3 class="serif" style="font-size:22px">What we stand for</h3>'
    '<ul>'
    '<li><strong>Documented condition.</strong> True hours, written report, run-off video on request.</li>'
    '<li><strong>Honest deals.</strong> We\'d rather lose a sale than ship a surprise.</li>'
    '<li><strong>One number, one team.</strong> Quoting, rigging, freight, paperwork — all handled in-house.</li>'
    '<li><strong>Credentials lenders trust.</strong> CMEA · USPAP-compliant appraisals.</li>'
    '</ul></div>'
    '</div>'
    '</div></div></section>' + band)
page("about.html", f'About {CO["name"]} — Used Injection Molding Machine Dealer in {CO["city"]}, {CO["region"]}',
     f'{CO["name"]} is a {STATS.get("years_in_business",55)}+ year dealer of used injection molding machines in {CO["city"]}, {CO["region"]}. Owned by Nicole Haas. Certified CMEA/USPAP appraisals; nationwide rigging and freight.',
     aboutbody, jsonld=about_ld)

# ============================================================ CONTACT
contact_ld = {"@context":"https://schema.org","@type":"ContactPage","name":f'Contact {CO["name"]}',
    "url":CO["url"].rstrip("/")+"/contact.html",
    "mainEntity":{"@type":"Organization","name":CO["name"],"telephone":CO["phone_e164"],"email":CO["email"],
        "address":{"@type":"PostalAddress","addressLocality":CO["city"],"addressRegion":CO["region"],"postalCode":CO["postal"],"addressCountry":"US"}}}
contactbody = (
    '<section><div class="wrap"><div class="bc"><a href="index.html">Home</a> / Contact</div>'
    '<div class="sec-head"><span class="pill">Contact</span>'
    '<h2 class="serif">Tell us what you need. We answer fast.</h2>'
    '<p>Buying, selling, appraisals, or just kicking tires — every message gets a reply within 1 business day.</p></div>'
    '<div class="grid-2">'
    '<div>'
    '<div class="svc" style="margin-bottom:14px"><h3 class="serif" style="font-size:20px">Call or text</h3>'
    f'<p class="lede" style="font-size:16px"><a href="tel:{CO["phone_e164"]}" style="color:#1B8A7A;font-weight:700">{CO["phone"]}</a></p></div>'
    '<div class="svc" style="margin-bottom:14px"><h3 class="serif" style="font-size:20px">Email</h3>'
    f'<p class="lede" style="font-size:16px"><a href="mailto:{CO["email"]}" style="color:#1B8A7A;font-weight:700">{CO["email"]}</a></p></div>'
    '<div class="svc"><h3 class="serif" style="font-size:20px">Office</h3>'
    f'<p class="lede" style="font-size:16px">{CO["city"]}, {CO["region"]} {CO["postal"]}<br>Serving all 50 states</p></div>'
    '</div>'
    '<div>'
    '<form id="contact-form" class="form">'
    '<h2 class="serif" style="font-size:24px;margin-bottom:6px">Send a message</h2>'
    '<p class="lede" style="color:#52606B;font-size:14px;margin-bottom:10px">Pre-filled if you came from a machine page.</p>'
    '<div class="row"><div><label>Your name</label><input name="name" required></div>'
    '<div><label>Company</label><input name="company"></div></div>'
    '<div class="row"><div><label>Phone</label><input name="phone" required></div>'
    '<div><label>Email</label><input name="email" type="email"></div></div>'
    '<label>Which machine or service?</label>'
    '<input name="machine" id="contact-machine" placeholder="e.g. 300-Ton Van Dorn">'
    '<label>How can we help?</label>'
    '<textarea name="message" rows="4" placeholder="Looking for 300–500 ton hydraulic, mid-2010s, for a PP part…"></textarea>'
    '<div class="submit-row"><button type="submit" class="btn btn-primary">Send Message</button>'
    f'<a class="btn btn-ghost" href="tel:{CO["phone_e164"]}">or call {CO["phone"]}</a></div>'
    '<div class="ok">Thanks — Nicole will reach out within 1 business day.</div>'
    '<div class="err">Something went wrong. Please call '+CO["phone"]+' or email '+CO["email"]+'.</div>'
    '</form>'
    '<script>(function(){var q=new URLSearchParams(location.search).get(\'machine\');if(q){var el=document.getElementById(\'contact-machine\');if(el)el.value=q;}})();</script>'
    '</div>'
    '</div></div></section>' + band + FORM_JS)
page("contact.html", f'Contact {CO["name"]} — {CO["phone"]} | {CO["city"]}, {CO["region"]}',
     f'Contact {CO["name"]} in {CO["city"]}, {CO["region"]} for used injection molding machines, appraisals, or rigging and freight. Call {CO["phone"]} or send a message — replies within 1 business day.',
     contactbody, jsonld=contact_ld)

# ============================================================ SEO/GEO files
base = CO["url"].rstrip("/")
urls = ["index.html","inventory.html","sell.html","services.html","about.html","faq.html","contact.html"] + [murl(m) for m in A]
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
    "".join(f'  <url><loc>{base}/{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls) + '</urlset>\n'
open(os.path.join(OUT,"sitemap.xml"),"w").write(sitemap)
open(os.path.join(OUT,"robots.txt"),"w").write(
    "User-agent: *\nAllow: /\n"
    "User-agent: GPTBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\n"
    "User-agent: Google-Extended\nAllow: /\n\n"
    f"Sitemap: {base}/sitemap.xml\n")
llms = (f"# {CO['name']}\n\n> {CO['entity_line']}\n\n"
        f"{CO['name']} buys and sells inspected used injection molding machines from {CO['city']}, {CO['region']}. "
        f"Owner: {CO.get('owner_name','Nicole Haas')}. "
        f"{STATS.get('years_in_business',55)}+ years in plastics machinery. Shipped to {STATS.get('states_shipped',48)} states. "
        "Certified appraisals (CMEA/USPAP/NEBB), documented condition reports, nationwide rigging and freight.\n\n"
        "## What we do\n" + "".join(f"- **{s['name']}** — {s['lede']}\n" for s in SERVICES) +
        "\n## Inventory\n" + "".join(f"- [{m['tonnage']}-Ton {m['brand']} {m['model']}]({base}/{murl(m)}): {m['summary']}\n" for m in A) +
        f"\n## Key pages\n"
        f"- [All Inventory]({base}/inventory.html)\n"
        f"- [Sell Your Machine]({base}/sell.html) — cash offers within 24 hours\n"
        f"- [Services]({base}/services.html) — appraisals, rigging, freight\n"
        f"- [About]({base}/about.html)\n"
        f"- [Buyer &amp; Seller FAQ]({base}/faq.html)\n"
        f"- [Contact]({base}/contact.html)\n"
        f"\n## Contact\n{CO['phone']} · {CO['email']} · {CO['city']}, {CO['region']} {CO['postal']}\n")
open(os.path.join(OUT,"llms.txt"),"w",encoding="utf-8").write(llms)

# ============================================================ STATIC ASSETS
# Anything under ./static/ is copied verbatim into ./site/.
# This is where hand-written pages live (quote.html, admin/*) so they survive
# the rebuild — build.py wipes site/ on every run.
STATIC = os.path.join(HERE, "static")
if os.path.isdir(STATIC):
    for root, dirs, files in os.walk(STATIC):
        rel = os.path.relpath(root, STATIC)
        dest = OUT if rel == "." else os.path.join(OUT, rel)
        os.makedirs(dest, exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(root, f), os.path.join(dest, f))

print(f"Built {len(urls)} pages + sitemap/robots/llms/favicon/og into {OUT}")
print("Pages:", ", ".join(urls))
if os.path.isdir(STATIC):
    print(f"Copied static/* (quote.html, admin/*) into {OUT}")
