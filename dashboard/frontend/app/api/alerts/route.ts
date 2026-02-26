import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

// ── GET /api/alerts ───────────────────────────────────────────────────────────
// Returns unread alerts. Admin only.
export async function GET(_req: NextRequest): Promise<NextResponse> {
  const session = await getServerSession(authOptions)
  if (!session || session.user.role !== 'admin') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const alerts = await prisma.alert.findMany({
      where: { isRead: false },
      orderBy: { createdAt: 'desc' },
    })

    return NextResponse.json(alerts)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal server error'
    console.error('GET /api/alerts error:', err)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

// ── PATCH /api/alerts?id=xxx ──────────────────────────────────────────────────
// Marks a single alert as read. Admin only.
export async function PATCH(req: NextRequest): Promise<NextResponse> {
  const session = await getServerSession(authOptions)
  if (!session || session.user.role !== 'admin') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const id = req.nextUrl.searchParams.get('id')
  if (!id) {
    return NextResponse.json({ error: 'id query param required' }, { status: 400 })
  }

  try {
    const alert = await prisma.alert.findUnique({ where: { id } })
    if (!alert) {
      return NextResponse.json({ error: 'Alert not found' }, { status: 404 })
    }

    const updated = await prisma.alert.update({
      where: { id },
      data: { isRead: true },
    })

    return NextResponse.json(updated)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal server error'
    console.error(`PATCH /api/alerts?id=${id} error:`, err)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
