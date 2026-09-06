#!/usr/bin/env python3
"""
GEO Report Premium Beautifier
La Crown Inc. — lacrown.ai/geo-upward

Usage:
    python beautifier.py <data.json> [--output report.pdf] [--client-logo logo.png]

Input: JSON file structured per the GEO_DATA_SCHEMA in SKILL.md
Output: Premium dark-themed PDF matching La Crown brand standards
"""

import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime


# ─── BRAND CONFIG ────────────────────────────────────────────────────────────
# Edit these to change branding. Primary brand = La Crown defaults.
BRAND = {
    "name": "La Crown Inc.",
    "tagline": "AI-Powered Growth",
    "website": "lacrown.ai/geo-upward",
    "phone": "260-782-8390",
    "contact_name": "Millisa Nwokolo",
    "colors": {
        "primary":             "#FFC72C",   # bright yellow-gold — headers, accents
        "primary_bright":      "#FFD75E",   # hover/highlight variant
        "secondary":           "#E94560",   # coral red — score gauges, CTAs
        "bg_deep":             "#0A0A0F",   # deepest background
        "bg_dark":             "#111118",   # page background
        "bg_card":             "#1A1A28",   # card backgrounds
        "bg_card_alt":         "#141420",   # alternate card
        "border":              "#2A2A3A",   # subtle borders
        "text_primary":        "#F0EDE8",   # main body text
        "text_secondary":      "#A09898",   # muted text
        "text_accent":         "#FFC72C",   # gold text highlights
        "critical":            "#E74C3C",   # critical severity
        "high":                "#E67E22",   # high severity
        "medium":              "#F39C12",   # medium severity
        "low":                 "#3498DB",   # low severity
        "score_excellent":     "#2ECC71",   # 85–100
        "score_good":          "#3498DB",   # 70–84
        "score_moderate":      "#F39C12",   # 55–69
        "score_below":         "#E67E22",   # 40–54
        "score_critical":      "#E74C3C",   # 0–39
    }
}


def apply_brand_config(config_path):
    """Deep-merge an external brand.json over the BRAND defaults so resellers can
    white-label the report (name, tagline, website, phone, contact_name, cover_tag,
    and any subset of colors) without editing this file. Any key the config omits
    keeps its La Crown default — so a customer can override just two colors if they want."""
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    for key, value in cfg.items():
        if key == "colors" and isinstance(value, dict):
            BRAND["colors"].update(value)          # merge color overrides, keep the rest
        else:
            BRAND[key] = value                     # name, tagline, website, phone, etc.
    print(f"  Brand: {BRAND['name']} (white-labeled via {os.path.basename(config_path)})")


def score_color(score):
    c = BRAND["colors"]
    if score >= 85: return c["score_excellent"]
    if score >= 70: return c["score_good"]
    if score >= 55: return c["score_moderate"]
    if score >= 40: return c["score_below"]
    return c["score_critical"]


def score_label(score):
    if score >= 85: return "EXCELLENT"
    if score >= 70: return "GOOD"
    if score >= 55: return "MODERATE"
    if score >= 40: return "DEVELOPING"
    return "CRITICAL"


def severity_color(severity):
    c = BRAND["colors"]
    s = severity.upper()
    if s == "CRITICAL": return c["critical"]
    if s == "HIGH":     return c["high"]
    if s == "MEDIUM":   return c["medium"]
    return c["low"]


def gauge_svg(score, size=160):
    """Generate an SVG arc gauge for the score."""
    color = score_color(score)
    cx, cy, r = size // 2, size // 2, (size // 2) - 14
    circ = 2 * 3.14159 * r
    # 75% arc (270 degrees), score fills proportionally
    arc_len = circ * 0.75
    filled = arc_len * (score / 100)
    gap = circ - arc_len
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="#2A2A3A" stroke-width="10"
        stroke-dasharray="{arc_len:.1f} {gap:.1f}"
        stroke-dashoffset="{-gap/2 - circ*0.125:.1f}"
        stroke-linecap="round"/>
      <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="{color}" stroke-width="10"
        stroke-dasharray="{filled:.1f} {circ - filled:.1f}"
        stroke-dashoffset="{-gap/2 - circ*0.125:.1f}"
        stroke-linecap="round"/>
      <text x="{cx}" y="{cy - 6}" text-anchor="middle"
        font-family="'DM Serif Display', Georgia, serif"
        font-size="{size // 4}" fill="{color}" font-weight="bold">{score}</text>
      <text x="{cx}" y="{cy + 14}" text-anchor="middle"
        font-family="Outfit, sans-serif" font-size="11"
        fill="#A09898" letter-spacing="1">of 100</text>
    </svg>"""


def mini_gauge_svg(score, size=72):
    """Smaller gauge for dimension breakdown cards."""
    color = score_color(score)
    cx, cy, r = size // 2, size // 2, (size // 2) - 8
    circ = 2 * 3.14159 * r
    arc_len = circ * 0.75
    filled = arc_len * (score / 100)
    gap = circ - arc_len
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="#2A2A3A" stroke-width="6"
        stroke-dasharray="{arc_len:.1f} {gap:.1f}"
        stroke-dashoffset="{-gap/2 - circ*0.125:.1f}"
        stroke-linecap="round"/>
      <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="{color}" stroke-width="6"
        stroke-dasharray="{filled:.1f} {circ - filled:.1f}"
        stroke-dashoffset="{-gap/2 - circ*0.125:.1f}"
        stroke-linecap="round"/>
      <text x="{cx}" y="{cy + 5}" text-anchor="middle"
        font-family="Outfit, sans-serif"
        font-size="13" fill="{color}" font-weight="bold">{score}</text>
    </svg>"""


def bar_chart_svg(dimensions, width=520, height=140):
    """Horizontal bar chart for score breakdown."""
    colors = BRAND["colors"]
    bars = ""
    label_w = 180
    bar_area = width - label_w - 60
    row_h = height // len(dimensions)

    for i, dim in enumerate(dimensions):
        y = i * row_h + 4
        score = dim.get("score", 0)
        bar_w = int(bar_area * score / 100)
        col = score_color(score)
        bars += f"""
        <text x="0" y="{y + row_h//2 + 4}" font-family="Outfit, sans-serif"
          font-size="10" fill="#A09898">{dim['name'][:26]}</text>
        <rect x="{label_w}" y="{y + 4}" width="{bar_w}" height="{row_h - 10}"
          fill="{col}" rx="3" opacity="0.85"/>
        <text x="{label_w + bar_w + 6}" y="{y + row_h//2 + 4}"
          font-family="Outfit, sans-serif" font-size="10" fill="{col}"
          font-weight="bold">{score}</text>"""

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
      {bars}
    </svg>"""


def platform_badge(name, score):
    col = score_color(score)
    label = score_label(score)
    return f"""
    <div class="platform-badge">
      <div class="platform-score" style="color:{col}">{score}</div>
      <div class="platform-name">{name}</div>
      <div class="platform-label" style="color:{col}">{label}</div>
    </div>"""


def finding_card(finding):
    sev = finding.get("severity", "LOW").upper()
    col = severity_color(sev)
    title = finding.get("title", "")
    body = finding.get("description", "")
    return f"""
    <div class="finding-card" style="border-left-color:{col}">
      <div class="finding-header">
        <span class="severity-badge" style="background:{col}20;color:{col};border:1px solid {col}40">{sev}</span>
        <span class="finding-title">{title}</span>
      </div>
      <p class="finding-body">{body}</p>
    </div>"""


def action_item(num, item, timeframe_color):
    title = item.get("title", "")
    desc = item.get("description", "")
    time_est = item.get("time_estimate", "")
    time_html = f'<span class="action-time">{time_est}</span>' if time_est else ""
    return f"""
    <div class="action-item">
      <div class="action-num" style="background:{timeframe_color}20;color:{timeframe_color};border:1px solid {timeframe_color}40">{num}</div>
      <div class="action-content">
        <div class="action-title">{title}{time_html}</div>
        <div class="action-desc">{desc}</div>
      </div>
    </div>"""


def crawler_row(crawler):
    status = crawler.get("status", "Unknown")
    status_color = "#2ECC71" if "Allowed" in status else ("#E67E22" if "Delay" in status else "#E74C3C")
    dot = f'<span style="color:{status_color}">●</span>'
    return f"""
    <tr>
      <td>{crawler.get('name','')}</td>
      <td style="color:#A09898">{crawler.get('platform','')}</td>
      <td>{dot} {status}</td>
      <td style="color:#A09898;font-size:11px">{crawler.get('recommendation','')}</td>
    </tr>"""


def generate_html(data: dict, logo_path: str = None) -> str:
    c = BRAND["colors"]
    b = BRAND

    # ── Pull data ────────────────────────────────────────────────────────────
    company     = data.get("company_name", "")
    url         = data.get("url", "")
    audit_date  = data.get("audit_date", datetime.now().strftime("%B %d, %Y"))
    overall     = data.get("overall_score", 0)
    tagline     = data.get("company_tagline", "")   # e.g. "38 Years · $1B+ Transactions"
    stats       = data.get("stats", [])             # list of {"label": "...", "value": "..."}
    summary     = data.get("executive_summary", "")
    dimensions  = data.get("dimensions", [])
    platforms   = data.get("platforms", [])
    crawlers    = data.get("crawlers", [])
    findings    = data.get("findings", [])
    quick_wins  = data.get("action_plan", {}).get("quick_wins", [])
    medium_term = data.get("action_plan", {}).get("medium_term", [])
    strategic   = data.get("action_plan", {}).get("strategic", [])
    methodology = data.get("methodology", "")

    overall_color = score_color(overall)
    overall_label = score_label(overall)

    # ── Logo HTML ────────────────────────────────────────────────────────────
    if logo_path and os.path.exists(logo_path):
        import base64
        ext = Path(logo_path).suffix.lower().replace(".", "")
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/{ext};base64,{logo_b64}" class="client-logo" alt="{company} logo">'
    else:
        logo_html = f'<div class="logo-text">{company}</div>'

    # ── Stats badges ─────────────────────────────────────────────────────────
    stats_html = ""
    for s in stats:
        stats_html += f'<div class="stat-badge"><span class="stat-val">{s["value"]}</span><span class="stat-lbl">{s["label"]}</span></div>'

    # ── Gauge ────────────────────────────────────────────────────────────────
    gauge_html = gauge_svg(overall, 180)

    # ── Score breakdown ──────────────────────────────────────────────────────
    dim_cards_html = ""
    for dim in dimensions:
        mg = mini_gauge_svg(dim.get("score", 0), 68)
        wt = dim.get("weight", "")
        ws = dim.get("weighted_score", "")
        ws_html = f'<div class="dim-weighted">{ws} pts</div>' if ws else ""
        dim_cards_html += f"""
        <div class="dim-card">
          <div class="dim-gauge">{mg}</div>
          <div class="dim-info">
            <div class="dim-name">{dim.get('name','')}</div>
            <div class="dim-sub">{dim.get('description','')}</div>
            <div class="dim-meta">{wt} weight {ws_html}</div>
          </div>
        </div>"""

    chart_html = bar_chart_svg(dimensions) if dimensions else ""

    # ── Platforms ────────────────────────────────────────────────────────────
    platforms_html = "".join(platform_badge(p.get("name",""), p.get("score",0)) for p in platforms)

    # ── Crawlers ─────────────────────────────────────────────────────────────
    crawler_rows_html = "".join(crawler_row(cr) for cr in crawlers)

    # ── Findings ─────────────────────────────────────────────────────────────
    findings_html = "".join(finding_card(f) for f in findings)
    finding_counts = {
        "CRITICAL": sum(1 for f in findings if f.get("severity","").upper()=="CRITICAL"),
        "HIGH":     sum(1 for f in findings if f.get("severity","").upper()=="HIGH"),
        "MEDIUM":   sum(1 for f in findings if f.get("severity","").upper()=="MEDIUM"),
        "LOW":      sum(1 for f in findings if f.get("severity","").upper()=="LOW"),
    }
    finding_summary = " · ".join(
        f'<span style="color:{severity_color(k)}">{v} {k}</span>'
        for k, v in finding_counts.items() if v > 0
    )

    # ── Action plan ──────────────────────────────────────────────────────────
    qw_html  = "".join(action_item(i+1, it, c["secondary"]) for i, it in enumerate(quick_wins))
    mt_html  = "".join(action_item(i+1, it, c["primary"]) for i, it in enumerate(medium_term))
    str_html = "".join(action_item(i+1, it, "#9B59B6") for i, it in enumerate(strategic))

    # ── La Crown logo SVG ────────────────────────────────────────────────────
    lacrown_svg = f"""
    <svg width="120" height="28" viewBox="0 0 120 28" fill="none">
      <text x="0" y="20" font-family="'DM Serif Display', Georgia, serif"
        font-size="16" fill="{c['primary']}" letter-spacing="2">LA CROWN</text>
    </svg>"""

    # ─────────────────────────────────────────────────────────────────────────
    # HTML TEMPLATE
    # ─────────────────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GEO Report — {company}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --gold:    {c['primary']};
    --coral:   {c['secondary']};
    --bg-deep: {c['bg_deep']};
    --bg:      {c['bg_dark']};
    --card:    {c['bg_card']};
    --card2:   {c['bg_card_alt']};
    --border:  {c['border']};
    --text:    {c['text_primary']};
    --muted:   {c['text_secondary']};
  }}

  html {{ font-size: 13px; }}
  body {{
    font-family: 'Outfit', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }}

  /* ── PAGE LAYOUT ─────────────────────────────────────── */
  .page {{ width: 794px; margin: 0 auto; }}

  /* ── COVER PAGE ─────────────────────────────────────── */
  .cover {{
    min-height: 1123px;
    background: linear-gradient(160deg, #0D0D18 0%, #0A0A12 50%, #100A18 100%);
    display: flex; flex-direction: column;
    padding: 0;
    position: relative;
    overflow: hidden;
    page-break-after: always;
  }}
  .cover-noise {{
    position: absolute; inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
  }}
  .cover-line {{
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, {c['primary']}, {c['secondary']}, transparent);
  }}
  .cover-header {{
    padding: 36px 52px 0;
    display: flex; justify-content: space-between; align-items: center;
    position: relative; z-index: 2;
  }}
  .cover-brand {{ display: flex; flex-direction: column; gap: 2px; }}
  .cover-brand-name {{
    font-family: 'DM Serif Display', serif;
    font-size: 13px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--gold);
  }}
  .cover-brand-tag {{
    font-size: 10px; letter-spacing: 1px; color: var(--muted);
    text-transform: uppercase;
  }}
  .cover-confidential {{
    font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted); border: 1px solid var(--border); padding: 4px 10px; border-radius: 2px;
  }}
  .cover-divider {{
    margin: 32px 52px;
    height: 1px;
    background: linear-gradient(90deg, var(--gold), transparent);
    position: relative; z-index: 2;
  }}
  .cover-body {{
    flex: 1; display: flex; flex-direction: column;
    padding: 0 52px;
    position: relative; z-index: 2;
  }}
  .cover-eyebrow {{
    font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 14px;
  }}
  .cover-title {{
    font-family: 'DM Serif Display', serif;
    font-size: 52px; line-height: 1.08;
    color: var(--text); margin-bottom: 6px;
  }}
  .cover-title em {{ color: var(--gold); font-style: normal; }}
  .cover-url {{
    font-size: 13px; color: var(--muted); letter-spacing: 1px;
    margin-bottom: 40px;
  }}
  .cover-logo-block {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px 28px;
    display: inline-flex; align-items: center; gap: 20px;
    margin-bottom: 36px; align-self: flex-start;
  }}
  .client-logo {{ max-height: 52px; max-width: 200px; object-fit: contain; }}
  .logo-text {{
    font-family: 'DM Serif Display', serif;
    font-size: 22px; color: var(--text);
  }}
  .cover-logo-meta {{ display: flex; flex-direction: column; gap: 4px; }}
  .cover-logo-meta span {{ font-size: 11px; color: var(--muted); }}

  .cover-stats {{
    display: flex; gap: 16px; flex-wrap: wrap;
    margin-bottom: 36px;
  }}
  .stat-badge {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 16px;
    display: flex; flex-direction: column; align-items: center; gap: 2px;
  }}
  .stat-val {{
    font-family: 'DM Serif Display', serif;
    font-size: 18px; color: var(--gold); font-weight: bold;
  }}
  .stat-lbl {{ font-size: 9px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }}

  .cover-score-row {{
    display: flex; align-items: center; gap: 32px; margin-top: auto; padding-bottom: 40px;
  }}
  .cover-score-gauge {{ flex-shrink: 0; }}
  .cover-score-text {{ flex: 1; }}
  .cover-score-label {{
    font-size: 10px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 6px;
  }}
  .cover-score-value {{
    font-family: 'DM Serif Display', serif;
    font-size: 36px; color: {overall_color}; margin-bottom: 4px;
  }}
  .cover-score-verdict {{
    font-size: 12px; color: var(--muted); line-height: 1.5;
    max-width: 340px;
  }}
  .cover-footer {{
    padding: 20px 52px;
    border-top: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center;
    position: relative; z-index: 2;
  }}
  .cover-footer-left {{ display: flex; flex-direction: column; gap: 2px; }}
  .cover-footer-name {{ font-size: 11px; color: var(--text); font-weight: 500; }}
  .cover-footer-contact {{ font-size: 10px; color: var(--muted); }}
  .cover-footer-date {{ font-size: 10px; color: var(--muted); }}

  /* ── CONTENT PAGES ───────────────────────────────────── */
  .content-page {{
    padding: 48px 52px;
    min-height: 1123px;
    page-break-after: always;
    position: relative;
  }}
  .content-page::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--gold) 0%, transparent 60%);
  }}
  .page-label {{
    font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 8px;
  }}
  .section-title {{
    font-family: 'DM Serif Display', serif;
    font-size: 32px; color: var(--text); margin-bottom: 6px;
  }}
  .section-title em {{ color: var(--gold); font-style: normal; }}
  .section-sub {{
    font-size: 12px; color: var(--muted); margin-bottom: 28px; line-height: 1.5;
  }}
  .section-divider {{
    height: 1px; background: var(--border); margin: 28px 0;
  }}

  /* ── EXECUTIVE SUMMARY ───────────────────────────────── */
  .exec-summary {{
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--gold);
    border-radius: 8px;
    padding: 24px 28px;
    font-size: 13px; line-height: 1.75; color: var(--text);
    margin-bottom: 28px;
  }}
  .exec-summary strong {{ color: var(--gold); }}

  /* ── SCORE BREAKDOWN ─────────────────────────────────── */
  .dim-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 28px; }}
  .dim-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; padding: 14px 16px;
    display: flex; align-items: center; gap: 14px;
  }}
  .dim-gauge {{ flex-shrink: 0; }}
  .dim-info {{ flex: 1; }}
  .dim-name {{ font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 2px; }}
  .dim-sub {{ font-size: 10px; color: var(--muted); margin-bottom: 4px; line-height: 1.4; }}
  .dim-meta {{ font-size: 10px; color: var(--muted); display: flex; align-items: center; gap: 8px; }}
  .dim-weighted {{ font-size: 10px; color: var(--gold); }}
  .chart-wrap {{ margin-top: 16px; }}

  /* ── OVERALL SCORE SUMMARY ROW ───────────────────────── */
  .overall-row {{
    background: var(--card2); border: 1px solid {overall_color}40;
    border-radius: 8px; padding: 16px 24px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 20px;
  }}
  .overall-row-label {{ font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); }}
  .overall-row-score {{ font-family: 'DM Serif Display', serif; font-size: 32px; color: {overall_color}; }}
  .overall-row-verdict {{
    font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
    color: {overall_color}; padding: 4px 12px;
    background: {overall_color}18; border: 1px solid {overall_color}40; border-radius: 4px;
  }}

  /* ── PLATFORM READINESS ──────────────────────────────── */
  .platform-grid {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }}
  .platform-badge {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 20px;
    text-align: center; flex: 1; min-width: 120px;
  }}
  .platform-score {{
    font-family: 'DM Serif Display', serif;
    font-size: 28px; font-weight: bold; margin-bottom: 4px;
  }}
  .platform-name {{ font-size: 10px; color: var(--muted); margin-bottom: 4px; }}
  .platform-label {{
    font-size: 9px; letter-spacing: 1px; text-transform: uppercase; font-weight: 600;
  }}

  /* ── CRAWLER TABLE ───────────────────────────────────── */
  .crawler-table {{
    width: 100%; border-collapse: collapse; font-size: 11px;
  }}
  .crawler-table th {{
    background: var(--card2); color: var(--muted);
    font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
    padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border);
  }}
  .crawler-table td {{
    padding: 8px 12px; border-bottom: 1px solid {c['border']}88; color: var(--text);
  }}
  .crawler-table tr:last-child td {{ border-bottom: none; }}

  /* ── FINDINGS ────────────────────────────────────────── */
  .finding-summary {{
    font-size: 11px; color: var(--muted); margin-bottom: 16px;
  }}
  .finding-card {{
    border-left: 3px solid;
    background: var(--card); border-top: 1px solid var(--border);
    border-right: 1px solid var(--border); border-bottom: 1px solid var(--border);
    border-radius: 0 6px 6px 0;
    padding: 14px 16px; margin-bottom: 10px;
  }}
  .finding-header {{
    display: flex; align-items: center; gap: 10px; margin-bottom: 6px;
  }}
  .severity-badge {{
    font-size: 9px; letter-spacing: 1.5px; font-weight: 700;
    padding: 2px 8px; border-radius: 3px; text-transform: uppercase; flex-shrink: 0;
  }}
  .finding-title {{ font-size: 12px; font-weight: 600; color: var(--text); }}
  .finding-body {{ font-size: 11px; color: var(--muted); line-height: 1.6; }}

  /* ── ACTION PLAN ─────────────────────────────────────── */
  .action-tier {{
    margin-bottom: 28px;
  }}
  .tier-header {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 12px;
  }}
  .tier-label {{
    font-size: 9px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted);
  }}
  .tier-badge {{
    font-size: 9px; letter-spacing: 1px; text-transform: uppercase; font-weight: 600;
    padding: 3px 12px; border-radius: 3px;
  }}
  .action-item {{
    display: flex; gap: 14px; align-items: flex-start;
    padding: 12px 14px; background: var(--card); border: 1px solid var(--border);
    border-radius: 7px; margin-bottom: 8px;
  }}
  .action-num {{
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; flex-shrink: 0;
  }}
  .action-content {{ flex: 1; }}
  .action-title {{
    font-size: 12px; font-weight: 600; color: var(--text);
    margin-bottom: 3px; display: flex; align-items: center; gap: 10px;
  }}
  .action-time {{
    font-size: 9px; color: var(--muted); background: var(--card2);
    border: 1px solid var(--border); padding: 1px 7px; border-radius: 3px;
    font-weight: 400;
  }}
  .action-desc {{ font-size: 11px; color: var(--muted); line-height: 1.5; }}

  /* ── APPENDIX ────────────────────────────────────────── */
  .methodology-text {{
    font-size: 12px; color: var(--muted); line-height: 1.75;
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; padding: 20px 24px;
    margin-bottom: 20px;
  }}
  .glossary-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
  .glossary-item {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 6px; padding: 10px 14px;
  }}
  .glossary-term {{ font-size: 11px; font-weight: 600; color: var(--gold); margin-bottom: 2px; }}
  .glossary-def {{ font-size: 10px; color: var(--muted); line-height: 1.4; }}

  /* ── FOOTER ──────────────────────────────────────────── */
  .page-footer {{
    position: absolute; bottom: 24px; left: 52px; right: 52px;
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid var(--border); padding-top: 12px;
    font-size: 9px; color: var(--muted); letter-spacing: 1px;
  }}
  .footer-brand {{ color: var(--gold); font-weight: 600; }}

  @media print {{
    body {{ background: var(--bg); }}
    .cover, .content-page {{ page-break-after: always; }}
  }}
</style>
</head>
<body>
<div class="page">

<!-- ══════════════════════════════════════════════════════════════════════════
     COVER PAGE
══════════════════════════════════════════════════════════════════════════ -->
<div class="cover">
  <div class="cover-noise"></div>
  <div class="cover-line"></div>

  <div class="cover-header">
    <div class="cover-brand">
      <div class="cover-brand-name">{b['name']}</div>
      <div class="cover-brand-tag">{b.get('cover_tag', 'Generative Engine Optimization Audit')}</div>
    </div>
    <div class="cover-confidential">Confidential</div>
  </div>

  <div class="cover-divider"></div>

  <div class="cover-body">
    <div class="cover-eyebrow">GEO Visibility Report</div>
    <div class="cover-title">{company}<br><em>{url}</em></div>
    <div class="cover-url">{audit_date}</div>

    <div class="cover-logo-block">
      {logo_html}
      <div class="cover-logo-meta">
        <span>{company}</span>
        <span>{url}</span>
      </div>
    </div>

    {'<div class="cover-stats">' + stats_html + '</div>' if stats else ''}

    <div class="cover-score-row">
      <div class="cover-score-gauge">{gauge_svg(overall, 180)}</div>
      <div class="cover-score-text">
        <div class="cover-score-label">Overall GEO Score</div>
        <div class="cover-score-value">{overall} / 100 — {overall_label}</div>
        <div class="cover-score-verdict">{tagline}</div>
      </div>
    </div>
  </div>

  <div class="cover-footer">
    <div class="cover-footer-left">
      <div class="cover-footer-name">{b['contact_name']}</div>
      <div class="cover-footer-contact">{b['phone']} · {b['website']}</div>
    </div>
    <div class="cover-footer-date">{audit_date}</div>
  </div>
</div>


<!-- ══════════════════════════════════════════════════════════════════════════
     PAGE 2 — EXECUTIVE SUMMARY + SCORE BREAKDOWN
══════════════════════════════════════════════════════════════════════════ -->
<div class="content-page">
  <div class="page-label">Executive Summary</div>
  <div class="section-title">The <em>Problem</em></div>
  <div class="section-sub">{url} — Audit conducted {audit_date}</div>

  <div class="exec-summary">{summary}</div>

  <div class="overall-row">
    <div class="overall-row-label">Overall GEO Score</div>
    <div class="overall-row-score">{overall} / 100</div>
    <div class="overall-row-verdict">{overall_label}</div>
  </div>

  <div class="section-divider"></div>
  <div class="page-label">Score Breakdown</div>
  <div class="section-title"><em>Six</em> Dimensions</div>
  <div class="section-sub">Each weighted dimension contributes to your overall GEO score.</div>

  <div class="dim-grid">{dim_cards_html}</div>
  <div class="chart-wrap">{chart_html}</div>

  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Confidential · {audit_date}</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════════════════════════════════
     PAGE 3 — AI READINESS
══════════════════════════════════════════════════════════════════════════ -->
<div class="content-page">
  <div class="page-label">AI Readiness</div>
  <div class="section-title">Platform <em>Scores</em></div>
  <div class="section-sub">How likely each AI search platform is to cite your content. Below 50 means significant barriers.</div>

  <div class="platform-grid">{platforms_html}</div>

  <div class="section-divider"></div>
  <div class="page-label">Crawler Access</div>
  <div class="section-title">Crawler <em>Access Status</em></div>
  <div class="section-sub">Explicit crawler permissions signal AI-friendliness and prevent accidental blocking.</div>

  <table class="crawler-table">
    <thead>
      <tr>
        <th>Crawler</th><th>Platform</th><th>Status</th><th>Recommendation</th>
      </tr>
    </thead>
    <tbody>{crawler_rows_html}</tbody>
  </table>

  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Confidential · {audit_date}</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════════════════════════════════
     PAGE 4 — KEY FINDINGS
══════════════════════════════════════════════════════════════════════════ -->
<div class="content-page">
  <div class="page-label">Key Findings</div>
  <div class="section-title">What We <em>Found</em></div>
  <div class="finding-summary">{len(findings)} issues identified. {finding_summary} Each directly impacts your GEO score.</div>

  {findings_html}

  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Confidential · {audit_date}</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════════════════════════════════
     PAGE 5 — ACTION PLAN
══════════════════════════════════════════════════════════════════════════ -->
<div class="content-page">
  <div class="page-label">Action Plan</div>
  <div class="section-title">What To Do <em>Next</em></div>
  <div class="section-sub">Prioritized by impact and effort. Quick wins can be completed this week.</div>

  {'<div class="action-tier"><div class="tier-header"><span class="tier-label">This Week · Quick Wins</span><span class="tier-badge" style="color:' + c['secondary'] + ';background:' + c['secondary'] + '18;border:1px solid ' + c['secondary'] + '40">Immediate Impact</span></div>' + qw_html + '</div>' if quick_wins else ''}
  {'<div class="action-tier"><div class="tier-header"><span class="tier-label">This Month · Medium-Term</span><span class="tier-badge" style="color:' + c['primary'] + ';background:' + c['primary'] + '18;border:1px solid ' + c['primary'] + '40">Content + Authority</span></div>' + mt_html + '</div>' if medium_term else ''}
  {'<div class="action-tier"><div class="tier-header"><span class="tier-label">This Quarter · Strategic</span><span class="tier-badge" style="color:#9B59B6;background:#9B59B618;border:1px solid #9B59B640">Long-term Advantage</span></div>' + str_html + '</div>' if strategic else ''}

  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Confidential · {audit_date}</span>
  </div>
</div>


<!-- ══════════════════════════════════════════════════════════════════════════
     PAGE 6 — APPENDIX
══════════════════════════════════════════════════════════════════════════ -->
<div class="content-page">
  <div class="page-label">Appendix</div>
  <div class="section-title"><em>Methodology</em></div>
  <div class="section-sub">How this audit was conducted and scored.</div>

  <div class="methodology-text">{methodology or "This GEO audit analyzed the website across six weighted dimensions: AI Citability & Visibility (25%), Brand Authority Signals (20%), Content Quality & E-E-A-T (20%), Technical Foundations (15%), Schema & Structured Data (10%), and Platform Optimization (10%). Platforms assessed: Google AI Overviews, ChatGPT Web Search, Perplexity AI, Google Gemini, Bing Copilot."}</div>

  <div class="section-divider"></div>
  <div class="page-label">Glossary</div>
  <div class="glossary-grid">
    <div class="glossary-item"><div class="glossary-term">GEO</div><div class="glossary-def">Generative Engine Optimization — optimizing for AI citation</div></div>
    <div class="glossary-item"><div class="glossary-term">AIO</div><div class="glossary-def">AI Overviews — Google's AI answer boxes in search</div></div>
    <div class="glossary-item"><div class="glossary-term">E-E-A-T</div><div class="glossary-def">Experience, Expertise, Authoritativeness, Trustworthiness</div></div>
    <div class="glossary-item"><div class="glossary-term">llms.txt</div><div class="glossary-def">Machine-readable file helping AI understand a site's purpose</div></div>
    <div class="glossary-item"><div class="glossary-term">SSR</div><div class="glossary-def">Server-Side Rendering — HTML generated server-side for crawlers</div></div>
    <div class="glossary-item"><div class="glossary-term">Schema.org</div><div class="glossary-def">Structured data vocabulary for search engines and AI</div></div>
    <div class="glossary-item"><div class="glossary-term">sameAs</div><div class="glossary-def">Schema.org property linking entity to profiles on other platforms</div></div>
    <div class="glossary-item"><div class="glossary-term">IndexNow</div><div class="glossary-def">Protocol for instant search engine content change notification</div></div>
  </div>

  <div class="section-divider"></div>
  <div style="text-align:center;padding:20px 0;font-size:10px;color:var(--muted);">
    Scores based on automated analysis and industry benchmarks. Validate with platform-specific testing.<br>
    © {datetime.now().year} {b['name']} — Confidential · {b['website']}
  </div>

  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Confidential · {audit_date}</span>
  </div>
</div>

</div><!-- .page -->
</body>
</html>"""
    return html


def generate_pdf(html: str, output_path: str):
    """Convert HTML to PDF using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
            )
            browser.close()
        print(f"  PDF saved: {output_path}")
    except Exception as e:
        print(f"  Playwright error: {e}")
        # Fallback: save HTML for manual conversion
        html_path = output_path.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  HTML fallback saved: {html_path}")


def main():
    parser = argparse.ArgumentParser(description="GEO Report Premium Beautifier — La Crown Inc.")
    parser.add_argument("data_file", help="Path to JSON data file (see SKILL.md for schema)")
    parser.add_argument("--output", "-o", default="geo-report-premium.pdf", help="Output PDF path")
    parser.add_argument("--client-logo", "-l", help="Path to client logo image (PNG/SVG)")
    parser.add_argument("--brand-config", "-b", help="Path to a brand.json to white-label the report (name, colors, contact, etc.)")
    parser.add_argument("--html-only", action="store_true", help="Save HTML only, skip PDF")
    args = parser.parse_args()

    # Apply white-label brand config (deep-merges over the La Crown defaults)
    if args.brand_config:
        apply_brand_config(args.brand_config)

    # Load data
    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n  GEO Report Premium Beautifier")
    print(f"  {BRAND['name']} — {BRAND['website']}")
    print(f"  Client: {data.get('company_name', 'Unknown')}")
    print(f"  Score:  {data.get('overall_score', 0)}/100\n")

    html = generate_html(data, logo_path=args.client_logo)

    if args.html_only:
        html_path = args.output.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  HTML saved: {html_path}")
    else:
        generate_pdf(html, args.output)

    print("  Done.")


if __name__ == "__main__":
    main()
