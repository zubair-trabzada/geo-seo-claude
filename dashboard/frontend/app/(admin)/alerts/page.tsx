import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/db'
import { format, formatDistanceToNow } from 'date-fns'
import { Bell, TrendingDown, Clock, CheckCircle2, AlertTriangle } from 'lucide-react'
import AlertActions from '@/components/AlertActions'

// ── Data fetching ─────────────────────────────────────────────────────────────

async function getAlerts() {
  const alerts = await prisma.alert.findMany({
    orderBy: { createdAt: 'desc' },
    include: { client: { select: { id: true, name: true } } },
  })
  return alerts
}

// ── Sub-components ─────────────────────────────────────────────────────────

const ALERT_TYPE_CONFIG = {
  score_drop: {
    icon: TrendingDown,
    label: 'Score Drop',
    iconClass: 'text-red-400',
    borderClass: 'border-red-800/40',
    bgClass: 'bg-red-950/20',
    badgeClass: 'bg-red-950/50 border-red-800 text-red-400',
  },
  overdue_audit: {
    icon: Clock,
    label: 'Overdue',
    iconClass: 'text-amber-400',
    borderClass: 'border-amber-800/40',
    bgClass: 'bg-amber-950/20',
    badgeClass: 'bg-amber-950/50 border-amber-800 text-amber-400',
  },
  milestone: {
    icon: CheckCircle2,
    label: 'Milestone',
    iconClass: 'text-emerald-400',
    borderClass: 'border-emerald-800/40',
    bgClass: 'bg-emerald-950/20',
    badgeClass: 'bg-emerald-950/50 border-emerald-800 text-emerald-400',
  },
}

type AlertType = keyof typeof ALERT_TYPE_CONFIG

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function AlertsPage({
  searchParams,
}: {
  searchParams?: { filter?: string }
}) {
  const session = await getServerSession(authOptions)
  if (!session || session.user.role !== 'admin') redirect('/login')

  const rawAlerts = await getAlerts()
  const filter = searchParams?.filter ?? 'all'

  const filteredAlerts = rawAlerts.filter((a) => {
    if (filter === 'unread') return !a.isRead
    if (filter === 'score_drop') return a.type === 'score_drop'
    if (filter === 'overdue') return a.type === 'overdue_audit'
    return true
  })

  const unreadCount = rawAlerts.filter((a) => !a.isRead).length

  const filterTabs = [
    { id: 'all', label: 'All', count: rawAlerts.length },
    { id: 'unread', label: 'Unread', count: unreadCount },
    { id: 'score_drop', label: 'Score Drops', count: rawAlerts.filter((a) => a.type === 'score_drop').length },
    { id: 'overdue', label: 'Overdue', count: rawAlerts.filter((a) => a.type === 'overdue_audit').length },
  ]

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Bell size={22} className="text-amber-400" />
            Alerts
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {unreadCount} unread alert{unreadCount !== 1 ? 's' : ''}
          </p>
        </div>
        {unreadCount > 0 && (
          <AlertActions alertIds={rawAlerts.filter((a) => !a.isRead).map((a) => a.id)} />
        )}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 flex-wrap">
        {filterTabs.map((tab) => (
          <a
            key={tab.id}
            href={`/admin/alerts${tab.id !== 'all' ? `?filter=${tab.id}` : ''}`}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
              filter === tab.id
                ? 'bg-indigo-600/20 border-indigo-600/50 text-indigo-300'
                : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:text-white hover:border-slate-600'
            }`}
          >
            {tab.label}
            <span
              className={`px-1.5 py-0.5 rounded-full text-xs font-bold ${
                filter === tab.id ? 'bg-indigo-600/30 text-indigo-300' : 'bg-slate-700 text-slate-400'
              }`}
            >
              {tab.count}
            </span>
          </a>
        ))}
      </div>

      {/* Alert list */}
      {filteredAlerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="w-16 h-16 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
            <Bell size={24} className="text-slate-600" />
          </div>
          <div className="text-center">
            <p className="text-slate-300 font-medium">No alerts</p>
            <p className="text-slate-500 text-sm mt-1">
              {filter === 'unread' ? 'All caught up!' : 'No alerts in this category.'}
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert) => {
            const typeKey = alert.type as AlertType
            const config = ALERT_TYPE_CONFIG[typeKey] ?? ALERT_TYPE_CONFIG.score_drop
            const Icon = config.icon

            return (
              <div
                key={alert.id}
                className={`bg-slate-900 border rounded-xl p-4 flex items-start gap-4 transition-colors ${
                  alert.isRead
                    ? 'border-slate-800 opacity-70'
                    : `${config.borderClass} ${config.bgClass}`
                }`}
              >
                {/* Icon */}
                <div
                  className={`shrink-0 w-9 h-9 rounded-full flex items-center justify-center border ${
                    alert.isRead ? 'bg-slate-800 border-slate-700' : `${config.bgClass} ${config.borderClass}`
                  }`}
                >
                  <Icon size={16} className={alert.isRead ? 'text-slate-500' : config.iconClass} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-white font-semibold text-sm">{alert.client.name}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium border ${config.badgeClass}`}
                    >
                      {config.label}
                    </span>
                    {!alert.isRead && (
                      <span className="w-2 h-2 bg-indigo-400 rounded-full" aria-label="Unread" />
                    )}
                  </div>
                  <p className="text-slate-300 text-sm">{alert.message}</p>
                  <p className="text-slate-500 text-xs mt-1.5" title={format(new Date(alert.createdAt), 'PPPp')}>
                    {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true })}
                  </p>
                </div>

                {/* Mark read action */}
                {!alert.isRead && (
                  <AlertActions alertIds={[alert.id]} single />
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
