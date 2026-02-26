import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { Zap, History } from 'lucide-react'
import SignOutButton from '@/components/SignOutButton'

export default async function ClientLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(authOptions)

  if (!session) redirect('/login')
  if (session.user.role === 'admin') redirect('/admin')

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Top navigation bar */}
      <header className="h-14 bg-slate-900/90 backdrop-blur border-b border-slate-800 sticky top-0 z-30 flex items-center justify-between px-6">
        {/* Brand */}
        <Link href="/client" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 bg-indigo-600/20 border border-indigo-600/40 rounded-lg flex items-center justify-center group-hover:bg-indigo-600/30 transition-colors">
            <Zap size={14} className="text-indigo-400" />
          </div>
          <span className="font-bold text-white text-sm tracking-tight hidden sm:block">GEO Dashboard</span>
        </Link>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          <Link
            href="/client"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all text-sm font-medium"
          >
            Dashboard
          </Link>
          <Link
            href="/client/history"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all text-sm font-medium"
          >
            <History size={14} />
            History
          </Link>
        </nav>

        {/* User info + sign out */}
        <div className="flex items-center gap-3">
          <span className="text-slate-500 text-sm hidden md:block">{session.user.email}</span>
          <SignOutButton />
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}
