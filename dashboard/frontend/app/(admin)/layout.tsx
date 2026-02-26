import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { Zap, Users, Bell } from 'lucide-react'
import SignOutButton from '@/components/SignOutButton'

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(authOptions)

  if (!session) redirect('/login')
  if (session.user.role === 'client') redirect('/client')

  return (
    <div className="min-h-screen bg-slate-950 flex">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        {/* Brand */}
        <div className="px-5 py-5 border-b border-slate-800">
          <Link href="/admin" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 bg-indigo-600/20 border border-indigo-600/40 rounded-xl flex items-center justify-center group-hover:bg-indigo-600/30 transition-colors">
              <Zap size={16} className="text-indigo-400" />
            </div>
            <span className="font-bold text-white text-sm tracking-tight">GEO Dashboard</span>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          <Link
            href="/admin"
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-all text-sm font-medium group"
          >
            <Users size={16} className="text-slate-400 group-hover:text-slate-300" />
            All Clients
          </Link>
          <Link
            href="/admin/alerts"
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-all text-sm font-medium group"
          >
            <Bell size={16} className="text-slate-400 group-hover:text-slate-300" />
            Alerts
          </Link>
        </nav>

        {/* Footer */}
        <div className="px-3 py-4 border-t border-slate-800">
          <div className="px-3 py-2">
            <p className="text-xs text-slate-500 truncate">{session.user.email}</p>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-14 bg-slate-900/80 backdrop-blur border-b border-slate-800 flex items-center justify-between px-6 shrink-0">
          <div />
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 bg-indigo-950 border border-indigo-700 text-indigo-400 text-xs font-bold rounded-full tracking-wide">
              ADMIN
            </span>
            <span className="text-slate-400 text-sm hidden sm:block">{session.user.email}</span>
            <SignOutButton />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
