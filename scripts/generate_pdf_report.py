#!/usr/bin/env python3
"""
GEO-SEO PDF Report Generator
Generates professional, client-ready PDF reports from GEO audit data.

Usage:
    python generate_pdf_report.py <json_data_file> [output_file.pdf]

The JSON data file should contain the audit results structured as:
{
    "url": "https://example.com",
    "brand_name": "Example Co",
    "date": "2026-02-18",
    "geo_score": 62,
    "scores": { ... },
    "findings": { ... },
    ...
}

Or pipe JSON data from stdin:
    cat audit_data.json | python generate_pdf_report.py - output.pdf
"""

import sys
import json
import os
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch, mm
    from reportlab.lib.colors import (
        HexColor, black, white, grey, lightgrey, darkgrey,
        Color
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether, Image as RLImage
    )
    from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line, Wedge
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics import renderPDF
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)


# ============================================================
# COLOR PALETTE
# ============================================================
PRIMARY = HexColor("#1a1a2e")       # Dark navy
SECONDARY = HexColor("#16213e")     # Slightly lighter navy
ACCENT = HexColor("#0f3460")        # Blue accent
HIGHLIGHT = HexColor("#e94560")     # Red/coral highlight
SUCCESS = HexColor("#00b894")       # Green
WARNING = HexColor("#fdcb6e")       # Yellow/amber
DANGER = HexColor("#d63031")        # Red
INFO = HexColor("#0984e3")          # Blue
LIGHT_BG = HexColor("#f8f9fa")      # Light background
MEDIUM_BG = HexColor("#e9ecef")     # Medium background
TEXT_PRIMARY = HexColor("#2d3436")   # Dark text
TEXT_SECONDARY = HexColor("#636e72") # Grey text
WHITE = white
BLACK = black


def get_score_color(score):
    """Return color based on score value."""
    if score >= 80:
        return SUCCESS
    elif score >= 60:
        return INFO
    elif score >= 40:
        return WARNING
    else:
        return DANGER


def get_score_label(score):
    """Return label based on score value."""
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 55:
        return "Moderate"
    elif score >= 40:
        return "Below Average"
    else:
        return "Needs Attention"


def create_score_gauge(score, width=120, height=120):
    """Create a visual score gauge."""
    d = Drawing(width, height)

    # Background circle
    d.add(Circle(width/2, height/2, 50, fillColor=LIGHT_BG, strokeColor=lightgrey, strokeWidth=2))

    # Score arc (simplified as colored circle)
    color = get_score_color(score)
    d.add(Circle(width/2, height/2, 45, fillColor=color, strokeColor=None))

    # Inner white circle
    d.add(Circle(width/2, height/2, 35, fillColor=WHITE, strokeColor=None))

    # Score text
    d.add(String(width/2, height/2 + 5, str(score),
                 fontSize=24, fontName='Helvetica-Bold',
                 fillColor=TEXT_PRIMARY, textAnchor='middle'))

    # Label
    d.add(String(width/2, height/2 - 12, "/100",
                 fontSize=10, fontName='Helvetica',
                 fillColor=TEXT_SECONDARY, textAnchor='middle'))

    return d


def create_bar_chart(data, labels, width=400, height=200):
    """Create a horizontal bar chart for scores."""
    d = Drawing(width, height)

    chart = VerticalBarChart()
    chart.x = 60
    chart.y = 30
    chart.height = height - 60
    chart.width = width - 80
    chart.data = [data]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.angle = 0
    chart.categoryAxis.labels.fontSize = 8
    chart.categoryAxis.labels.fontName = 'Helvetica'
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 100
    chart.valueAxis.valueStep = 20
    chart.valueAxis.labels.fontSize = 8

    # Color each bar based on score
    for i, score in enumerate(data):
        chart.bars[0].fillColor = get_score_color(score)

    chart.bars[0].strokeColor = None
    chart.bars[0].strokeWidth = 0

    d.add(chart)
    return d


def create_platform_chart(platforms, width=450, height=180):
    """Create a chart showing platform readiness scores."""
    d = Drawing(width, height)

    bar_height = 22
    bar_max_width = 280
    start_y = height - 30
    label_x = 10

    for i, (name, score) in enumerate(platforms.items()):
        y = start_y - (i * (bar_height + 10))

        # Platform name
        d.add(String(label_x, y + 5, name,
                     fontSize=9, fontName='Helvetica',
                     fillColor=TEXT_PRIMARY, textAnchor='start'))

        # Background bar
        bar_x = 130
        d.add(Rect(bar_x, y, bar_max_width, bar_height,
                    fillColor=LIGHT_BG, strokeColor=None))

        # Score bar
        bar_width = (score / 100) * bar_max_width
        color = get_score_color(score)
        d.add(Rect(bar_x, y, bar_width, bar_height,
                    fillColor=color, strokeColor=None))

        # Score text
        d.add(String(bar_x + bar_max_width + 10, y + 6, f"{score}/100",
                     fontSize=9, fontName='Helvetica-Bold',
                     fillColor=TEXT_PRIMARY, textAnchor='start'))

    return d


def build_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ReportTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=PRIMARY,
        spaceAfter=6,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        fontName='Helvetica',
        fontSize=14,
        textColor=TEXT_SECONDARY,
        spaceAfter=20,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=PRIMARY,
        spaceBefore=20,
        spaceAfter=10,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='SubHeader',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=ACCENT,
        spaceBefore=14,
        spaceAfter=6,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='BodyText_Custom',
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_PRIMARY,
        spaceBefore=4,
        spaceAfter=4,
        leading=14,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        name='SmallText',
        fontName='Helvetica',
        fontSize=8,
        textColor=TEXT_SECONDARY,
        spaceBefore=2,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name='ScoreLabel',
        fontName='Helvetica-Bold',
        fontSize=36,
        textColor=PRIMARY,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='HighlightBox',
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_PRIMARY,
        backColor=LIGHT_BG,
        borderPadding=10,
        spaceBefore=8,
        spaceAfter=8,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        name='CriticalFinding',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=DANGER,
        spaceBefore=4,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name='Recommendation',
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_PRIMARY,
        leftIndent=15,
        spaceBefore=3,
        spaceAfter=3,
        bulletIndent=5,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        fontName='Helvetica',
        fontSize=8,
        textColor=TEXT_SECONDARY,
        alignment=TA_CENTER,
    ))

    return styles


def header_footer(canvas, doc):
    """Add header and footer to each page."""
    canvas.saveState()

    # Header line
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(2)
    canvas.line(50, letter[1] - 40, letter[0] - 50, letter[1] - 40)

    # Header text
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(TEXT_SECONDARY)
    canvas.drawString(50, letter[1] - 35, "GEO-SEO Analysis Report")

    # Footer
    canvas.setStrokeColor(lightgrey)
    canvas.setLineWidth(0.5)
    canvas.line(50, 40, letter[0] - 50, 40)

    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(TEXT_SECONDARY)
    canvas.drawString(50, 28, f"Generated {datetime.now().strftime('%B %d, %Y')}")
    canvas.drawRightString(letter[0] - 50, 28, f"Page {doc.page}")
    canvas.drawCentredString(letter[0] / 2, 28, "Confidential")

    canvas.restoreState()


def make_table_style(header_color=PRIMARY):
    """Create a consistent table style."""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, lightgrey),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ])


def generate_report(data, output_path="GEO-REPORT.pdf"):
    """Generate the full PDF report from audit data."""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=55,
        bottomMargin=55,
        leftMargin=50,
        rightMargin=50,
    )

    styles = build_styles()
    elements = []

    # Extract data with defaults
    url = data.get("url", "https://example.com")
    brand_name = data.get("brand_name", url.replace("https://", "").replace("http://", "").split("/")[0])
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    geo_score = data.get("geo_score", 0)

    scores = data.get("scores", {})
    ai_citability = scores.get("ai_citability", 0)
    brand_authority = scores.get("brand_authority", 0)
    content_eeat = scores.get("content_eeat", 0)
    technical = scores.get("technical", 0)
    schema_score = scores.get("schema", 0)
    platform_optimization = scores.get("platform_optimization", 0)

    platforms = data.get("platforms", {
        "Google AI Overviews": 0,
        "ChatGPT": 0,
        "Perplexity": 0,
        "Gemini": 0,
        "Bing Copilot": 0,
    })

    crawlers = data.get("crawlers", [])
    findings = data.get("findings", [])
    quick_wins = data.get("quick_wins", [])
    medium_term = data.get("medium_term", [])
    strategic = data.get("strategic", [])
    executive_summary = data.get("executive_summary", "")
    crawler_access = data.get("crawler_access", {})
    schema_findings = data.get("schema_findings", {})
    content_findings = data.get("content_findings", {})
    technical_findings = data.get("technical_findings", {})
    brand_findings = data.get("brand_findings", {})

    # ============================================================
    # COVER PAGE
    # ============================================================
    elements.append(Spacer(1, 100))

    # Title
    elements.append(Paragraph("GEO Analysis Report", styles['ReportTitle']))
    elements.append(Spacer(1, 8))

    # Subtitle
    elements.append(Paragraph(
        f"Generative Engine Optimization Audit for <b>{brand_name}</b>",
        styles['ReportSubtitle']
    ))

    elements.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=20))

    # Key details table
    details_data = [
        ["Website", url],
        ["Analysis Date", datetime.strptime(date, "%Y-%m-%d").strftime("%B %d, %Y") if "-" in date else date],
        ["GEO Score", f"{geo_score}/100 — {get_score_label(geo_score)}"],
    ]

    details_table = Table(details_data, colWidths=[120, 350])
    details_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), ACCENT),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_PRIMARY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, lightgrey),
    ]))
    elements.append(details_table)

    elements.append(Spacer(1, 30))

    # Score gauge
    gauge = create_score_gauge(geo_score, 200, 200)
    elements.append(gauge)

    elements.append(Spacer(1, 20))

    # Score label
    score_color = get_score_color(geo_score)
    elements.append(Paragraph(
        f'<font color="{score_color.hexval()}">{get_score_label(geo_score)}</font>',
        ParagraphStyle('ScoreLabelColored', parent=styles['SectionHeader'],
                       alignment=TA_CENTER, fontSize=20)
    ))

    elements.append(PageBreak())

    # ============================================================
    # EXECUTIVE SUMMARY
    # ============================================================
    elements.append(Paragraph("Executive Summary", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))

    if executive_summary:
        elements.append(Paragraph(executive_summary, styles['BodyText_Custom']))
    else:
        elements.append(Paragraph(
            f"This report presents the findings of a comprehensive Generative Engine Optimization (GEO) "
            f"audit conducted on <b>{brand_name}</b> ({url}). The analysis evaluated the website's readiness "
            f"for AI-powered search engines including Google AI Overviews, ChatGPT, Perplexity, Gemini, "
            f"and Bing Copilot. The overall GEO Readiness Score is <b>{geo_score}/100</b>, "
            f"placing the site in the <b>{get_score_label(geo_score)}</b> tier.",
            styles['BodyText_Custom']
        ))

    elements.append(Spacer(1, 16))

    # ============================================================
    # SCORE BREAKDOWN
    # ============================================================
    elements.append(Paragraph("GEO Score Breakdown", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))

    score_data = [
        ["Component", "Score", "Weight", "Weighted"],
        ["AI Citability & Visibility", f"{ai_citability}/100", "25%", f"{round(ai_citability * 0.25, 1)}"],
        ["Brand Authority Signals", f"{brand_authority}/100", "20%", f"{round(brand_authority * 0.20, 1)}"],
        ["Content Quality & E-E-A-T", f"{content_eeat}/100", "20%", f"{round(content_eeat * 0.20, 1)}"],
        ["Technical Foundations", f"{technical}/100", "15%", f"{round(technical * 0.15, 1)}"],
        ["Structured Data", f"{schema_score}/100", "10%", f"{round(schema_score * 0.10, 1)}"],
        ["Platform Optimization", f"{platform_optimization}/100", "10%", f"{round(platform_optimization * 0.10, 1)}"],
        ["OVERALL", f"{geo_score}/100", "100%", f"{geo_score}"],
    ]

    score_table = Table(score_data, colWidths=[200, 80, 60, 80])
    style = make_table_style()

    # Bold the last row
    style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    style.add('BACKGROUND', (0, -1), (-1, -1), MEDIUM_BG)

    # Color-code score cells
    for i in range(1, len(score_data) - 1):
        score_val = int(score_data[i][1].split("/")[0])
        color = get_score_color(score_val)
        style.add('TEXTCOLOR', (1, i), (1, i), color)

    score_table.setStyle(style)
    elements.append(score_table)

    elements.append(Spacer(1, 16))

    # Score bar chart
    chart_scores = [ai_citability, brand_authority, content_eeat, technical, schema_score, platform_optimization]
    chart_labels = ["Citability", "Brand", "Content", "Technical", "Schema", "Platform"]
    elements.append(create_bar_chart(chart_scores, chart_labels))

    elements.append(PageBreak())

    # ============================================================
    # AI PLATFORM READINESS
    # ============================================================
    elements.append(Paragraph("AI Platform Readiness", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))

    elements.append(Paragraph(
        "These scores reflect how likely your content is to be cited by each AI search platform. "
        "A score below 50 indicates significant barriers to citation on that platform.",
        styles['BodyText_Custom']
    ))
    elements.append(Spacer(1, 10))

    # Platform chart
    if platforms:
        elements.append(create_platform_chart(platforms))

    elements.append(Spacer(1, 10))

    # Platform table
    platform_table_data = [["AI Platform", "Score", "Status"]]
    for name, score in platforms.items():
        status = get_score_label(score)
        platform_table_data.append([name, f"{score}/100", status])

    pt = Table(platform_table_data, colWidths=[180, 80, 150])
    pt_style = make_table_style()
    for i in range(1, len(platform_table_data)):
        score_val = int(platform_table_data[i][1].split("/")[0])
        color = get_score_color(score_val)
        pt_style.add('TEXTCOLOR', (1, i), (1, i), color)
    pt.setStyle(pt_style)
    elements.append(pt)

    elements.append(PageBreak())

    # ============================================================
    # AI CRAWLER ACCESS
    # ============================================================
    elements.append(Paragraph("AI Crawler Access Status", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))

    elements.append(Paragraph(
        "Blocking AI crawlers prevents AI platforms from citing your content. "
        "The table below shows which AI crawlers can currently access your site.",
        styles['BodyText_Custom']
    ))
    elements.append(Spacer(1, 8))

    if crawler_access:
        # Use Paragraph objects for text wrapping in cells
        cell_style = ParagraphStyle(
            'CrawlerCell', fontName='Helvetica', fontSize=9,
            textColor=TEXT_PRIMARY, leading=12,
        )
        header_cell_style = ParagraphStyle(
            'CrawlerHeaderCell', fontName='Helvetica-Bold', fontSize=9,
            textColor=WHITE, leading=12,
        )
        status_style_allowed = ParagraphStyle(
            'StatusAllowed', fontName='Helvetica-Bold', fontSize=9,
            textColor=SUCCESS, leading=12,
        )
        status_style_blocked = ParagraphStyle(
            'StatusBlocked', fontName='Helvetica-Bold', fontSize=9,
            textColor=DANGER, leading=12,
        )
        status_style_restricted = ParagraphStyle(
            'StatusRestricted', fontName='Helvetica-Bold', fontSize=9,
            textColor=WARNING, leading=12,
        )
        status_style_default = ParagraphStyle(
            'StatusDefault', fontName='Helvetica', fontSize=9,
            textColor=TEXT_PRIMARY, leading=12,
        )

        crawler_data = [[
            Paragraph("Crawler", header_cell_style),
            Paragraph("Platform", header_cell_style),
            Paragraph("Status", header_cell_style),
            Paragraph("Recommendation", header_cell_style),
        ]]
        for crawler_name, info in crawler_access.items():
            if isinstance(info, dict):
                status_text = info.get("status", "Unknown")
                status_upper = status_text.upper()
                if "ALLOW" in status_upper:
                    s_style = status_style_allowed
                elif "BLOCK" in status_upper:
                    s_style = status_style_blocked
                elif "RESTRICT" in status_upper:
                    s_style = status_style_restricted
                else:
                    s_style = status_style_default

                crawler_data.append([
                    Paragraph(crawler_name, cell_style),
                    Paragraph(info.get("platform", ""), cell_style),
                    Paragraph(status_text, s_style),
                    Paragraph(info.get("recommendation", ""), cell_style),
                ])
            else:
                crawler_data.append([
                    Paragraph(crawler_name, cell_style),
                    Paragraph("", cell_style),
                    Paragraph(str(info), cell_style),
                    Paragraph("", cell_style),
                ])

        # Full page width: letter (612pt) - 50pt margins each side = 512pt
        ct = Table(crawler_data, colWidths=[90, 110, 72, 240])
        ct_style = make_table_style()
        ct_style.add('VALIGN', (0, 0), (-1, -1), 'TOP')

        ct.setStyle(ct_style)
        elements.append(ct)
    else:
        elements.append(Paragraph(
            "<i>Run /geo crawlers to populate this section with AI crawler access data.</i>",
            styles['BodyText_Custom']
        ))

    elements.append(PageBreak())

    # ============================================================
    # KEY FINDINGS
    # ============================================================
    elements.append(Paragraph("Key Findings", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))

    if findings:
        for finding in findings:
            severity = finding.get("severity", "info").upper()
            title = finding.get("title", "")
            description = finding.get("description", "")

            if severity == "CRITICAL":
                sev_color = DANGER
            elif severity == "HIGH":
                sev_color = WARNING
            elif severity == "MEDIUM":
                sev_color = INFO
            else:
                sev_color = TEXT_SECONDARY

            elements.append(Paragraph(
                f'<font color="{sev_color.hexval()}">[{severity}]</font> <b>{title}</b>',
                styles['BodyText_Custom']
            ))
            if description:
                elements.append(Paragraph(description, styles['Recommendation']))
            elements.append(Spacer(1, 4))
    else:
        elements.append(Paragraph(
            "<i>Run a full /geo audit to populate findings.</i>",
            styles['BodyText_Custom']
        ))

    elements.append(PageBreak())

    # ============================================================
    # PRIORITIZED ACTION PLAN
    # ============================================================
    elements.append(Paragraph("Prioritized Action Plan", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))

    # Quick Wins
    elements.append(Paragraph("Quick Wins (This Week)", styles['SubHeader']))
    elements.append(Paragraph(
        "High impact, low effort — can be implemented immediately.",
        styles['SmallText']
    ))

    if quick_wins:
        for i, action in enumerate(quick_wins, 1):
            if isinstance(action, dict):
                text = f"<b>{i}.</b> {action.get('action', '')} — <i>{action.get('impact', '')}</i>"
            else:
                text = f"<b>{i}.</b> {action}"
            elements.append(Paragraph(text, styles['Recommendation']))
    else:
        default_wins = [
            "Allow all Tier 1 AI crawlers in robots.txt (GPTBot, ClaudeBot, PerplexityBot)",
            "Add publication and last-updated dates to all content pages",
            "Add author bylines with credentials to blog posts and articles",
            "Create an llms.txt file to guide AI systems to your key content",
            "Add sameAs properties to Organization schema linking to all platform profiles",
        ]
        for i, action in enumerate(default_wins, 1):
            elements.append(Paragraph(f"<b>{i}.</b> {action}", styles['Recommendation']))

    elements.append(Spacer(1, 12))

    # Medium-Term
    elements.append(Paragraph("Medium-Term Improvements (This Month)", styles['SubHeader']))
    elements.append(Paragraph(
        "Significant impact, moderate effort — requires content or technical changes.",
        styles['SmallText']
    ))

    if medium_term:
        for i, action in enumerate(medium_term, 1):
            if isinstance(action, dict):
                text = f"<b>{i}.</b> {action.get('action', '')} — <i>{action.get('impact', '')}</i>"
            else:
                text = f"<b>{i}.</b> {action}"
            elements.append(Paragraph(text, styles['Recommendation']))
    else:
        default_medium = [
            "Restructure top 10 pages with question-based headings and direct answer blocks",
            "Implement comprehensive Organization + Article + Person schema markup",
            "Optimize content blocks for AI citability (134-167 word self-contained passages)",
            "Ensure server-side rendering for all public content pages",
            "Implement IndexNow protocol for Bing/Copilot indexing speed",
        ]
        for i, action in enumerate(default_medium, 1):
            elements.append(Paragraph(f"<b>{i}.</b> {action}", styles['Recommendation']))

    elements.append(Spacer(1, 12))

    # Strategic
    elements.append(Paragraph("Strategic Initiatives (This Quarter)", styles['SubHeader']))
    elements.append(Paragraph(
        "Long-term competitive advantage — requires ongoing investment.",
        styles['SmallText']
    ))

    if strategic:
        for i, action in enumerate(strategic, 1):
            if isinstance(action, dict):
                text = f"<b>{i}.</b> {action.get('action', '')} — <i>{action.get('impact', '')}</i>"
            else:
                text = f"<b>{i}.</b> {action}"
            elements.append(Paragraph(text, styles['Recommendation']))
    else:
        default_strategic = [
            "Build Wikipedia/Wikidata entity presence through press coverage and notability",
            "Develop active Reddit community engagement strategy in relevant subreddits",
            "Create YouTube content strategy aligned with AI-searched queries",
            "Establish original research/data publication program for unique citability",
            "Build topical authority through comprehensive content clusters",
        ]
        for i, action in enumerate(default_strategic, 1):
            elements.append(Paragraph(f"<b>{i}.</b> {action}", styles['Recommendation']))

    elements.append(PageBreak())

    # ============================================================
    # METHODOLOGY & GLOSSARY
    # ============================================================
    elements.append(Paragraph("Appendix: Methodology", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))

    elements.append(Paragraph(
        f"This GEO audit was conducted on {date} analyzing {url}. "
        "The analysis evaluated the website across six dimensions: AI Citability & Visibility (25%), "
        "Brand Authority Signals (20%), Content Quality & E-E-A-T (20%), Technical Foundations (15%), "
        "Structured Data (10%), and Platform Optimization (10%).",
        styles['BodyText_Custom']
    ))

    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "<b>Platforms assessed:</b> Google AI Overviews, ChatGPT Web Search, Perplexity AI, "
        "Google Gemini, Bing Copilot",
        styles['BodyText_Custom']
    ))

    elements.append(Paragraph(
        "<b>Standards referenced:</b> Google Search Quality Rater Guidelines (Dec 2025), "
        "Schema.org specification, Core Web Vitals (2026 thresholds), "
        "llms.txt emerging standard, RSL 1.0 licensing framework",
        styles['BodyText_Custom']
    ))

    elements.append(Spacer(1, 16))

    # Glossary
    elements.append(Paragraph("Glossary", styles['SubHeader']))

    glossary = [
        ["Term", "Definition"],
        ["GEO", "Generative Engine Optimization — optimizing content for AI search citation"],
        ["AIO", "AI Overviews — Google's AI-generated answer boxes in search results"],
        ["E-E-A-T", "Experience, Expertise, Authoritativeness, Trustworthiness"],
        ["SSR", "Server-Side Rendering — generating HTML on the server for crawler access"],
        ["CWV", "Core Web Vitals — Google's page experience metrics (LCP, INP, CLS)"],
        ["INP", "Interaction to Next Paint — responsiveness metric (replaced FID March 2024)"],
        ["JSON-LD", "JavaScript Object Notation for Linked Data — preferred structured data format"],
        ["sameAs", "Schema.org property linking an entity to its profiles on other platforms"],
        ["llms.txt", "Proposed standard file for guiding AI systems about site content"],
        ["IndexNow", "Protocol for instantly notifying search engines of content changes"],
    ]

    gt = Table(glossary, colWidths=[80, 380])
    gt.setStyle(make_table_style())
    elements.append(gt)

    elements.append(Spacer(1, 30))

    # Footer disclaimer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=lightgrey, spaceAfter=8))
    elements.append(Paragraph(
        "This report was generated by the GEO-SEO Claude Code Analysis Tool. "
        "Scores and recommendations are based on automated analysis and industry benchmarks. "
        "Results should be validated with platform-specific testing.",
        styles['SmallText']
    ))

    # ============================================================
    # BUILD PDF
    # ============================================================
    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Generate a sample report for demonstration
        sample_data = {
            "url": "https://example.com",
            "brand_name": "Example Company",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "geo_score": 58,
            "scores": {
                "ai_citability": 45,
                "brand_authority": 62,
                "content_eeat": 70,
                "technical": 55,
                "schema": 30,
                "platform_optimization": 48,
            },
            "platforms": {
                "Google AI Overviews": 65,
                "ChatGPT": 52,
                "Perplexity": 48,
                "Gemini": 60,
                "Bing Copilot": 45,
            },
            "executive_summary": (
                "This report presents the findings of a comprehensive GEO audit "
                "conducted on Example Company (https://example.com). The site achieved "
                "an overall GEO Readiness Score of 58/100, placing it in the Moderate tier. "
                "The strongest area is Content Quality (70/100), while Structured Data (30/100) "
                "represents the biggest opportunity for improvement. Implementing schema markup, "
                "allowing AI crawlers, and optimizing content structure could increase the score "
                "to approximately 78/100 within 90 days."
            ),
            "findings": [
                {"severity": "critical", "title": "No Schema Markup Detected",
                 "description": "The site has no JSON-LD structured data, making it difficult for AI models to understand entity relationships."},
                {"severity": "high", "title": "JavaScript-Only Rendering",
                 "description": "Key content pages use client-side rendering, making them invisible to AI crawlers that don't execute JavaScript."},
                {"severity": "high", "title": "Missing llms.txt",
                 "description": "No llms.txt file exists to guide AI systems to the most important content."},
                {"severity": "medium", "title": "Weak Brand Entity Presence",
                 "description": "Brand is not present on Wikipedia or Wikidata, limiting entity recognition by AI models."},
                {"severity": "medium", "title": "Content Not Optimized for Citability",
                 "description": "Most content blocks are either too short or too long for optimal AI citation (target: 134-167 words)."},
            ],
            "quick_wins": [
                "Allow all Tier 1 AI crawlers in robots.txt",
                "Add publication dates to all content pages",
                "Create llms.txt file with key page references",
                "Add author bylines with credentials",
                "Fix meta descriptions on top 10 pages",
            ],
            "medium_term": [
                "Implement Organization schema with sameAs linking",
                "Add Article + Person schema to all blog posts",
                "Restructure content with question-based H2 headings",
                "Optimize content blocks for 134-167 word citability",
                "Implement server-side rendering for content pages",
            ],
            "strategic": [
                "Build Wikipedia/Wikidata entity presence",
                "Develop Reddit community engagement strategy",
                "Create YouTube content aligned with AI search queries",
                "Establish original research publication program",
                "Build comprehensive topical authority content clusters",
            ],
            "crawler_access": {
                "GPTBot": {"platform": "ChatGPT", "status": "Allowed", "recommendation": "Keep allowed"},
                "ClaudeBot": {"platform": "Claude", "status": "Allowed", "recommendation": "Keep allowed"},
                "PerplexityBot": {"platform": "Perplexity", "status": "Blocked", "recommendation": "Unblock for visibility"},
                "Google-Extended": {"platform": "Gemini", "status": "Allowed", "recommendation": "Keep allowed"},
                "Bingbot": {"platform": "Bing Copilot", "status": "Allowed", "recommendation": "Keep allowed"},
            },
        }

        output_file = "GEO-REPORT-sample.pdf"
        result = generate_report(sample_data, output_file)
        print(f"Report generated: {result}")

    else:
        # Load data from file or stdin
        input_path = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "GEO-REPORT.pdf"

        if input_path == "-":
            MAX_STDIN_BYTES = 10_000_000
            raw = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
            if len(raw) > MAX_STDIN_BYTES:
                print("ERROR: stdin input exceeds 10 MB limit", file=sys.stderr)
                sys.exit(1)
            data = json.loads(raw)
        else:
            with open(input_path) as f:
                data = json.load(f)

        result = generate_report(data, output_file)
        print(f"Report generated: {result}")
