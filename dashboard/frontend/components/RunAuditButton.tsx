'use client'

import { useState } from 'react'
import { RefreshCw, Loader2, CheckCircle2 } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface RunAuditButtonProps {
  clientId: string
}

export default function RunAuditButton({ clientId }: RunAuditButtonProps) {
  const router = useRouter()
  const [state, setState] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  async function handleClick() {
    setState('loading')
    setErrorMsg(null)

    try {
      const res = await fetch('/api/audits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId }),
      })

      const data = await res.json()

      if (!res.ok) {
        setErrorMsg(data.error ?? 'Audit failed')
        setState('error')
        return
      }

      setState('done')
      setTimeout(() => {
        setState('idle')
        router.refresh()
      }, 2000)
    } catch {
      setErrorMsg('Network error. Please try again.')
      setState('error')
    }
  }

  if (state === 'error') {
    return (
      <button
        onClick={() => { setState('idle'); setErrorMsg(null) }}
        className="btn-secondary text-xs px-3 py-2 border-red-800 text-red-400"
        title={errorMsg ?? ''}
      >
        <RefreshCw size={13} />
        Retry Audit
      </button>
    )
  }

  if (state === 'done') {
    return (
      <button className="btn-secondary text-xs px-3 py-2 border-emerald-800 text-emerald-400" disabled>
        <CheckCircle2 size={13} />
        Audit Queued
      </button>
    )
  }

  return (
    <button
      onClick={handleClick}
      disabled={state === 'loading'}
      className="btn-secondary text-xs px-3 py-2"
    >
      {state === 'loading' ? (
        <>
          <Loader2 size={13} className="animate-spin" />
          Running…
        </>
      ) : (
        <>
          <RefreshCw size={13} />
          Run Audit Now
        </>
      )}
    </button>
  )
}
