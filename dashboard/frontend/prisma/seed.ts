import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcryptjs'

const prisma = new PrismaClient()

async function main() {
  console.log('Seeding database...')

  // Clean up existing data (order matters for FK constraints)
  await prisma.recommendation.deleteMany()
  await prisma.alert.deleteMany()
  await prisma.audit.deleteMany()
  await prisma.user.deleteMany()
  await prisma.client.deleteMany()

  // ── Admin user (no client) ────────────────────────────────────────────────
  const adminHash = await bcrypt.hash('admin123', 12)
  const admin = await prisma.user.create({
    data: {
      email: 'admin@geodashboard.local',
      passwordHash: adminHash,
      role: 'admin',
    },
  })
  console.log(`Created admin user: ${admin.email}`)

  // ── Test client: BaraBand ─────────────────────────────────────────────────
  const client = await prisma.client.create({
    data: {
      name: 'BaraBand',
      websiteUrl: 'https://www.baraband.se',
      isActive: true,
    },
  })
  console.log(`Created client: ${client.name}`)

  // ── Client user ───────────────────────────────────────────────────────────
  const clientHash = await bcrypt.hash('client123', 12)
  const clientUser = await prisma.user.create({
    data: {
      email: 'baraband@geodashboard.local',
      passwordHash: clientHash,
      role: 'client',
      clientId: client.id,
    },
  })
  console.log(`Created client user: ${clientUser.email}`)

  // ── Seeded audit (baseline data from geo-audit-data.json) ─────────────────
  const scores = {
    ai_citability: 28,
    brand_authority: 42,
    content_eeat: 35,
    technical: 55,
    schema: 20,
    platform_optimization: 15,
  }

  const rawData = {
    url: 'https://www.baraband.se',
    brand_name: 'BaraBand',
    date: '2026-02-26',
    geo_score: 39,
    scores,
    platforms: {
      'Google AI Overviews': 20,
      ChatGPT: 35,
      Perplexity: 45,
      'Bing Copilot': 55,
    },
    executive_summary:
      'BaraBand scores 39/100 on GEO readiness. The site has moderate technical health but critically lacks structured data, AI-friendly content formatting, and brand authority signals needed to appear in AI-generated answers. Immediate wins are available through schema markup, FAQ content, and Wikipedia/Wikidata presence.',
    findings: [
      {
        severity: 'critical',
        title: 'No Schema Markup Detected',
        description:
          'The site has no JSON-LD or microdata schema. This is the single highest-impact fix for AI citation readiness.',
      },
      {
        severity: 'critical',
        title: 'Missing Wikipedia / Wikidata Presence',
        description:
          'AI systems heavily weight Wikipedia and Wikidata for brand authority. BaraBand has no presence on either platform.',
      },
      {
        severity: 'high',
        title: 'No FAQ or Q&A Content',
        description:
          'AI Overviews preferentially cite pages that directly answer questions. The site lacks dedicated FAQ sections.',
      },
      {
        severity: 'high',
        title: 'Thin Author Bio & E-E-A-T Signals',
        description:
          'Content lacks explicit authorship, credentials, and expertise indicators required for E-E-A-T scoring.',
      },
      {
        severity: 'medium',
        title: 'Limited Backlink Profile',
        description:
          'Domain authority is low. More authoritative inbound links would improve AI citation likelihood.',
      },
    ],
    quick_wins: [
      'Add Organization + Product JSON-LD schema to all pages',
      'Create a dedicated FAQ page answering the top 10 customer questions',
      'Add author bios with credentials to all editorial content',
      'Submit site to Google Search Console and verify',
      'Create and verify a Google Business Profile',
    ],
    medium_term: [
      'Build Wikipedia article for the brand',
      'Create Wikidata entity for BaraBand',
      'Publish 5 long-form guides targeting informational queries',
      'Earn 20+ backlinks from music industry publications',
      'Implement BreadcrumbList and SiteLinksSearchBox schema',
    ],
    strategic: [
      'Develop a thought-leadership content programme',
      'Pursue HARO / journalist outreach for brand mentions',
      'Partner with music schools and academies for co-citation',
      'Build a brand mentions monitoring workflow',
    ],
    crawler_access: {
      GPTBot: 'allowed',
      ClaudeBot: 'allowed',
      PerplexityBot: 'unknown',
      BingBot: 'allowed',
      GoogleBot: 'allowed',
    },
  }

  const recommendations = [
    {
      category: 'schema',
      priority: 1,
      title: 'Implement JSON-LD Organization Schema',
      description:
        'Add a JSON-LD Organization schema block to every page, including name, url, logo, sameAs (social profiles), and contactPoint. This is the single fastest win for AI citation readiness.',
      effort: 'low',
      impact: 'high',
      status: 'pending',
    },
    {
      category: 'schema',
      priority: 1,
      title: 'Add Product / Offer Schema to Product Pages',
      description:
        'Each product page should include Product schema with name, description, sku, offers, and aggregateRating where reviews exist.',
      effort: 'medium',
      impact: 'high',
      status: 'pending',
    },
    {
      category: 'content_eeat',
      priority: 1,
      title: 'Create FAQ Page Targeting Top Questions',
      description:
        'Build a standalone /faq page with at least 15 Q&A pairs covering the most common customer questions. Use FAQPage schema. AI systems preferentially cite structured Q&A content.',
      effort: 'low',
      impact: 'high',
      status: 'pending',
    },
    {
      category: 'brand_authority',
      priority: 2,
      title: 'Create Wikipedia Article for BaraBand',
      description:
        'Draft and submit a Wikipedia article meeting notability guidelines. Cite published reviews and industry coverage. A Wikipedia presence is one of the strongest AI authority signals.',
      effort: 'high',
      impact: 'high',
      status: 'pending',
    },
    {
      category: 'brand_authority',
      priority: 2,
      title: 'Create Wikidata Entity',
      description:
        'Add a Wikidata item for BaraBand linked to the Wikipedia article. Include identifiers for major music databases (MusicBrainz, Discogs). Used by multiple AI systems for entity resolution.',
      effort: 'medium',
      impact: 'medium',
      status: 'pending',
    },
    {
      category: 'content_eeat',
      priority: 2,
      title: 'Add Author Bios with Credentials',
      description:
        'Every piece of editorial content should display a named author with a short bio, credentials, and a link to their profile page. Implement Person schema on author pages.',
      effort: 'low',
      impact: 'medium',
      status: 'pending',
    },
    {
      category: 'technical',
      priority: 2,
      title: 'Verify Google Search Console & Submit Sitemap',
      description:
        'Ensure GSC is verified and an up-to-date XML sitemap is submitted. This ensures timely indexing of new content by Google and Bing.',
      effort: 'low',
      impact: 'medium',
      status: 'pending',
    },
    {
      category: 'platform_optimization',
      priority: 3,
      title: 'Optimise robots.txt for AI Crawlers',
      description:
        'Review robots.txt to ensure GPTBot, ClaudeBot, PerplexityBot, and GoogleBot-Extended are explicitly allowed. Block only private/duplicate content paths.',
      effort: 'low',
      impact: 'medium',
      status: 'pending',
    },
  ]

  const audit = await prisma.audit.create({
    data: {
      clientId: client.id,
      isBaseline: true,
      geoScore: 39,
      scores: JSON.stringify(scores),
      rawData: JSON.stringify(rawData),
      recommendations: {
        create: recommendations.map((r) => ({
          ...r,
          clientId: client.id,
        })),
      },
    },
  })
  console.log(`Created baseline audit: ${audit.id} (score: ${audit.geoScore})`)

  // ── Seed an alert ──────────────────────────────────────────────────────────
  await prisma.alert.create({
    data: {
      clientId: client.id,
      type: 'milestone',
      message: 'Baseline GEO audit completed for BaraBand. Score: 39/100.',
      isRead: false,
    },
  })
  console.log('Created baseline alert')

  console.log('Seeding complete.')
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
