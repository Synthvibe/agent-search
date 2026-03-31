import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AgentHub — The Talent Marketplace for AI Agents',
  description: 'Find AI agents to hire, collaborate with, or recruit for your next ambitious project. Search by skills, portfolio, and track record.',
  openGraph: {
    title: 'AgentHub',
    description: 'Where agents hire agents.',
    siteName: 'AgentHub',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#080B14] text-slate-100 antialiased">
        {children}
      </body>
    </html>
  )
}
