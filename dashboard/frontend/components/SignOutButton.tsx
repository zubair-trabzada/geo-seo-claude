'use client'

import { signOut } from 'next-auth/react'
import { LogOut } from 'lucide-react'

export default function SignOutButton() {
  return (
    <button
      onClick={() => signOut({ callbackUrl: '/login' })}
      className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors text-sm px-2 py-1 rounded-lg hover:bg-slate-800"
      aria-label="Sign out"
    >
      <LogOut size={15} />
      <span className="hidden sm:inline">Sign out</span>
    </button>
  )
}
