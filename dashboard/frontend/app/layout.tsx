import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Providers } from '@/app/providers'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'GEO Dashboard',
  description: 'AI Search Visibility Platform — track your Generative Engine Optimization score',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`dark ${inter.variable}`}>
      <body className="bg-slate-950 text-slate-100 antialiased font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
