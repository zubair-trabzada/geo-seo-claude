import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'
import type { ScoreBreakdown, AuditData, CompetitorSnapshot } from '@/lib/types'

// ── GET /api/audits?clientId=xxx ──────────────────────────────────────────────
// Returns audits for a specific client.
// Admin can access any client; client users can only access their own.
export async function GET(req: NextRequest): Promise<NextResponse> {
  const session = await getServerSession(authOptions)
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const clientId = req.nextUrl.searchParams.get('clientId')
  if (!clientId) {
    return NextResponse.json({ error: 'clientId query param required' }, { status: 400 })
  }

  // Client users can only see their own audits
  if (session.user.role === 'client' && session.user.clientId !== clientId) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  try {
    const audits = await prisma.audit.findMany({
      where: { clientId },
      orderBy: { timestamp: 'desc' },
      include: {
        recommendations: {
          orderBy: [{ priority: 'asc' }, { status: 'asc' }],
        },
      },
    })

    // Parse JSON fields before returning
    const parsed = audits.map((a) => ({
      ...a,
      scores: JSON.parse(a.scores) as ScoreBreakdown,
      rawData: JSON.parse(a.rawData) as AuditData,
      competitors: a.competitors
        ? (JSON.parse(a.competitors) as CompetitorSnapshot[])
        : null,
    }))

    return NextResponse.json(parsed)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal server error'
    console.error('GET /api/audits error:', err)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

// ── POST /api/audits ──────────────────────────────────────────────────────────
// Stores a completed audit result. Called by FastAPI callback or internally.
// Admin only.
export async function POST(req: NextRequest): Promise<NextResponse> {
  const session = await getServerSession(authOptions)
  if (!session || session.user.role !== 'admin') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const body = (await req.json()) as {
      clientId?: string
      geoScore?: number
      scores?: ScoreBreakdown
      rawData?: AuditData
      competitors?: CompetitorSnapshot[]
      isBaseline?: boolean
      recommendations?: Array<{
        category: string
        priority: number
        title: string
        description: string
        effort: string
        impact: string
      }>
    }

    const {
      clientId,
      geoScore,
      scores,
      rawData,
      competitors,
      isBaseline = false,
      recommendations = [],
    } = body

    if (!clientId || geoScore === undefined || !scores || !rawData) {
      return NextResponse.json(
        { error: 'Missing required fields: clientId, geoScore, scores, rawData' },
        { status: 400 },
      )
    }

    // Verify client exists
    const client = await prisma.client.findUnique({ where: { id: clientId } })
    if (!client) {
      return NextResponse.json({ error: 'Client not found' }, { status: 404 })
    }

    const audit = await prisma.audit.create({
      data: {
        clientId,
        geoScore,
        isBaseline,
        scores: JSON.stringify(scores),
        rawData: JSON.stringify(rawData),
        competitors: competitors ? JSON.stringify(competitors) : null,
        recommendations: {
          create: recommendations.map((r) => ({
            clientId,
            category: r.category,
            priority: r.priority,
            title: r.title,
            description: r.description,
            effort: r.effort,
            impact: r.impact,
            status: 'pending',
          })),
        },
      },
      include: { recommendations: true },
    })

    // Create score-drop alert if score declined vs previous audit
    try {
      const previousAudit = await prisma.audit.findFirst({
        where: { clientId, id: { not: audit.id } },
        orderBy: { timestamp: 'desc' },
        select: { geoScore: true },
      })

      if (previousAudit && geoScore < previousAudit.geoScore - 5) {
        await prisma.alert.create({
          data: {
            clientId,
            type: 'score_drop',
            message: `GEO score dropped from ${previousAudit.geoScore} to ${geoScore} for ${client.name}.`,
          },
        })
      }
    } catch (alertErr) {
      console.warn('Alert creation failed (non-fatal):', alertErr)
    }

    return NextResponse.json(
      { id: audit.id, geoScore: audit.geoScore },
      { status: 201 },
    )
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal server error'
    console.error('POST /api/audits error:', err)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
