'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Plus, Minus, Loader2, ChevronLeft, Globe, User, Lock, Building } from 'lucide-react'

interface FormState {
  name: string
  websiteUrl: string
  competitors: string[]
  email: string
  password: string
}

function isValidUrl(url: string): boolean {
  try {
    new URL(url.startsWith('http') ? url : `https://${url}`)
    return true
  } catch {
    return false
  }
}

export default function NewClientPage() {
  const router = useRouter()
  const [form, setForm] = useState<FormState>({
    name: '',
    websiteUrl: '',
    competitors: [''],
    email: '',
    password: '',
  })
  const [errors, setErrors] = useState<Partial<Record<keyof FormState | 'submit', string>>>({})
  const [loading, setLoading] = useState(false)
  const [phase, setPhase] = useState<'form' | 'auditing'>('form')

  function setField(key: keyof FormState, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  function setCompetitor(index: number, value: string) {
    setForm((prev) => {
      const updated = [...prev.competitors]
      updated[index] = value
      return { ...prev, competitors: updated }
    })
  }

  function addCompetitor() {
    if (form.competitors.length < 3) {
      setForm((prev) => ({ ...prev, competitors: [...prev.competitors, ''] }))
    }
  }

  function removeCompetitor(index: number) {
    setForm((prev) => ({
      ...prev,
      competitors: prev.competitors.filter((_, i) => i !== index),
    }))
  }

  function validate(): boolean {
    const newErrors: typeof errors = {}

    if (!form.name.trim()) newErrors.name = 'Client name is required'
    if (!form.websiteUrl.trim()) {
      newErrors.websiteUrl = 'Website URL is required'
    } else if (!isValidUrl(form.websiteUrl)) {
      newErrors.websiteUrl = 'Enter a valid URL (e.g. https://example.com)'
    }
    if (!form.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      newErrors.email = 'Enter a valid email address'
    }
    if (!form.password) {
      newErrors.password = 'Password is required'
    } else if (form.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    }

    const invalidCompetitor = form.competitors.find((c) => c.trim() && !isValidUrl(c))
    if (invalidCompetitor) {
      newErrors.submit = 'One or more competitor URLs are invalid'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return

    setLoading(true)
    setPhase('auditing')

    try {
      const payload = {
        name: form.name.trim(),
        websiteUrl: form.websiteUrl.trim(),
        competitors: form.competitors.filter((c) => c.trim()).map((c) => c.trim()),
        email: form.email.trim().toLowerCase(),
        password: form.password,
      }

      const res = await fetch('/api/clients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await res.json()

      if (!res.ok) {
        setErrors({ submit: data.error ?? 'Failed to create client' })
        setPhase('form')
        setLoading(false)
        return
      }

      router.push(`/admin/clients/${data.id}`)
    } catch {
      setErrors({ submit: 'Network error. Please try again.' })
      setPhase('form')
      setLoading(false)
    }
  }

  if (phase === 'auditing') {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-6 px-4">
        <div className="relative">
          <div className="w-20 h-20 rounded-full border-4 border-indigo-800 border-t-indigo-400 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <Globe size={24} className="text-indigo-400" />
          </div>
        </div>
        <div className="text-center">
          <h2 className="text-xl font-bold text-white">Running Baseline Audit</h2>
          <p className="text-slate-400 mt-2 max-w-sm">
            Analyzing <span className="text-indigo-400">{form.websiteUrl}</span> for GEO signals.
            This usually takes 30–60 seconds…
          </p>
        </div>
        <div className="flex gap-2 mt-2">
          {['Crawling pages', 'Checking AI citations', 'Scoring categories'].map((step, i) => (
            <span
              key={i}
              className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-xs text-slate-400 animate-pulse"
              style={{ animationDelay: `${i * 0.3}s` }}
            >
              {step}
            </span>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/admin"
          className="inline-flex items-center gap-1.5 text-slate-400 hover:text-white text-sm mb-4 transition-colors"
        >
          <ChevronLeft size={15} />
          Back to clients
        </Link>
        <h1 className="text-2xl font-bold text-white">Add New Client</h1>
        <p className="text-slate-400 text-sm mt-1">
          Create a client profile and trigger a baseline GEO audit.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Client details card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <Building size={16} className="text-indigo-400" />
            <h2 className="font-semibold text-white text-sm">Client Details</h2>
          </div>

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Client Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setField('name', e.target.value)}
              placeholder="Acme Corp"
              className={`input ${errors.name ? 'border-red-600 focus:ring-red-500' : ''}`}
            />
            {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name}</p>}
          </div>

          {/* Website URL */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Website URL <span className="text-red-400">*</span>
            </label>
            <input
              type="url"
              value={form.websiteUrl}
              onChange={(e) => setField('websiteUrl', e.target.value)}
              placeholder="https://acmecorp.com"
              className={`input ${errors.websiteUrl ? 'border-red-600 focus:ring-red-500' : ''}`}
            />
            {errors.websiteUrl && <p className="text-red-400 text-xs mt-1">{errors.websiteUrl}</p>}
          </div>

          {/* Competitors */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Primary Competitors
              <span className="text-slate-500 font-normal ml-2">(up to 3 URLs)</span>
            </label>
            <div className="space-y-2">
              {form.competitors.map((comp, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="url"
                    value={comp}
                    onChange={(e) => setCompetitor(i, e.target.value)}
                    placeholder={`https://competitor${i + 1}.com`}
                    className="input flex-1"
                  />
                  {form.competitors.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeCompetitor(i)}
                      className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-950/30 rounded-lg transition-colors"
                      aria-label="Remove competitor"
                    >
                      <Minus size={15} />
                    </button>
                  )}
                </div>
              ))}
              {form.competitors.length < 3 && (
                <button
                  type="button"
                  onClick={addCompetitor}
                  className="flex items-center gap-1.5 text-sm text-indigo-400 hover:text-indigo-300 transition-colors py-1"
                >
                  <Plus size={14} />
                  Add competitor URL
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Create user card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <User size={16} className="text-emerald-400" />
            <h2 className="font-semibold text-white text-sm">Client Portal Access</h2>
          </div>
          <p className="text-slate-500 text-xs -mt-1">
            Create login credentials so the client can access their GEO dashboard.
          </p>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Email <span className="text-red-400">*</span>
            </label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setField('email', e.target.value)}
              placeholder="client@acmecorp.com"
              className={`input ${errors.email ? 'border-red-600 focus:ring-red-500' : ''}`}
            />
            {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email}</p>}
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Password <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="password"
                value={form.password}
                onChange={(e) => setField('password', e.target.value)}
                placeholder="Min. 8 characters"
                className={`input pl-9 ${errors.password ? 'border-red-600 focus:ring-red-500' : ''}`}
              />
            </div>
            {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password}</p>}
          </div>
        </div>

        {/* Submit error */}
        {errors.submit && (
          <div className="px-4 py-3 bg-red-950/50 border border-red-800/60 rounded-xl text-red-400 text-sm">
            {errors.submit}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={loading}
            className="btn-primary px-6 py-2.5"
          >
            {loading ? (
              <>
                <Loader2 size={15} className="animate-spin" />
                Creating…
              </>
            ) : (
              <>
                <Plus size={15} />
                Create Client
              </>
            )}
          </button>
          <Link href="/admin" className="btn-secondary px-6 py-2.5">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  )
}
