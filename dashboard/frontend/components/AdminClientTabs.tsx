'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { CategoryBreakdown } from '@/components/CategoryBreakdown'
import { CitationExamples } from '@/components/CitationExamples'
import { ProgressChart } from '@/components/ProgressChart'
import { RecommendationBoard } from '@/components/RecommendationBoard'
import type { ScoreBreakdown, RecommendationRecord, AuditData } from '@/lib/types'

interface AuditLite {
  id: string
  date: string
  score: number
  isBaseline: boolean
  scores: ScoreBreakdown
}

interface LatestAudit {
  id: string
  geoScore: number
  scores: ScoreBreakdown
  rawData: AuditData
  isBaseline: boolean
  timestamp: Date
}

interface AdminClientTabsProps {
  latestAudit: LatestAudit | null
  chartData: Array<{ date: string; score: number; isBaseline?: boolean }>
  auditTableRows: AuditLite[]
  recommendations: RecommendationRecord[]
}

type TabId = 'overview' | 'history' | 'recommendations'

const TABS: Array<{ id: TabId; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'history', label: 'Audit History' },
  { id: 'recommendations', label: 'Recommendations' },
]

const SCORE_LABELS: Record<keyof ScoreBreakdown, string> = {
  ai_citability: 'AI Citability',
  brand_authority: 'Brand Authority',
  content_eeat: 'Content & E-E-A-T',
  technical: 'Technical',
  schema: 'Schema',
  platform_optimization: 'Platform',
}

function ScoreCell({ score }: { score: number }) {
  const color =
    score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-amber-400' : score >= 40 ? 'text-orange-400' : 'text-red-400'
  return <span className={`font-semibold tabular-nums text-sm ${color}`}>{Math.round(score)}</span>
}

async function updateRecommendationStatus(id: string, status: string) {
  await fetch(`/api/recommendations/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
}

export default function AdminClientTabs({
  latestAudit,
  chartData,
  auditTableRows,
  recommendations,
}: AdminClientTabsProps) {
  const [activeTab, setActiveTab] = useState<TabId>('overview')

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
      {/* Tab bar */}
      <div className="border-b border-slate-800 px-4 flex gap-1 pt-2">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all border-b-2 -mb-px ${
              activeTab === tab.id
                ? 'text-white border-indigo-500 bg-slate-800/40'
                : 'text-slate-400 border-transparent hover:text-slate-300 hover:bg-slate-800/20'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="p-5">
        {/* Overview tab */}
        {activeTab === 'overview' && (
          <div className="space-y-5">
            {latestAudit ? (
              <>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                  <CategoryBreakdown scores={latestAudit.scores} />
                  <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5">
                    <h3 className="text-slate-200 font-semibold text-sm tracking-wide uppercase mb-4">
                      Score Trend
                    </h3>
                    <ProgressChart data={chartData} />
                  </div>
                </div>
                <div>
                  <h3 className="text-slate-200 font-semibold text-sm tracking-wide uppercase mb-3">
                    Top Findings
                  </h3>
                  <CitationExamples findings={latestAudit.rawData?.findings ?? []} />
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
                <p className="text-slate-400 text-sm">No audit data yet.</p>
                <p className="text-slate-500 text-xs">Run an audit to see the overview.</p>
              </div>
            )}
          </div>
        )}

        {/* Audit History tab */}
        {activeTab === 'history' && (
          <div className="space-y-5">
            <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5">
              <h3 className="text-slate-200 font-semibold text-sm tracking-wide uppercase mb-4">
                Score Progress
              </h3>
              <ProgressChart data={chartData} />
            </div>

            {auditTableRows.length === 0 ? (
              <p className="text-slate-500 text-sm text-center py-8">No audits recorded yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left text-slate-500 font-medium px-3 py-2.5 text-xs uppercase tracking-wider">Date</th>
                      <th className="text-left text-slate-500 font-medium px-3 py-2.5 text-xs uppercase tracking-wider">Score</th>
                      {(Object.keys(SCORE_LABELS) as Array<keyof ScoreBreakdown>).map((key) => (
                        <th key={key} className="text-left text-slate-500 font-medium px-3 py-2.5 text-xs uppercase tracking-wider whitespace-nowrap">
                          {SCORE_LABELS[key]}
                        </th>
                      ))}
                      <th className="text-left text-slate-500 font-medium px-3 py-2.5 text-xs uppercase tracking-wider">Type</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {auditTableRows.map((row) => (
                      <tr key={row.id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-3 py-3 text-slate-300 whitespace-nowrap">
                          {format(new Date(row.date), 'MMM d, yyyy')}
                        </td>
                        <td className="px-3 py-3">
                          <ScoreCell score={row.score} />
                        </td>
                        {(Object.keys(SCORE_LABELS) as Array<keyof ScoreBreakdown>).map((key) => (
                          <td key={key} className="px-3 py-3">
                            <ScoreCell score={row.scores[key] ?? 0} />
                          </td>
                        ))}
                        <td className="px-3 py-3">
                          {row.isBaseline && (
                            <span className="px-2 py-0.5 bg-amber-950/50 border border-amber-800 text-amber-400 text-xs font-medium rounded-full">
                              Baseline
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Recommendations tab */}
        {activeTab === 'recommendations' && (
          <RecommendationBoard
            recommendations={recommendations}
            onStatusChange={updateRecommendationStatus}
          />
        )}
      </div>
    </div>
  )
}
