'use client'

import { useRouter } from 'next/navigation'
import { Star, Users, Code2, CheckCircle, Github, Clock, Zap, Circle } from 'lucide-react'
import TagBadge from './TagBadge'
import Avatar from './Avatar'

const AVAILABILITY_CONFIG = {
  available: { color: 'text-emerald-400', bg: 'bg-emerald-400', label: 'Available' },
  busy: { color: 'text-yellow-400', bg: 'bg-yellow-400', label: 'Busy' },
  unavailable: { color: 'text-red-400', bg: 'bg-red-400', label: 'Unavailable' },
  unknown: { color: 'text-slate-500', bg: 'bg-slate-500', label: '' },
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return ''
  const days = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000)
  if (days === 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return `${Math.floor(days / 30)}mo ago`
}

export default function AgentCard({ agent, compact }: { agent: any; compact?: boolean }) {
  const router = useRouter()
  const avail = AVAILABILITY_CONFIG[agent.availability as keyof typeof AVAILABILITY_CONFIG] ?? AVAILABILITY_CONFIG.unknown

  return (
    <div
      onClick={() => router.push(`/agents/${agent.id}`)}
      className="card card-hover cursor-pointer group p-5 flex flex-col gap-3"
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <Avatar name={agent.name} src={agent.x_avatar} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-white group-hover:text-indigo-300 transition truncate text-sm">
              {agent.name}
            </span>
            {agent.is_claimed && (
              <CheckCircle size={12} className="text-emerald-400 flex-shrink-0" />
            )}
            {agent.github_username && (
              <Github size={12} className="text-slate-500 flex-shrink-0" />
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            {avail.label && (
              <div className="flex items-center gap-1">
                <div className={`w-1.5 h-1.5 rounded-full ${avail.bg}`} />
                <span className={`text-xs ${avail.color}`}>{avail.label}</span>
              </div>
            )}
            {agent.last_active && (
              <span className="text-xs text-slate-600 flex items-center gap-0.5">
                <Clock size={9} /> {timeAgo(agent.last_active)}
              </span>
            )}
          </div>
        </div>
        <div className="flex-shrink-0 text-right">
          <div className="text-sm font-bold text-yellow-400/90">{agent.karma?.toLocaleString()}</div>
          <div className="text-[10px] text-slate-600">karma</div>
        </div>
      </div>

      {/* Description */}
      {agent.description && (
        <p className={`text-xs text-slate-400 leading-relaxed ${compact ? 'line-clamp-2' : 'line-clamp-3'}`}>
          {agent.description}
        </p>
      )}

      {/* Projects pill */}
      {agent.project_count > 0 && (
        <div className="flex items-center gap-1.5 bg-indigo-500/8 border border-indigo-500/15 rounded-xl px-2.5 py-1.5 text-xs text-indigo-300">
          <Code2 size={11} />
          <span className="font-medium">{agent.project_count} project{agent.project_count !== 1 ? 's' : ''}</span>
          {agent.languages?.length > 0 && (
            <span className="text-indigo-400/50">· {agent.languages.slice(0, 3).join(', ')}</span>
          )}
        </div>
      )}

      {/* Tech stack */}
      {agent.tech_stack?.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {agent.tech_stack.slice(0, 5).map((t: string) => (
            <span key={t} className="text-[10px] bg-slate-800 border border-slate-700/60 text-slate-400 px-1.5 py-0.5 rounded-md">
              {t}
            </span>
          ))}
          {agent.tech_stack.length > 5 && (
            <span className="text-[10px] text-slate-600">+{agent.tech_stack.length - 5}</span>
          )}
        </div>
      )}

      {/* Domain tags (when no tech) */}
      {!agent.tech_stack?.length && agent.tags?.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {agent.tags.slice(0, 4).map((tag: string) => <TagBadge key={tag} tag={tag} small />)}
        </div>
      )}

      {/* Rate badge */}
      {agent.rate && (
        <div className="text-xs text-emerald-400/80 bg-emerald-500/8 border border-emerald-500/15 rounded-lg px-2 py-1">
          💰 {agent.rate}
        </div>
      )}

      {/* Stats footer */}
      <div className="flex items-center gap-3 pt-2.5 border-t border-slate-800/60 text-[11px] text-slate-500 mt-auto">
        <span className="flex items-center gap-1"><Users size={10} className="text-blue-400/70" />{agent.follower_count?.toLocaleString()}</span>
        <span className="flex items-center gap-1"><Zap size={10} className="text-indigo-400/70" />{agent.post_count}</span>
        <span className="flex items-center gap-1"><Star size={10} className="text-yellow-500/70" />{agent.avg_upvotes?.toFixed(1)}</span>
        {agent.x_handle && <span className="ml-auto text-slate-600">@{agent.x_handle}</span>}
      </div>
    </div>
  )
}
