import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'
import bcrypt from 'bcryptjs'
import type { ClientWithStats } from '@/lib/types'

// ── GET /api/clients ──────────────────────────────────────────────────────────
// Returns all clients with latest audit score. Admin only.
export async function GET(_req: NextRequest): Promise<NextResponse> {
  const session = await getServerSession(authOptions)
  if (!session || session.user.role !== 'admin') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const clients = await prisma.client.findMany({
      where: { isActive: true },
      orderBy: { createdAt: 'desc' },
      include: {
        audits: {
          orderBy: { timestamp: 'desc' },
          take: 2,
          select: { id: true, geoScore: true, timestamp: true },
        },
        _count: { select: { audits: true } },
      },
    })

    const result: ClientWithStats[] = clients.map((c) => {
      const [latest, previous] = c.audits
      const latestScore = latest?.geoScore ?? null
      const previousScore = previous?.geoScore ?? null
      const scoreDelta =
        latestScore !== null && previousScore !== null
          ? Math.round((latestScore - previousScore) * 10) / 10
          : null

      return {
        id: c.id,
        name: c.name,
        websiteUrl: c.websiteUrl,
        createdAt: c.createdAt,
        latestScore,
        previousScore,
        scoreDelta,
        lastAuditAt: latest?.timestamp ?? null,
        auditCount: c._count.audits,
      }
    })

    return NextResponse.json(result)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal server error'
    console.error('GET /api/clients error:', err)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

// ── POST /api/clients ─────────────────────────────────────────────────────────
// Creates a new client + user account, then triggers a baseline audit.
// Admin only.
export async function POST(req: NextRequest): Promise<NextResponse> {
  const session = await getServerSession(authOptions)
  if (!session || session.user.role !== 'admin') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const body = (await req.json()) as {
      name?: string
      websiteUrl?: string
      email?: string
      password?: string
      competitors?: string[]
    }

    const { name, websiteUrl, email, password, competitors = [] } = body

    if (!name || !websiteUrl || !email || !password) {
      return NextResponse.json(
        { error: 'Missing required fields: name, websiteUrl, email, password' },
        { status: 400 },
      )
    }

    // Check if user email already exists
    const existingUser = await prisma.user.findUnique({
      where: { email: email.toLowerCase().trim() },
    })
    if (existingUser) {
      return NextResponse.json(
        { error: 'A user with that email already exists' },
        { status: 409 },
      )
    }

    // Create client record
    const client = await prisma.client.create({
      data: { name, websiteUrl },
    })

    // Create client user account
    const passwordHash = await bcrypt.hash(password, 12)
    await prisma.user.create({
      data: {
        email: email.toLowerCase().trim(),
        passwordHash,
        role: 'client',
        clientId: client.id,
      },
    })

    // Trigger baseline audit via FastAPI (non-fatal if service unavailable)
    try {
      const fastApiUrl = process.env.FASTAPI_URL ?? 'http://localhost:8000'
      await fetch(`${fastApiUrl}/audit/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clientId: client.id,
          websiteUrl,
          competitors,
          isBaseline: true,
        }),
      })
    } catch (auditErr) {
      console.warn('Baseline audit trigger failed (non-fatal):', auditErr)
    }

    return NextResponse.json(
      { id: client.id, name: client.name, websiteUrl: client.websiteUrl },
      { status: 201 },
    )
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal server error'
    console.error('POST /api/clients error:', err)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
