import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/db'
import Link from 'next/link'
import { TrendingUp, AlertCircle } from 'lucide-react'
import { ScoreGauge } from '@/components/ScoreGauge'
import { ProgressChart } from '@/components/ProgressChart'
import { CompetitorBar } from '@/components/CompetitorBar'
import { CategoryBreakdown } from '@/components/CategoryBreakdown'
import { MilestoneFeed } from '@/components/MilestoneFeed'
import RecommendationSection from '@/components/RecommendationSection'
import { CitationExamples } from '@/components/CitationExamples'
import type { ScoreBreakdown, AuditData, CompetitorSnapshot, RecommendationRecord } from '@/lib/types'

// ── Data fetching ─────────────────────────────────────────────────────────────

async function getClientDashboardData(clientId: string) {
  const client = await prisma.client.findUnique({
    where: { id: clientId },
    include: {
      audits: {
        orderBy: { timestamp: 'desc' },
        take: 20,
        include: {
          recommendations: {
            orderBy: [{ priority: 'asc' }, { status: 'asc' }],
          },
        },
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

// ── No audit state ────────────────────────────────────────────────────────────

function NoAuditState({ clientName }: { clientName: string }) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-6 px-6 text-center">
      <div className="w-20 h-20 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center">
        <TrendingUp size={32} className="text-slate-600" />
      </div>
      <div>
        <h2 className="text-xl font-bold text-white">{clientName}</h2>
        <p className="text-slate-400 mt-2 max-w-sm">
          Your baseline GEO audit is being prepared. Check back shortly — it usually completes within
          a few minutes.
        </p>
      </div>
      <div className="flex gap-2">
        <span className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-full text-xs text-slate-400 animate-pulse">
          Audit pending…
        </span>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function ClientDashboardPage() {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  const clientId = session.user.clientId
  if (!clientId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3 text-center px-4">
        <AlertCircle size={32} className="text-red-400" />
        <p className="text-slate-300 font-medium">No client account linked to your user.</p>
        <p className="text-slate-500 text-sm">Contact your admin to set up your account.</p>
      </div>
    )
  }

  const data = await getClientDashboardData(clientId)

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-slate-400">Client not found.</p>
      </div>
    )
  }

  const { client, audits } = data

  if (audits.length === 0) {
    return <NoAuditState clientName={client.name} />
  }

  const latestAudit = audits[0]
  const baselineAudit = audits.find((a) => a.isBaseline) ?? audits[audits.length - 1]
  const currentScore = Math.round(latestAudit.geoScore)
  const baselineScore = Math.round(baselineAudit.geoScore)

  // Chart data (oldest first)
  const chartData = [...audits]
    .reverse()
    .map((a) => ({
      date: new Date(a.timestamp).toISOString().split('T')[0],
      score: Math.round(a.geoScore),
      isBaseline: a.isBaseline,
    }))

  // Top competitor from latest audit
  const competitors = latestAudit.competitors ?? []
  const topCompetitor = competitors.length > 0 ? competitors[0] : null

  // Milestones feed data
  const milestoneAudits = [...audits]
    .reverse()
    .map((a) => ({
      timestamp: a.timestamp.toISOString(),
      geoScore: Math.round(a.geoScore),
      rawData: JSON.stringify(a.rawData),
      isBaseline: a.isBaseline,
    }))

  // Recommendations for latest audit only
  const latestRecs = latestAudit.recommendations

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto space-y-6">
      {/* Client name banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{client.name}</h1>
          <p className="text-slate-400 text-sm mt-0.5">GEO Performance Dashboard</p>
        </div>
        <Link href="/client/history" className="btn-secondary text-sm px-4 py-2">
          <TrendingUp size={14} />
          Full History
        </Link>
      </div>

      {/* Row 1: Score Gauge + Progress Chart */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Score Gauge */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col items-center">
          <h2 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-4">
            Current GEO Score
          </h2>
          <ScoreGauge score={currentScore} size="lg" label="GEO Score" />
          {currentScore !== baselineScore && (
            <div className="mt-4 flex items-center gap-2">
              <span
                className={`inline-flex items-center gap-1 text-sm font-semibold px-3 py-1 rounded-full ${
                  currentScore > baselineScore
                    ? 'bg-emerald-950/50 border border-emerald-800 text-emerald-400'
                    : 'bg-red-950/50 border border-red-800 text-red-400'
                }`}
              >
                {currentScore > baselineScore
                  ? `↑ +${currentScore - baselineScore} from baseline`
                  : `↓ ${currentScore - baselineScore} from baseline`}
              </span>
            </div>
          )}
        </div>

        {/* Progress Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <h2 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-4">
            Progress Since Start
          </h2>
          <ProgressChart data={chartData} />
        </div>
      </div>

      {/* Row 2: Competitor Bar (full width) */}
      {topCompetitor && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <CompetitorBar
            clientName={client.name}
            clientScore={currentScore}
            competitorName={topCompetitor.name ?? topCompetitor.url}
            competitorScore={Math.round(topCompetitor.geoScore)}
          />
        </div>
      )}

      {/* Row 3: Category Breakdown (full width) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <CategoryBreakdown scores={latestAudit.scores} />
      </div>

      {/* Row 4: Milestones + Action Items */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Milestones */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <MilestoneFeed
            audits={milestoneAudits}
            currentScore={currentScore}
            baselineScore={baselineScore}
          />
        </div>

        {/* Recommendations */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <RecommendationSection recommendations={latestRecs} heading="Action Items" />
        </div>
      </div>

      {/* Row 5: Top Findings (citations) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <CitationExamples findings={latestAudit.rawData?.findings ?? []} />
      </div>
    </div>
  )
}
