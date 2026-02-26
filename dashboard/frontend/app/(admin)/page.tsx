import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/db'
import Link from 'next/link'
import {
  Users,
  TrendingDown,
  Clock,
  BarChart3,
  Plus,
  Bell,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react'
import { formatDistanceToNow, subDays } from 'date-fns'
import type { ClientWithStats } from '@/lib/types'

// ── Helpers ───────────────────────────────────────────────────────────────────

function getClientStatus(client: ClientWithStats): 'good' | 'drop' | 'overdue' {
  if (!client.lastAuditAt) return 'overdue'
  const daysSince = (Date.now() - new Date(client.lastAuditAt).getTime()) / 86_400_000
  if (daysSince > 30) return 'overdue'
  if (client.scoreDelta !== null && client.scoreDelta < -5) return 'drop'
  return 'good'
}

const STATUS_CONFIG = {
  good: { label: 'Good', className: 'bg-emerald-950/60 border-emerald-800 text-emerald-400' },
  drop: { label: 'Score Drop', className: 'bg-amber-950/60 border-amber-800 text-amber-400' },
  overdue: { label: 'Overdue', className: 'bg-red-950/60 border-red-800 text-red-400' },
}

function ScoreChip({ score }: { score: number | null }) {
  if (score === null) return <span className="text-slate-500 text-sm">—</span>
  const color =
    score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-amber-400' : score >= 40 ? 'text-orange-400' : 'text-red-400'
  return <span className={`font-bold text-sm tabular-nums ${color}`}>{Math.round(score)}</span>
}

function DeltaChip({ delta }: { delta: number | null }) {
  if (delta === null) return <span className="text-slate-500 text-xs">—</span>
  if (delta === 0) return <span className="text-slate-400 text-xs">±0</span>
  const positive = delta > 0
  return (
    <span className={`text-xs font-semibold ${positive ? 'text-emerald-400' : 'text-red-400'}`}>
      {positive ? `↑+${delta}` : `↓${delta}`}
    </span>
  )
}

// ── Data fetching ─────────────────────────────────────────────────────────────

async function getAdminStats() {
  const [clients, recentAudits, unreadAlerts] = await Promise.all([
    prisma.client.findMany({
      where: { isActive: true },
      orderBy: { createdAt: 'desc' },
      include: {
        audits: {
          orderBy: { timestamp: 'desc' },
          take: 2,
          select: { geoScore: true, timestamp: true },
        },
        _count: { select: { audits: true } },
      },
    }),
    prisma.audit.count({
      where: { timestamp: { gte: subDays(new Date(), 7) } },
    }),
    prisma.alert.count({ where: { isRead: false } }),
  ])

  const clientsWithStats: ClientWithStats[] = clients.map((c) => {
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

  const avgScore =
    clientsWithStats.filter((c) => c.latestScore !== null).length > 0
      ? Math.round(
          clientsWithStats
            .filter((c) => c.latestScore !== null)
            .reduce((sum, c) => sum + (c.latestScore ?? 0), 0) /
            clientsWithStats.filter((c) => c.latestScore !== null).length
        )
      : null

  const recentAlerts = await prisma.alert.findMany({
    where: { isRead: false },
    orderBy: { createdAt: 'desc' },
    take: 5,
    include: { client: { select: { name: true } } },
  })

  return { clients: clientsWithStats, avgScore, recentAudits, unreadAlerts, recentAlerts }
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function AdminDashboardPage() {
  const session = await getServerSession(authOptions)
  if (!session || session.user.role !== 'admin') redirect('/login')

  const { clients, avgScore, recentAudits, unreadAlerts, recentAlerts } = await getAdminStats()

  const statCards = [
    {
      label: 'Total Clients',
      value: clients.length,
      icon: Users,
      color: 'text-indigo-400',
      bg: 'bg-indigo-950/40',
      border: 'border-indigo-800/50',
    },
    {
      label: 'Avg GEO Score',
      value: avgScore !== null ? avgScore : '—',
      icon: BarChart3,
      color: 'text-emerald-400',
      bg: 'bg-emerald-950/40',
      border: 'border-emerald-800/50',
    },
    {
      label: 'Active Alerts',
      value: unreadAlerts,
      icon: Bell,
      color: 'text-amber-400',
      bg: 'bg-amber-950/40',
      border: 'border-amber-800/50',
    },
    {
      label: 'Audits This Week',
      value: recentAudits,
      icon: Clock,
      color: 'text-blue-400',
      bg: 'bg-blue-950/40',
      border: 'border-blue-800/50',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Client Overview</h1>
          <p className="text-slate-400 text-sm mt-0.5">Manage all clients and monitor GEO performance</p>
        </div>
        <Link
          href="/admin/clients/new"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-colors shadow-lg shadow-indigo-900/30"
        >
          <Plus size={16} />
          Add Client
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => {
          const Icon = card.icon
          return (
            <div
              key={card.label}
              className={`${card.bg} border ${card.border} rounded-xl px-5 py-4`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-slate-400 text-xs font-medium uppercase tracking-wider">{card.label}</span>
                <Icon size={16} className={card.color} />
              </div>
              <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
            </div>
          )
        })}
      </div>

      {/* Clients table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="font-semibold text-white text-sm">Clients</h2>
          <span className="text-slate-500 text-xs">{clients.length} total</span>
        </div>

        {clients.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <Users size={32} className="text-slate-700" />
            <p className="text-slate-400 text-sm">No clients yet</p>
            <Link
              href="/admin/clients/new"
              className="text-indigo-400 hover:text-indigo-300 text-sm flex items-center gap-1"
            >
              <Plus size={14} />
              Add your first client
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="text-left text-slate-500 font-medium px-5 py-3 text-xs uppercase tracking-wider">Client</th>
                  <th className="text-left text-slate-500 font-medium px-4 py-3 text-xs uppercase tracking-wider">Score</th>
                  <th className="text-left text-slate-500 font-medium px-4 py-3 text-xs uppercase tracking-wider">Change</th>
                  <th className="text-left text-slate-500 font-medium px-4 py-3 text-xs uppercase tracking-wider">Last Audit</th>
                  <th className="text-left text-slate-500 font-medium px-4 py-3 text-xs uppercase tracking-wider">Status</th>
                  <th className="text-left text-slate-500 font-medium px-4 py-3 text-xs uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {clients.map((client) => {
                  const status = getClientStatus(client)
                  const statusCfg = STATUS_CONFIG[status]
                  return (
                    <tr key={client.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-3.5">
                        <div>
                          <p className="text-white font-medium">{client.name}</p>
                          <p className="text-slate-500 text-xs mt-0.5 truncate max-w-[200px]">{client.websiteUrl}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <ScoreChip score={client.latestScore} />
                      </td>
                      <td className="px-4 py-3.5">
                        <DeltaChip delta={client.scoreDelta} />
                      </td>
                      <td className="px-4 py-3.5">
                        {client.lastAuditAt ? (
                          <span className="text-slate-400 text-xs">
                            {formatDistanceToNow(new Date(client.lastAuditAt), { addSuffix: true })}
                          </span>
                        ) : (
                          <span className="text-slate-600 text-xs">Never</span>
                        )}
                      </td>
                      <td className="px-4 py-3.5">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${statusCfg.className}`}
                        >
                          {statusCfg.label}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        <Link
                          href={`/admin/clients/${client.id}`}
                          className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 text-xs font-medium transition-colors"
                        >
                          <ExternalLink size={12} />
                          View
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Alerts section */}
      {recentAlerts.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell size={15} className="text-amber-400" />
              <h2 className="font-semibold text-white text-sm">Recent Alerts</h2>
              <span className="px-2 py-0.5 bg-amber-950/50 border border-amber-800 text-amber-400 text-xs font-bold rounded-full">
                {unreadAlerts}
              </span>
            </div>
            <Link href="/admin/alerts" className="text-indigo-400 hover:text-indigo-300 text-xs font-medium">
              View all
            </Link>
          </div>
          <div className="divide-y divide-slate-800/60">
            {recentAlerts.map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 px-5 py-3.5">
                <AlertTriangle size={15} className="text-amber-400 shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-slate-200 text-sm font-medium">{alert.client.name}</p>
                  <p className="text-slate-400 text-xs mt-0.5">{alert.message}</p>
                </div>
                <span className="text-slate-500 text-xs shrink-0">
                  {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
