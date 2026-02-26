import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

type RouteContext = { params: { id: string } }

// ── GET /api/clients/[id] ─────────────────────────────────────────────────────
// Returns a single client with all their audits.
// Accessible by admin or the matching client user.
export async function GET(
  _req: NextRequest,
  { params }: RouteContext,
): Promise<NextResponse> {
  const session = await getServerSession(authOptions)
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Client users can only access their own data
  if (
    session.user.role === 'client' &&
    session.user.clientId !== params.id
  ) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  try {
    const client = await prisma.client.findUnique({
      where: { id: params.id },
      include: {
        audits: {
          orderBy: { timestamp: 'desc' },
          include: {
            recommendations: {
              orderBy: [{ priority: 'asc' }, { status: 'asc' }],
            },
          },
        },
        users: {
          select: { id: true, email: true, role: true, createdAt: true },
        },
      },
    })

    if (!client) {
      return NextResponse.json({ error: 'Client not found' }, { status: 404 })
    }

    return NextResponse.json(client)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal server error'
    console.error(`GET /api/clients/${params.id} error:`, err)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

// ── PATCH /api/clients/[id] ───────────────────────────────────────────────────
// Updates client name, websiteUrl, or isActive. Admin only.
export async function PATCH(
  req: NextRequest,
  { params }: RouteContext,
): Promise<NextResponse> {
  const session = await getServerSession(authOptions)
  if (!session || session.user.role !== 'admin') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const body = (await req.json()) as {
      name?: string
      websiteUrl?: string
      isActive?: boolean
    }

    const { name, websiteUrl, isActive } = body

    const updated = await prisma.client.update({
      where: { id: params.id },
      data: {
        ...(name !== undefined && { name }),
        ...(websiteUrl !== undefined && { websiteUrl }),
        ...(isActive !== undefined && { isActive }),
      },
    })

    return NextResponse.json(updated)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal server error'
    console.error(`PATCH /api/clients/${params.id} error:`, err)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
