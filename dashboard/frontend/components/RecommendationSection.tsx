'use client'

import { RecommendationBoard } from '@/components/RecommendationBoard'
import type { RecommendationRecord } from '@/lib/types'

interface RecommendationSectionProps {
  recommendations: RecommendationRecord[]
  heading?: string
}

async function updateStatus(id: string, status: string) {
  await fetch(`/api/recommendations/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
}

export default function RecommendationSection({
  recommendations,
  heading = 'Action Items',
}: RecommendationSectionProps) {
  return (
    <div>
      {heading && (
        <h2 className="text-slate-200 font-semibold text-sm tracking-wide uppercase mb-4">
          {heading}
        </h2>
      )}
      <RecommendationBoard recommendations={recommendations} onStatusChange={updateStatus} />
    </div>
  )
}
