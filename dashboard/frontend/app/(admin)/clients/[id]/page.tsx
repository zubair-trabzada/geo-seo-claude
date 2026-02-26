import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect, notFound } from 'next/navigation'
import { prisma } from '@/lib/db'
import Link from 'next/link'
import {
  ChevronLeft,
  ExternalLink,
  FileDown,
  Calendar,
  BarChart3,
} from 'lucide-react'
import { format } from 'date-fns'
import { ScoreGauge } from '@/components/ScoreGauge'
import AdminClientTabs from '@/components/AdminClientTabs'
import RunAuditButton from '@/components/RunAuditButton'
import type { ScoreBreakdown, AuditData, CompetitorSnapshot, RecommendationRecord } from '@/lib/types'

// ── Data fetching ─────────────────────────────────────────────────────────────

async function getClientData(id: string) {
  const client = await prisma.client.findUnique({
    where: { id },
    include: {
      audits: {
        orderBy: { timestamp: 'desc' },
        include: { recommendations: true },
      },
    },
  })
  if (!client) return null

  const audits = client.audits.map((a) => ({
    ...a,
    scores: JSON.parse(a.scores) as ScoreBreakdown,
    rawData: JSON.parse(a.rawData) as AuditData,
    competitors: a.competitors ? (JSON.parse(a.competitors) as CompetitorSnapshot[]) : null,
    recommendations: a.recommendations as RecommendationRecord[],
  }))

  return { client, audits }
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ScoreDeltaBadge({ current, baseline }: { current: number; baseline: number }) {
  const delta = Math.round(current - baseline)
  if (delta === 0) return null
  return (
    <span
      className={`inline-flex items-center gap-1 text-sm font-semibold px-3 py-1 rounded-full ${
        delta > 0
          ? 'bg-emerald-950/50 border border-emerald-800 text-emerald-400'
          : 'bg-red-950/50 border border-red-800 text-red-400'
      }`}
    >
      {delta > 0 ? `↑ +${delta}` : `↓ ${delta}`} from baseline
    </span>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function AdminClientPage({ params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions)
  if (!session || session.user.role !== 'admin') redirect('/login')

  const data = await getClientData(params.id)
  if (!data) notFound()

  const { client, audits } = data
  const latestAudit = audits[0] ?? null
  const baselineAudit = audits.find((a) => a.isBaseline) ?? audits[audits.length - 1] ?? null

  const chartData = [...audits]
    .reverse()
    .map((a) => ({
      date: new Date(a.timestamp).toISOString().split('T')[0],
      score: Math.round(a.geoScore),
      isBaseline: a.isBaseline,
    }))

  const auditTableRows = audits.map((a) => ({
    id: a.id,
    date: a.timestamp,
    score: Math.round(a.geoScore),
    isBaseline: a.isBaseline,
    scores: a.scores,
  }))

  return (
    <div className="p-6 space-y-6">
      {/* Back */}
      <Link
        href="/admin"
        className="inline-flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors"
      >
        <ChevronLeft size={15} />
        All Clients
      </Link>

      {/* Client header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">{client.name}</h1>
            <a
              href={client.websiteUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-slate-400 hover:text-indigo-400 text-sm mt-1 transition-colors"
            >
              <ExternalLink size={13} />
              {client.websiteUrl}
            </a>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {latestAudit && baselineAudit && (
                <ScoreDeltaBadge
                  current={latestAudit.geoScore}
                  baseline={baselineAudit.geoScore}
                />
              )}
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Calendar size={12} />
                Client since {format(new Date(client.createdAt), 'MMM d, yyyy')}
              </span>
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <BarChart3 size={12} />
                {audits.length} audit{audits.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Link
              href={`/client`}
              className="btn-secondary text-xs px-3 py-2"
              aria-label="View client portal"
            >
              <ExternalLink size={13} />
              View as Client
            </Link>
            <RunAuditButton clientId={client.id} />
            <button className="btn-secondary text-xs px-3 py-2">
              <FileDown size={13} />
              Export PDF
            </button>
          </div>
        </div>

        {/* Score hero */}
        {latestAudit && (
          <div className="mt-6 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center gap-6">
            <div className="flex flex-col items-center">
              <ScoreGauge score={latestAudit.geoScore} size="lg" label="Current GEO Score" />
            </div>
            {baselineAudit && baselineAudit.id !== latestAudit.id && (
              <div className="flex flex-col items-center opacity-50">
                <ScoreGauge score={baselineAudit.geoScore} size="md" label="Baseline Score" />
              </div>
            )}
            <div className="flex-1 grid grid-cols-2 gap-4 min-w-0">
              {[
                { label: 'Last Audit', value: format(new Date(latestAudit.timestamp), 'MMM d, yyyy') },
                { label: 'Total Audits', value: audits.length },
                {
                  label: 'Best Score',
                  value: Math.round(Math.max(...audits.map((a) => a.geoScore))),
                },
                {
                  label: 'Baseline Score',
                  value: baselineAudit ? Math.round(baselineAudit.geoScore) : '—',
                },
              ].map((stat) => (
                <div key={stat.label} className="bg-slate-800/50 rounded-xl px-4 py-3">
                  <p className="text-xs text-slate-500 mb-1">{stat.label}</p>
                  <p className="text-lg font-bold text-white">{stat.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Tab content */}
      <AdminClientTabs
        latestAudit={latestAudit}
        chartData={chartData}
        auditTableRows={auditTableRows}
        recommendations={latestAudit?.recommendations ?? []}
      />
    </div>
  )
}
