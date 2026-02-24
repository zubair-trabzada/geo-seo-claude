#!/usr/bin/env python3
"""Generate a client-facing GEO optimization guide PDF for BaraBand.se"""

import sys
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white, black, lightgrey
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem
    )
except ImportError:
    print("ERROR: ReportLab required. Run: pip install reportlab")
    sys.exit(1)

# Colors
PRIMARY = HexColor("#1a1a2e")
ACCENT = HexColor("#0f3460")
HIGHLIGHT = HexColor("#e94560")
SUCCESS = HexColor("#00b894")
WARNING = HexColor("#fdcb6e")
DANGER = HexColor("#d63031")
INFO = HexColor("#0984e3")
LIGHT_BG = HexColor("#f8f9fa")
MEDIUM_BG = HexColor("#e9ecef")
TEXT = HexColor("#2d3436")
TEXT_LIGHT = HexColor("#636e72")

def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=28,
        textColor=PRIMARY, spaceAfter=8, alignment=TA_LEFT))
    styles.add(ParagraphStyle('CoverSub', fontName='Helvetica', fontSize=14,
        textColor=TEXT_LIGHT, spaceAfter=20, alignment=TA_LEFT))
    styles.add(ParagraphStyle('Phase', fontName='Helvetica-Bold', fontSize=20,
        textColor=PRIMARY, spaceBefore=24, spaceAfter=10))
    styles.add(ParagraphStyle('StepTitle', fontName='Helvetica-Bold', fontSize=14,
        textColor=ACCENT, spaceBefore=16, spaceAfter=6))
    styles.add(ParagraphStyle('Body', fontName='Helvetica', fontSize=10,
        textColor=TEXT, spaceBefore=3, spaceAfter=3, leading=14, alignment=TA_LEFT))
    styles.add(ParagraphStyle('BodyBold', fontName='Helvetica-Bold', fontSize=10,
        textColor=TEXT, spaceBefore=3, spaceAfter=3, leading=14))
    styles.add(ParagraphStyle('Instruction', fontName='Helvetica', fontSize=10,
        textColor=TEXT, leftIndent=15, spaceBefore=2, spaceAfter=2, leading=14))
    styles.add(ParagraphStyle('CodeBlock', fontName='Courier', fontSize=8.5,
        textColor=HexColor("#2d3436"), backColor=LIGHT_BG, borderPadding=8,
        spaceBefore=6, spaceAfter=6, leading=12, leftIndent=15))
    styles.add(ParagraphStyle('Note', fontName='Helvetica-Oblique', fontSize=9,
        textColor=INFO, spaceBefore=4, spaceAfter=4, leftIndent=15))
    styles.add(ParagraphStyle('Impact', fontName='Helvetica-Bold', fontSize=9,
        textColor=SUCCESS, spaceBefore=4, spaceAfter=8, leftIndent=15))
    styles.add(ParagraphStyle('Small', fontName='Helvetica', fontSize=8,
        textColor=TEXT_LIGHT, spaceBefore=2, spaceAfter=2))
    styles.add(ParagraphStyle('Footer', fontName='Helvetica', fontSize=8,
        textColor=TEXT_LIGHT, alignment=TA_CENTER))
    styles.add(ParagraphStyle('TOCItem', fontName='Helvetica', fontSize=11,
        textColor=ACCENT, spaceBefore=6, spaceAfter=6, leftIndent=10))
    styles.add(ParagraphStyle('Warning', fontName='Helvetica-Bold', fontSize=10,
        textColor=DANGER, spaceBefore=4, spaceAfter=4, leftIndent=15))
    return styles

def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.5)
    canvas.line(40, A4[1] - 35, A4[0] - 40, A4[1] - 35)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawString(40, A4[1] - 30, "BaraBand.se — GEO Optimization Guide")
    canvas.setStrokeColor(lightgrey)
    canvas.setLineWidth(0.5)
    canvas.line(40, 35, A4[0] - 40, 35)
    canvas.drawString(40, 22, f"Prepared {datetime.now().strftime('%B %d, %Y')}")
    canvas.drawRightString(A4[0] - 40, 22, f"Page {doc.page}")
    canvas.drawCentredString(A4[0] / 2, 22, "Confidential")
    canvas.restoreState()

def make_table(data, col_widths=None):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t

def generate():
    doc = SimpleDocTemplate("GEO-GUIDE-BaraBand.pdf", pagesize=A4,
        topMargin=45, bottomMargin=45, leftMargin=40, rightMargin=40)
    s = build_styles()
    e = []

    # ── COVER ──
    e.append(Spacer(1, 80))
    e.append(Paragraph("GEO Optimization Guide", s['CoverTitle']))
    e.append(Paragraph("BaraBand.se — Step-by-Step Implementation Plan", s['CoverSub']))
    e.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=20))

    cover_info = [
        ["Prepared for", "BaraBand.se"],
        ["Website", "https://www.baraband.se"],
        ["Current GEO Score", "39 / 100"],
        ["Target GEO Score", "70+ / 100 (within 90 days)"],
        ["Date", datetime.now().strftime("%B %d, %Y")],
    ]
    ct = Table(cover_info, colWidths=[140, 340])
    ct.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), ACCENT),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, lightgrey),
    ]))
    e.append(ct)
    e.append(Spacer(1, 40))
    e.append(Paragraph(
        "This guide contains step-by-step instructions to optimize BaraBand.se for AI-powered "
        "search engines (Google AI Overviews, ChatGPT, Perplexity, Bing Copilot). Each step "
        "includes exact instructions, where to make changes in Shopify, and the expected impact. "
        "Steps are ordered by priority — start from the top and work your way down.",
        s['Body']))
    e.append(Spacer(1, 20))
    e.append(Paragraph(
        "<b>What is GEO?</b> Generative Engine Optimization is the practice of optimizing your "
        "website so that AI search engines cite, recommend, and surface your products in their "
        "answers. AI-referred traffic has grown +527% year-over-year and converts 4.4x better "
        "than traditional organic traffic.",
        s['Body']))

    e.append(PageBreak())

    # ── TABLE OF CONTENTS ──
    e.append(Paragraph("Table of Contents", s['Phase']))
    e.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))
    toc = [
        "Phase 1: Quick Wins (Week 1-2) — Immediate impact, minimal effort",
        "  Step 1: Install a Review App (Judge.me)",
        "  Step 2: Create an llms.txt File",
        "  Step 3: Clean Up the Om Oss (About) Page",
        "  Step 4: Add Author Bio for Blog Posts",
        "  Step 5: Add Company Registration Number to Footer",
        "  Step 6: Submit Sitemap to Bing Webmaster Tools",
        "  Step 7: Add og:locale Meta Tag",
        "Phase 2: Content & Schema (Weeks 3-6) — Build AI-citable content",
        "  Step 8: Create a FAQ Page with Schema Markup",
        "  Step 9: Add BreadcrumbList Schema to Product/Collection Pages",
        "  Step 10: Enhance Organization Schema on Homepage",
        "  Step 11: Publish a Material Comparison Guide",
        "  Step 12: Register on Trustpilot",
        "  Step 13: Install Microsoft Channel on Shopify",
        "Phase 3: Growth Content (Month 2-3) — Deepen authority",
        "  Step 14: Reformat Size Guide as Q&A",
        "  Step 15: Create Apple Watch Compatibility Page",
        "  Step 16: Create Brand Heritage Pages (Hirsch, Fluco, Colareb)",
        "  Step 17: Source and Add GTINs to Products",
        "Phase 4: Authority Building (Month 3+) — Long-term strategy",
        "  Step 18: Build Reddit Presence",
        "  Step 19: Pursue YouTube Coverage",
        "  Step 20: Seek Press / Editorial Mentions",
    ]
    for item in toc:
        indent = 20 if item.startswith("  ") else 0
        bold = not item.startswith("  ")
        style = ParagraphStyle('toc_item', parent=s['Body'],
            fontSize=10 if bold else 9,
            fontName='Helvetica-Bold' if bold else 'Helvetica',
            textColor=PRIMARY if bold else ACCENT,
            leftIndent=indent, spaceBefore=6 if bold else 2, spaceAfter=2)
        e.append(Paragraph(item.strip(), style))

    e.append(PageBreak())

    # ═══════════════════════════════════════════════════
    # PHASE 1
    # ═══════════════════════════════════════════════════
    e.append(Paragraph("Phase 1: Quick Wins (Week 1-2)", s['Phase']))
    e.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    e.append(Paragraph("These steps require minimal technical skill and can be completed in a few hours. "
        "They address the most critical gaps found in the audit.", s['Body']))

    # ── STEP 1 ──
    e.append(Paragraph("Step 1: Install a Review App", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> All four AI platforms (ChatGPT Shopping, Google AI Overviews, Perplexity, "
        "Bing Copilot) require customer reviews and star ratings to recommend products. "
        "BaraBand.se currently has zero reviews on the entire site. This is the single "
        "highest-impact action you can take.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 2 hours &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Easy &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_1 = [
        "Log in to your Shopify Admin panel (baraband.myshopify.com/admin)",
        'Go to <b>Apps</b> in the left sidebar, then click <b>"Search and add apps"</b>',
        'Search for <b>"Judge.me Product Reviews"</b> and install it (the free plan is sufficient)',
        "After installation, go to Judge.me settings:",
        '&nbsp;&nbsp;&nbsp;&nbsp;a. Enable <b>"Automatic review request emails"</b> — this sends an email to customers after delivery asking them to leave a review',
        '&nbsp;&nbsp;&nbsp;&nbsp;b. Set the delay to <b>7 days after fulfillment</b> (gives time for delivery)',
        '&nbsp;&nbsp;&nbsp;&nbsp;c. Enable the <b>review widget</b> on product pages',
        '&nbsp;&nbsp;&nbsp;&nbsp;d. In Judge.me Settings → SEO, ensure <b>"Enable JSON-LD structured data"</b> is turned ON — this adds star ratings that Google can read',
        "Send review requests to past customers: In Judge.me, go to <b>Emails → Import past orders</b> to request reviews from previous buyers",
        "Verify it works: Visit any product page, then test with Google's Rich Results Test (search.google.com/test/rich-results) — you should see Product schema with aggregateRating",
    ]
    for i, step in enumerate(steps_1, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))
    e.append(Paragraph("<b>Target:</b> 10+ reviews on your top 5 products within 60 days.", s['Impact']))

    # ── STEP 2 ──
    e.append(Paragraph("Step 2: Create an llms.txt File", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> llms.txt is the emerging standard for telling AI crawlers what your site is about, "
        "what language it operates in, and which pages are most important. Without it, AI systems "
        "crawl your site blindly. It is the AI equivalent of robots.txt.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 30 minutes &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Easy &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_2 = [
        'In Shopify Admin, go to <b>Online Store → Pages → Add page</b>',
        'Title: <b>"llms.txt"</b>',
        "Paste the following content into the page body (plain text):",
    ]
    for i, step in enumerate(steps_2, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))

    llms_content = (
        "# BaraBand.se - llms.txt<br/>"
        "# Swedish watch strap e-commerce<br/><br/>"
        "&gt; BaraBand.se aer en svensk naetbutik som specialiserar sig paa premium<br/>"
        "&gt; klockarmband fraan Europas ledande tillverkare. Vi saeljer laeder-,<br/>"
        "&gt; gummi-, nylon-, maesh- och hybridarmband i bredder fraan 8mm till 30mm.<br/>"
        "&gt; Vi aer auktoriserad aaterfoersaeljare foer Hirsch (Oesterrike, grundat 1765),<br/>"
        "&gt; Fluco (Tyskland, grundat 1952) och Colareb (Italien).<br/>"
        "&gt; Priser fraan 229 kr till 599+ kr. Fri frakt oever 350 kr, 60 dagars oeppet koep.<br/><br/>"
        "## Key Pages<br/>"
        "- Homepage: https://www.baraband.se<br/>"
        "- Size Guide: https://www.baraband.se/pages/storleksguide<br/>"
        "- All Products: https://www.baraband.se/collections/all<br/>"
        "- Blog: https://www.baraband.se/blogs/news<br/>"
        "- About: https://www.baraband.se/pages/om-oss<br/><br/>"
        "## Brands<br/>"
        "- Hirsch (Austria, est. 1765)<br/>"
        "- Fluco (Germany, est. 1952)<br/>"
        "- Colareb (Italy, handmade vegan)<br/>"
        "- bandberra (sailcloth and premium nylon)<br/><br/>"
        "## Contact<br/>"
        "- Email: support@baraband.se<br/>"
        "- Address: Box 202, 191 23 Sollentuna, Sweden"
    )
    e.append(Paragraph(llms_content, s['CodeBlock']))

    steps_2b = [
        'Save the page. The URL will be: <b>baraband.se/pages/llms-txt</b>',
        'Ideally, set up a redirect so <b>baraband.se/llms.txt</b> points to this page. In Shopify Admin → Settings → Navigation → URL Redirects, add: /llms.txt → /pages/llms-txt',
    ]
    for i, step in enumerate(steps_2b, 4):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))
    e.append(Paragraph("AI crawlers will now find structured guidance about your site.", s['Impact']))

    # ── STEP 3 ──
    e.append(PageBreak())
    e.append(Paragraph("Step 3: Clean Up the Om Oss (About) Page", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> Your current About page contains 500+ Swedish city/municipality links — a legacy "
        "SEO tactic that confuses AI crawlers and dilutes your brand narrative. AI systems reading "
        "this page cannot understand what BaraBand is about because the brand information is buried "
        "under hundreds of geographic links.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 1 hour &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Easy &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_3 = [
        'In Shopify Admin, go to <b>Pages</b> and open your "Om oss" or "Kontakta oss" page',
        "<b>Delete ALL city/municipality links</b> from the page content (the entire list of 500+ city names)",
        "Replace the page content with a clean brand narrative. Suggested content:",
    ]
    for i, step in enumerate(steps_3, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))

    about_content = (
        "<b>Om BaraBand</b><br/><br/>"
        "BaraBand foeddes ur en enkel idee: att ge klockentusiaster i Sverige<br/>"
        "tillgaang till kvalitetsarmband till rimliga priser.<br/><br/>"
        "Vi samarbetar med Europas ledande tillverkare:<br/>"
        "- Hirsch (Oesterrike, grundat 1765) — premiumlaeder och performance<br/>"
        "- Fluco (Tyskland, grundat 1952) — handgjorda laederarmband<br/>"
        "- Colareb (Italien) — veganska armband av innovativa fibrer<br/><br/>"
        "Vi erbjuder 60 dagars oeppet koep och fri frakt oever 350 kr.<br/><br/>"
        "<b>Kontakt:</b> support@baraband.se<br/>"
        "<b>Adress:</b> Box 202, 191 23 Sollentuna<br/>"
        "<b>Org.nr:</b> [ditt organisationsnummer]"
    )
    e.append(Paragraph(about_content, s['CodeBlock']))

    e.append(Paragraph("<b>4.</b> Save the page.", s['Instruction']))
    e.append(Paragraph("AI crawlers can now extract a clear, factual summary of your brand in 2 sentences.", s['Impact']))

    # ── STEP 4 ──
    e.append(Paragraph("Step 4: Add Author Bio for Blog Posts", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> All 6 blog posts are attributed to \"Jacob .\" with no biography or credentials. "
        "AI search platforms like Perplexity and Google require named authors with expertise signals "
        "before they will cite content. Anonymous content receives minimal citation consideration.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 1 hour &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Easy &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_4 = [
        'Create a new page in Shopify: <b>Pages → Add page</b>. Title: "Om Jacob" or "Meet the Founder"',
        "Write 3-4 sentences: Jacob's watch interest/background, when BaraBand was founded, "
        "the curation philosophy (why these specific European brands), and how many products have been curated. Add a photo.",
        'Example text: "Jacob aer grundare av BaraBand och har varit klockentusiast i oever [X] aar. '
        'Han startade BaraBand foer att goera europeiska kvalitetsarmband tillgaengliga foer svenska '
        'klockentusiaster. Idag kurerar han ett sortiment av oever 200 armband fraan Hirsch, Fluco, '
        'Colareb och andra ledande tillverkare."',
        "In your Shopify blog settings, update the author name from \"Jacob .\" to the full name with a link to the bio page.",
    ]
    for i, step in enumerate(steps_4, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))
    e.append(Paragraph("Every blog post now carries author credibility — a core signal for Perplexity and Google E-E-A-T.", s['Impact']))

    # ── STEP 5 ──
    e.append(Paragraph("Step 5: Add Organisationsnummer to Footer", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> Swedish e-commerce consumers expect to see the company registration number. "
        "Its absence is a trust gap, especially for first-time buyers.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 10 minutes &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Very Easy &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_5 = [
        'Go to <b>Online Store → Themes → Customize</b>',
        "Navigate to the <b>Footer</b> section",
        'Add your Org.nr to the footer text, e.g.: "BaraBand.se | Org.nr: XXXXXX-XXXX"',
        "Save.",
    ]
    for i, step in enumerate(steps_5, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))

    # ── STEP 6 ──
    e.append(Paragraph("Step 6: Submit Sitemap to Bing Webmaster Tools", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> Bing Copilot (Microsoft's AI assistant) uses Bing's index. If your site isn't "
        "properly submitted to Bing, Copilot won't recommend your products. This takes 20 minutes "
        "and has permanent benefits.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 20 minutes &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Easy &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_6 = [
        'Go to <b>bing.com/webmasters</b> and sign in with a Microsoft account',
        'Click <b>"Add Site"</b> and enter: <b>https://baraband.se</b>',
        "Choose a verification method (DNS verification is recommended — add a CNAME record to your domain)",
        'Once verified, go to <b>Sitemaps</b> and submit: <b>https://baraband.se/sitemap.xml</b>',
        "Bing will begin crawling and indexing your pages for Copilot recommendations.",
    ]
    for i, step in enumerate(steps_6, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))

    # ── STEP 7 ──
    e.append(Paragraph("Step 7: Add og:locale Meta Tag", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> AI systems and social platforms need to know your site's language. Without "
        "an explicit locale tag, they may not correctly identify your content as Swedish.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 15 minutes &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Requires theme code edit &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_7 = [
        'Go to <b>Online Store → Themes → Actions → Edit Code</b>',
        'Open the file <b>theme.liquid</b> (in the Layout folder)',
        'Find the <b>&lt;head&gt;</b> section and add this line after the existing meta tags:',
    ]
    for i, step in enumerate(steps_7, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))
    e.append(Paragraph('&lt;meta property="og:locale" content="sv_SE"&gt;', s['CodeBlock']))
    e.append(Paragraph("<b>4.</b> Also verify that the &lt;html&gt; tag has <b>lang=\"sv\"</b>. If not, change "
        '&lt;html&gt; to &lt;html lang="sv"&gt;.', s['Instruction']))
    e.append(Paragraph("<b>5.</b> Save the file.", s['Instruction']))

    e.append(PageBreak())

    # ═══════════════════════════════════════════════════
    # PHASE 2
    # ═══════════════════════════════════════════════════
    e.append(Paragraph("Phase 2: Content & Schema (Weeks 3-6)", s['Phase']))
    e.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    e.append(Paragraph("These steps build the content and structured data that AI platforms need to cite and "
        "recommend your products. They require more time but deliver significant score improvements.", s['Body']))

    # ── STEP 8 ──
    e.append(Paragraph("Step 8: Create a FAQ Page with Schema Markup", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> FAQ pages are the most reliably cited content format by AI systems. When someone "
        "asks ChatGPT or Perplexity \"how do I measure my watch strap?\", the answer comes from "
        "FAQ content. You currently have no FAQ page — both /pages/faq and /pages/vanliga-fragor "
        "return errors.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 3-4 hours &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Medium &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_8 = [
        'Create a new page: <b>Pages → Add page</b>. Title: <b>"Vanliga fragor"</b> (URL: /pages/vanliga-fragor)',
        "Write 10-15 questions and answers. Here are the recommended Q&As:",
    ]
    for i, step in enumerate(steps_8, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))

    faq_data = [
        ["Question", "Answer Key Points"],
        ["Hur maeter jag mitt klockarmband?", "Lugbredd = avstaand mellan lugs. Maet med skjutmaatt. Vanliga: 18, 20, 22mm"],
        ["Vad aer snabbkoppling (Quick Release)?", "Spaennteknik som goer det enkelt att byta armband utan verktyg"],
        ["Vilket armband passar Apple Watch?", "38-41mm boett = 20mm band. 42-49mm boett = 22mm band. Adapter behoevs"],
        ["Skillnad mellan laeder och gummi?", "Laeder: klassiskt, undvik vatten. FKM-gummi: vattentaaligt, sport"],
        ["Vilket armband passar Seiko 5?", "De flesta Seiko 5-modeller har 22mm lugbredd"],
        ["Hur laang tid tar leveransen?", "1-3 arbetsdagar via PostNord inom Sverige"],
        ["Vad kostar returen?", "39 kr, 60 dagars oeppet koep, oanvaend i originalfoerpackning"],
        ["Vad aer NATO-armband?", "Genomdraget nylonarmband med militaert ursprung, tunn och talig"],
        ["Hur skoeter jag laederarmband?", "Undvik vatten, konditionera regelmaessigt, rotera mellan armband"],
        ["Vad aer FKM-gummi?", "Fluorelastomer — svettresistent, UV-taaligt, perfekt foer dykning och traening"],
    ]
    e.append(make_table(faq_data, [180, 330]))
    e.append(Spacer(1, 6))
    e.append(Paragraph("<b>3.</b> Write each answer as 2-3 sentences. Be specific and factual — not marketing copy.", s['Instruction']))
    e.append(Paragraph("<b>4.</b> Add FAQ schema markup. If your Shopify theme supports custom code per page, "
        "add the FAQPage JSON-LD block (provided in the full audit report) to this page. "
        "Alternatively, install the \"JSON-LD for SEO\" Shopify app which can auto-generate FAQ schema.", s['Instruction']))
    e.append(Paragraph("This single page can capture 10-15 AI search queries and drive recurring citation traffic.", s['Impact']))

    # ── STEP 9 ──
    e.append(Paragraph("Step 9: Add BreadcrumbList Schema", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> Collection pages currently have zero structured data. Adding BreadcrumbList "
        "enables breadcrumb path display in Google search results and helps AI systems understand "
        "your site's hierarchy.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 2 hours &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Requires theme code edit &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    e.append(Paragraph("This step requires editing your Shopify theme code. If you are not comfortable "
        "with code, ask your web developer to do this.", s['Note']))
    steps_9 = [
        'Go to <b>Online Store → Themes → Actions → Edit Code</b>',
        'Open <b>product.liquid</b> (or main-product.liquid in the Sections folder)',
        "Add the following code just before the closing &lt;/body&gt; or at the bottom of the template:",
    ]
    for i, step in enumerate(steps_9, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))

    breadcrumb_code = (
        '&lt;script type="application/ld+json"&gt;<br/>'
        '{<br/>'
        '&nbsp;&nbsp;"@context": "https://schema.org",<br/>'
        '&nbsp;&nbsp;"@type": "BreadcrumbList",<br/>'
        '&nbsp;&nbsp;"itemListElement": [<br/>'
        '&nbsp;&nbsp;&nbsp;&nbsp;{"@type":"ListItem","position":1,"name":"Hem",<br/>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"item":"{{ shop.url }}"},<br/>'
        '&nbsp;&nbsp;&nbsp;&nbsp;{"@type":"ListItem","position":2,<br/>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"name":"{{ collection.title | escape }}",<br/>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"item":"{{ shop.url }}/collections/{{ collection.handle }}"},<br/>'
        '&nbsp;&nbsp;&nbsp;&nbsp;{"@type":"ListItem","position":3,<br/>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"name":"{{ product.title | escape }}",<br/>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"item":"{{ shop.url }}/products/{{ product.handle }}"}<br/>'
        '&nbsp;&nbsp;]<br/>'
        '}<br/>'
        '&lt;/script&gt;'
    )
    e.append(Paragraph(breadcrumb_code, s['CodeBlock']))
    e.append(Paragraph("<b>4.</b> Repeat for <b>collection.liquid</b> (with only 2 items: Hem and the collection name).", s['Instruction']))
    e.append(Paragraph("<b>5.</b> Save both files and verify with Google's Rich Results Test.", s['Instruction']))

    # ── STEP 10 ──
    e.append(Paragraph("Step 10: Enhance Organization Schema", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> Your current Organization schema only has name, URL, logo, and one Instagram link. "
        "AI systems need more context: what you sell, where you are located, how to contact you, "
        "and what market you serve.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 1 hour &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Requires theme code edit &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    e.append(Paragraph("The enhanced Organization JSON-LD schema is provided in the full audit report "
        "(GEO-AUDIT-REPORT.md). Have your web developer replace the existing Organization "
        "schema block in theme.liquid with the enhanced version that includes: description, "
        "areaServed (SE), contactPoint with email, PostalAddress for Sollentuna, and sameAs "
        "with all social profiles.", s['Instruction']))

    # ── STEP 11 ──
    e.append(PageBreak())
    e.append(Paragraph("Step 11: Publish a Material Comparison Guide", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> This is the single most impactful content piece you can create. A comprehensive "
        "guide comparing watch strap materials serves every AI platform simultaneously: Google AIO "
        "(table extraction), ChatGPT (informational citation), Perplexity (research source), and "
        "Bing Copilot (featured content).", s['Body']))
    e.append(Paragraph("<b>Time:</b> 4 hours &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Medium (writing) &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_11 = [
        'Create a new blog post in <b>Blog posts → Add blog post</b>',
        '<b>Title:</b> "Komplett guide: Vilket klockarmband passar dig? Jaemfoerelse av material"',
        "<b>Author:</b> Jacob (with full name, linked to author bio page)",
        "<b>Structure the article with these H2 headings</b> (minimum 1,000 words total):",
    ]
    for i, step in enumerate(steps_11, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))

    guide_structure = [
        ["Section (H2 Heading)", "Content to Include"],
        ["Laeder — klassiskt och tidloest", "Full grain vs top grain, care tips, when to use, Hirsch/Fluco examples"],
        ["FKM Gummi — foer sport och vatten", "What FKM is, sweat/UV resistance, diving suitability, price range"],
        ["Nylon (NATO) — taaligt och prisvart", "Military origins, washing instructions, casual wear, price advantage"],
        ["Sailcloth — det baesta av tvaa varldar", "What it is, durability, bandberra range, when to choose it"],
        ["Mesh (naetarmband) — elegant och justerbart", "Infinite adjustment, dress watch pairing, comfort"],
        ["Jaemfoerelsetabell", "TABLE: Material | Hallbarhet | Komfort | Vatten | Prisintervall"],
        ["Vanliga fragor", "3-5 Q&As about material choice"],
    ]
    e.append(make_table(guide_structure, [180, 330]))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>5.</b> Include a comparison table — AI systems love extracting tables for featured snippets.", s['Instruction']))
    e.append(Paragraph("<b>6.</b> Link to relevant collection pages from each section (e.g., the leather section links to /collections/lader).", s['Instruction']))
    e.append(Paragraph("<b>7.</b> Publish and share on Instagram.", s['Instruction']))
    e.append(Paragraph("This single article can rank for 10+ search queries and become your most-cited page by AI systems.", s['Impact']))

    # ── STEP 12 ──
    e.append(Paragraph("Step 12: Register on Trustpilot", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> A second review source strengthens trust signals. Trustpilot ratings appear "
        "directly in Google search results and are indexed by all AI platforms.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 2 hours &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Easy &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free (basic plan)", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_12 = [
        "Go to business.trustpilot.com and create a free business account for baraband.se",
        "Verify your domain ownership",
        "Set up automatic review invitation emails (similar to Judge.me but for Trustpilot)",
        "Add the Trustpilot widget to your homepage footer (embed code provided by Trustpilot)",
        "Target: 20+ reviews within 90 days to establish a credible rating",
    ]
    for i, step in enumerate(steps_12, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))

    # ── STEP 13 ──
    e.append(Paragraph("Step 13: Install Microsoft Channel on Shopify", s['StepTitle']))
    e.append(Paragraph("<b>Why:</b> This submits all 204 products to Bing Shopping and Microsoft Merchant Center, "
        "making them available for Bing Copilot product recommendations.", s['Body']))
    e.append(Paragraph("<b>Time:</b> 1 hour &nbsp;&nbsp;|&nbsp;&nbsp;<b>Difficulty:</b> Easy &nbsp;&nbsp;|&nbsp;&nbsp;<b>Cost:</b> Free", s['Body']))
    e.append(Spacer(1, 4))
    e.append(Paragraph("<b>Instructions:</b>", s['BodyBold']))
    steps_13 = [
        'In Shopify Admin, go to <b>Apps → Search "Microsoft Channel"</b>',
        "Install the official Microsoft Channel app by Microsoft Corporation",
        "Connect your Microsoft account and verify your store",
        "The app will automatically sync your product catalog to Microsoft Merchant Center",
        "Products will appear in Bing Shopping results and Bing Copilot recommendations",
    ]
    for i, step in enumerate(steps_13, 1):
        e.append(Paragraph(f"<b>{i}.</b> {step}", s['Instruction']))

    e.append(PageBreak())

    # ═══════════════════════════════════════════════════
    # PHASE 3
    # ═══════════════════════════════════════════════════
    e.append(Paragraph("Phase 3: Growth Content (Month 2-3)", s['Phase']))
    e.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    e.append(Paragraph("These steps deepen your content authority and capture more AI search queries.", s['Body']))

    # ── STEP 14 ──
    e.append(Paragraph("Step 14: Reformat Size Guide as Q&A", s['StepTitle']))
    e.append(Paragraph("Your storleksguide is already your strongest content asset. Reformatting it with "
        "question-based H2 headings makes it directly extractable by Google AI Overviews.", s['Body']))
    e.append(Paragraph("<b>Action:</b> Edit /pages/storleksguide. Change section headers to questions: "
        '"Hur maeter jag min lugbredd?", "Vad aer skillnaden mellan lugbredd och bandbredd?", '
        '"Hur installerar jag ett snabbkopplingsarmband?". Keep the existing content but restructure '
        "it as answers under each question heading.", s['Instruction']))

    # ── STEP 15 ──
    e.append(Paragraph("Step 15: Create Apple Watch Compatibility Page", s['StepTitle']))
    e.append(Paragraph("Apple Watch accessory queries have very high AI Overview frequency. A dedicated "
        "compatibility page captures these searches.", s['Body']))
    e.append(Paragraph("<b>Action:</b> Create a blog post or page covering: which Apple Watch Series uses which "
        "band width, adapter requirements, recommended materials for Apple Watch (avoid leather "
        "with sweat), and your compatible products with direct links.", s['Instruction']))

    # ── STEP 16 ──
    e.append(Paragraph("Step 16: Create Brand Heritage Pages", s['StepTitle']))
    e.append(Paragraph("Hirsch, Fluco, and Colareb have existing brand recognition in AI training data. "
        "Creating detailed brand pages on your site creates citation pathways.", s['Body']))
    e.append(Paragraph("<b>Action:</b> Create 3 blog posts (600-800 words each):", s['Instruction']))
    brand_pages = [
        ['Brand Page', 'Key Content'],
        ['Hirsch klockarmband', '260-year history, Austrian craftsmanship, material innovations, your Hirsch range'],
        ['Fluco klockarmband', '70+ year history, German handcraft, what makes Fluco different'],
        ['Colareb veganska armband', 'Italian tradition, 4 vegan fiber types, sustainability angle'],
    ]
    e.append(make_table(brand_pages, [160, 350]))

    # ── STEP 17 ──
    e.append(Paragraph("Step 17: Source and Add GTINs to Products", s['StepTitle']))
    e.append(Paragraph("Both Google Merchant Center and Microsoft Merchant Center require GTINs (EAN codes) "
        "for full Shopping integration.", s['Body']))
    e.append(Paragraph("<b>Action:</b> Contact your Hirsch and Fluco distributors and request manufacturer EAN "
        "codes for each product. Add these to Shopify under each product's metafields. "
        "The Google and Microsoft Channel apps will automatically include them in your feed.", s['Instruction']))

    e.append(PageBreak())

    # ═══════════════════════════════════════════════════
    # PHASE 4
    # ═══════════════════════════════════════════════════
    e.append(Paragraph("Phase 4: Authority Building (Month 3+)", s['Phase']))
    e.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    e.append(Paragraph("These are ongoing strategic actions that build long-term brand authority in AI systems. "
        "Brand mentions are 3x more strongly correlated with AI citations than backlinks.", s['Body']))

    # ── STEP 18 ──
    e.append(Paragraph("Step 18: Build Organic Reddit Presence", s['StepTitle']))
    e.append(Paragraph("Reddit discussions are primary training data for AI models. A single popular thread "
        "mentioning your brand persists in AI training data for years.", s['Body']))
    e.append(Paragraph("<b>Action:</b> Create a Reddit account. Join r/Watches, r/watchstraps, and r/Watchbands. "
        "Participate authentically — share knowledge about strap materials, sizing tips, and brand "
        "comparisons. When relevant, mention BaraBand as a source. Never spam.", s['Instruction']))
    e.append(Paragraph("Do NOT post promotional content. Focus on being helpful. Mention BaraBand naturally "
        "when someone asks where to buy quality straps in Sweden/Europe.", s['Warning']))

    # ── STEP 19 ──
    e.append(Paragraph("Step 19: Pursue YouTube Coverage", s['StepTitle']))
    e.append(Paragraph("Watch strap review content on YouTube feeds directly into AI training data.", s['Body']))
    e.append(Paragraph("<b>Action:</b> Identify 3-5 Swedish or international watch YouTube creators (look for channels "
        "reviewing watch straps or affordable watch accessories). Send them free product samples "
        "in exchange for honest reviews. Even a 5-minute review creates lasting AI training data.", s['Instruction']))

    # ── STEP 20 ──
    e.append(Paragraph("Step 20: Seek Press / Editorial Mentions", s['StepTitle']))
    e.append(Paragraph("A single article in a Swedish lifestyle or watch publication linking to baraband.se "
        "dramatically increases Perplexity's willingness to cite your domain.", s['Body']))
    e.append(Paragraph("<b>Action:</b> Reach out to Swedish lifestyle blogs, watch enthusiast sites, or publications "
        "like Klockor &amp; Pennor. Pitch a story angle: \"Swedish retailer brings 260-year-old Austrian "
        "watchstrap tradition to Scandinavia\" or \"The rise of vegan watch straps — Italian innovation "
        "meets Swedish e-commerce\".", s['Instruction']))

    e.append(PageBreak())

    # ═══════════════════════════════════════════════════
    # PROGRESS TRACKER
    # ═══════════════════════════════════════════════════
    e.append(Paragraph("Progress Tracker", s['Phase']))
    e.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    e.append(Paragraph("Use this checklist to track your progress. Check off each step as you complete it.", s['Body']))
    e.append(Spacer(1, 8))

    tracker = [
        ["#", "Action", "Time", "Done"],
        ["1", "Install Judge.me review app", "2 hrs", ""],
        ["2", "Create llms.txt file", "30 min", ""],
        ["3", "Clean up Om Oss page (remove city links)", "1 hr", ""],
        ["4", "Add author bio for Jacob", "1 hr", ""],
        ["5", "Add Org.nr to footer", "10 min", ""],
        ["6", "Submit sitemap to Bing Webmaster Tools", "20 min", ""],
        ["7", "Add og:locale meta tag", "15 min", ""],
        ["8", "Create FAQ page with 10-15 Q&As", "3-4 hrs", ""],
        ["9", "Add BreadcrumbList schema to theme", "2 hrs", ""],
        ["10", "Enhance Organization schema", "1 hr", ""],
        ["11", "Publish material comparison guide", "4 hrs", ""],
        ["12", "Register on Trustpilot", "2 hrs", ""],
        ["13", "Install Microsoft Channel on Shopify", "1 hr", ""],
        ["14", "Reformat size guide as Q&A", "2 hrs", ""],
        ["15", "Create Apple Watch compatibility page", "3 hrs", ""],
        ["16", "Create 3 brand heritage pages", "6 hrs", ""],
        ["17", "Source and add GTINs to products", "2 hrs", ""],
        ["18", "Build Reddit presence (ongoing)", "Ongoing", ""],
        ["19", "Pursue YouTube coverage", "Ongoing", ""],
        ["20", "Seek press / editorial mentions", "Ongoing", ""],
    ]
    t = Table(tracker, colWidths=[30, 300, 60, 50])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (3, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        # Highlight phase separators
        ('BACKGROUND', (0, 8), (-1, 8), MEDIUM_BG),
        ('FONTNAME', (0, 8), (-1, 8), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 14), (-1, 14), MEDIUM_BG),
        ('FONTNAME', (0, 14), (-1, 14), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 18), (-1, 18), MEDIUM_BG),
        ('FONTNAME', (0, 18), (-1, 18), 'Helvetica-Bold'),
    ]))
    e.append(t)

    e.append(Spacer(1, 20))
    e.append(Paragraph("<b>Expected Results:</b>", s['BodyBold']))
    results = [
        ["Phase", "Timeline", "Expected GEO Score"],
        ["Starting point", "Now", "39 / 100"],
        ["After Phase 1 (Quick Wins)", "Week 2", "~50 / 100"],
        ["After Phase 2 (Content & Schema)", "Week 6", "~62 / 100"],
        ["After Phase 3 (Growth Content)", "Month 3", "~70 / 100"],
        ["After Phase 4 (Authority)", "Month 6+", "80+ / 100"],
    ]
    e.append(make_table(results, [200, 100, 140]))

    e.append(Spacer(1, 20))
    e.append(HRFlowable(width="100%", thickness=0.5, color=lightgrey, spaceAfter=8))
    e.append(Paragraph(
        "This guide was generated by the GEO-SEO Analysis Tool based on a comprehensive "
        "audit of baraband.se conducted on February 24, 2026. For questions or assistance "
        "with implementation, contact your GEO consultant.",
        s['Small']))

    # BUILD
    doc.build(e, onFirstPage=header_footer, onLaterPages=header_footer)
    return "GEO-GUIDE-BaraBand.pdf"

if __name__ == "__main__":
    result = generate()
    print(f"Guide generated: {result}")
