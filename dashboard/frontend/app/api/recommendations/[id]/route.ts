import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

type RouteContext = { params: { id: string } }

type RecommendationStatus = 'pending' | 'in_progress' | 'done'

// ── PATCH /api/recommendations/[id] ──────────────────────────────────────────
// Updates the status of a recommendation.
// Admin can update any; client users can only update their own.
export async function PATCH(
  req: NextRequest,
  { params }: RouteContext,
): Promise<NextResponse> {
  const session = await getServerSession(authOptions)
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const body = (await req.json()) as { status?: string }
    const { status } = body

    const validStatuses: RecommendationStatus[] = ['pending', 'in_progress', 'done']
    if (!status || !validStatuses.includes(status as RecommendationStatus)) {
      return NextResponse.json(
        { error: `status must be one of: ${validStatuses.join(', ')}` },
        { status: 400 },
      )
    }

    // Fetch the recommendation to verify ownership for client users
    const recommendation = await prisma.recommendation.findUnique({
      where: { id: params.id },
    })

    if (!recommendation) {
      return NextResponse.json({ error: 'Recommendation not found' }, { status: 404 })
    }

    // Client users can only update recommendations for their own client
    if (
      session.user.role === 'client' &&
      session.user.clientId !== recommendation.clientId
    ) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }

    const updated = await prisma.recommendation.update({
      where: { id: params.id },
      data: { status },
    })

    return NextResponse.json(updated)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal server error'
    console.error(`PATCH /api/recommendations/${params.id} error:`, err)
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
