import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/db'
import Link from 'next/link'
import { ChevronLeft, Download, TrendingUp, AlertCircle } from 'lucide-react'
import { format } from 'date-fns'
import { ProgressChart } from '@/components/ProgressChart'
import type { ScoreBreakdown } from '@/lib/types'

// ── Data fetching ─────────────────────────────────────────────────────────────

async function getAuditHistory(clientId: string) {
  const client = await prisma.client.findUnique({
    where: { id: clientId },
    select: { name: true, websiteUrl: true },
  })
  if (!client) return null

  const audits = await prisma.audit.findMany({
    where: { clientId },
    orderBy: { timestamp: 'desc' },
    select: {
      id: true,
      timestamp: true,
      geoScore: true,
      isBaseline: true,
      scores: true,
    },
  })

  return { client, audits }
}

// ── Sub-components ────────────────────────────────────────────────────────────

const SCORE_LABELS: Record<keyof ScoreBreakdown, string> = {
  ai_citability: 'AI Citability',
  brand_authority: 'Brand',
  content_eeat: 'E-E-A-T',
  technical: 'Technical',
  schema: 'Schema',
  platform_optimization: 'Platform',
}

function ScoreChip({ score }: { score: number }) {
  const color =
    score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-amber-400' : score >= 40 ? 'text-orange-400' : 'text-red-400'
  return <span className={`font-semibold tabular-nums ${color}`}>{Math.round(score)}</span>
}

function DeltaChip({ delta }: { delta: number | null }) {
  if (delta === null) return <span className="text-slate-500 text-xs">—</span>
  if (delta === 0) return <span className="text-slate-400 text-xs">±0</span>
  return (
    <span className={`text-xs font-semibold ${delta > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
      {delta > 0 ? `↑+${delta}` : `↓${delta}`}
    </span>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function ClientHistoryPage() {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  const clientId = session.user.clientId
  if (!clientId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3 text-center px-4">
        <AlertCircle size={32} className="text-red-400" />
        <p className="text-slate-300 font-medium">No client account linked to your user.</p>
      </div>
    )
  }

  const data = await getAuditHistory(clientId)

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-slate-400">Client not found.</p>
      </div>
    )
  }

  const { client, audits } = data

  // Build chart data (oldest first)
  const chartData = [...audits]
    .reverse()
    .map((a) => ({
      date: new Date(a.timestamp).toISOString().split('T')[0],
      score: Math.round(a.geoScore),
      isBaseline: a.isBaseline,
    }))

  // Build table rows with parsed scores and delta
  const tableRows = audits.map((audit, i) => {
    const scores = JSON.parse(audit.scores) as ScoreBreakdown
    const nextAudit = audits[i + 1] ?? null // Next in desc order = previous audit
    const delta = nextAudit ? Math.round(audit.geoScore - nextAudit.geoScore) : null
    return { ...audit, scores, delta }
  })

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/client"
            className="inline-flex items-center gap-1.5 text-slate-400 hover:text-white text-sm mb-3 transition-colors"
          >
            <ChevronLeft size={15} />
            Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <TrendingUp size={22} className="text-indigo-400" />
            Audit History
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {client.name} — {audits.length} audit{audits.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Progress chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <h2 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-4">
          GEO Score Over Time
        </h2>
        {audits.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
            No audit data yet.
          </div>
        ) : (
          <ProgressChart data={chartData} />
        )}
      </div>

      {/* Audit history table */}
      {audits.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800">
            <h2 className="font-semibold text-white text-sm">All Audits</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/50">
                  <th className="text-left text-slate-500 font-medium px-5 py-3 text-xs uppercase tracking-wider whitespace-nowrap">
                    Date
                  </th>
                  <th className="text-left text-slate-500 font-medium px-4 py-3 text-xs uppercase tracking-wider">
                    Score
                  </th>
                  <th className="text-left text-slate-500 font-medium px-4 py-3 text-xs uppercase tracking-wider">
                    Change
                  </th>
                  {(Object.keys(SCORE_LABELS) as Array<keyof ScoreBreakdown>).map((key) => (
                    <th
                      key={key}
                      className="text-left text-slate-500 font-medium px-4 py-3 text-xs uppercase tracking-wider whitespace-nowrap"
                    >
                      {SCORE_LABELS[key]}
                    </th>
                  ))}
                  <th className="text-left text-slate-500 font-medium px-4 py-3 text-xs uppercase tracking-wider">
                    Report
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {tableRows.map((row) => (
                  <tr
                    key={row.id}
                    className={`transition-colors ${
                      row.isBaseline ? 'bg-amber-950/10 hover:bg-amber-950/20' : 'hover:bg-slate-800/30'
                    }`}
                  >
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-200 whitespace-nowrap">
                          {format(new Date(row.timestamp), 'MMM d, yyyy')}
                        </span>
                        {row.isBaseline && (
                          <span className="px-2 py-0.5 bg-amber-950/60 border border-amber-800 text-amber-400 text-xs font-medium rounded-full">
                            Baseline
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <ScoreChip score={row.geoScore} />
                    </td>
                    <td className="px-4 py-3.5">
                      <DeltaChip delta={row.delta} />
                    </td>
                    {(Object.keys(SCORE_LABELS) as Array<keyof ScoreBreakdown>).map((key) => (
                      <td key={key} className="px-4 py-3.5">
                        <ScoreChip score={row.scores[key] ?? 0} />
                      </td>
                    ))}
                    <td className="px-4 py-3.5">
                      <a
                        href={`/api/reports/${row.id}`}
                        className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                      >
                        <Download size={12} />
                        PDF
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {audits.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
          <TrendingUp size={32} className="text-slate-700" />
          <div>
            <p className="text-slate-300 font-medium">No audits yet</p>
            <p className="text-slate-500 text-sm mt-1">
              Your first audit will appear here once it completes.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
