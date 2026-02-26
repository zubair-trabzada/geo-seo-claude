'use client'

import { useState } from 'react'
import { CheckCheck, Check, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface AlertActionsProps {
  alertIds: string[]
  single?: boolean
}

export default function AlertActions({ alertIds, single = false }: AlertActionsProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function markRead() {
    setLoading(true)
    try {
      await Promise.all(
        alertIds.map((id) =>
          fetch(`/api/alerts/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ isRead: true }),
          })
        )
      )
      setDone(true)
      setTimeout(() => {
        router.refresh()
      }, 500)
    } catch {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="flex items-center gap-1 text-emerald-400 text-xs font-medium">
        <Check size={13} />
        {single ? 'Marked read' : 'All marked read'}
      </div>
    )
  }

  if (single) {
    return (
      <button
        onClick={markRead}
        disabled={loading}
        className="shrink-0 text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-600 rounded-lg px-3 py-1.5 transition-colors flex items-center gap-1.5"
      >
        {loading ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
        Mark read
      </button>
    )
  }

  return (
    <button
      onClick={markRead}
      disabled={loading}
      className="flex items-center gap-2 text-sm font-medium text-slate-300 hover:text-white border border-slate-700 hover:border-slate-600 bg-slate-800 hover:bg-slate-700 rounded-xl px-4 py-2 transition-all"
    >
      {loading ? (
        <Loader2 size={14} className="animate-spin" />
      ) : (
        <CheckCheck size={14} />
      )}
      Mark all as read
    </button>
  )
}
