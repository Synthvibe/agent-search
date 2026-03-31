import { Users, Code2, CheckCircle, FileText, Briefcase } from 'lucide-react'

export default function StatsBar({ stats }: { stats: any }) {
  const items = [
    { icon: Users, value: stats.total_agents?.toLocaleString(), label: 'Agents indexed', color: 'text-blue-400' },
    { icon: CheckCircle, value: stats.verified_agents?.toLocaleString(), label: 'Verified', color: 'text-emerald-400' },
    { icon: Code2, value: stats.total_projects?.toLocaleString(), label: 'Projects', color: 'text-indigo-400' },
    { icon: FileText, value: stats.total_posts?.toLocaleString(), label: 'Posts scraped', color: 'text-violet-400' },
    { icon: Briefcase, value: stats.available_agents?.toLocaleString() || '—', label: 'Available to hire', color: 'text-yellow-400' },
  ]

  return (
    <div className="border-b border-slate-800/60 bg-slate-900/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-center gap-8 overflow-x-auto">
        {items.map(({ icon: Icon, value, label, color }) => (
          <div key={label} className="flex items-center gap-2 flex-shrink-0">
            <Icon size={13} className={color} />
            <span className="text-sm font-semibold text-white">{value}</span>
            <span className="text-xs text-slate-500">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
