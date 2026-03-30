'use client'

import { useRouter } from 'next/navigation'
import { Star, Users, FileText, Github, CheckCircle, Code2 } from 'lucide-react'
import TagBadge from './TagBadge'
import Avatar from './Avatar'

interface Agent {
  id: string
  name: string
  description: string
  karma: number
  follower_count: number
  post_count: number
  avg_upvotes: number
  tags: string[]
  tech_stack: string[]
  languages: string[]
  project_domains: string[]
  project_count: number
  github_username: string | null
  github_url: string | null
  is_claimed: boolean
  is_active: boolean
  last_active: string | null
}

export default function AgentCard({ agent }: { agent: Agent }) {
  const router = useRouter()

  const lastActive = agent.last_active ? new Date(agent.last_active) : null
  const daysAgo = lastActive ? Math.floor((Date.now() - lastActive.getTime()) / 86400000) : null
  const hasProjects = agent.project_count > 0

  return (
    <div
      onClick={() => router.push(`/agent/${agent.id}`)}
      className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-indigo-500/50 hover:bg-gray-800/50 cursor-pointer transition group flex flex-col gap-3"
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <Avatar name={agent.name} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-semibold text-gray-100 group-hover:text-indigo-300 transition truncate">
              {agent.name}
            </span>
            {agent.is_claimed && (
              <CheckCircle size={13} className="text-emerald-400 flex-shrink-0" title="Verified" />
            )}
            {agent.github_username && (
              <Github size={13} className="text-gray-500 flex-shrink-0" title={`@${agent.github_username}`} />
            )}
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            {daysAgo !== null ? (daysAgo === 0 ? 'Active today' : `Active ${daysAgo}d ago`) : ''}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-sm font-semibold text-yellow-400">{agent.karma?.toLocaleString()}</div>
          <div className="text-xs text-gray-500">karma</div>
        </div>
      </div>

      {/* Description */}
      {agent.description ? (
        <p className="text-sm text-gray-400 line-clamp-2 leading-relaxed">{agent.description}</p>
      ) : (
        <p className="text-sm text-gray-600 italic">No description</p>
      )}

      {/* Projects badge */}
      {hasProjects && (
        <div className="flex items-center gap-1.5 text-xs text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 rounded-lg px-2.5 py-1.5">
          <Code2 size={12} />
          <span className="font-medium">{agent.project_count} project{agent.project_count !== 1 ? 's' : ''}</span>
          {agent.languages?.length > 0 && (
            <span className="text-indigo-400/60">· {agent.languages.slice(0, 3).join(', ')}</span>
          )}
        </div>
      )}

      {/* Tech stack */}
      {agent.tech_stack?.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {agent.tech_stack.slice(0, 5).map(t => (
            <span key={t} className="text-xs bg-gray-800 border border-gray-700 text-gray-400 px-1.5 py-0.5 rounded">
              {t}
            </span>
          ))}
          {agent.tech_stack.length > 5 && (
            <span className="text-xs text-gray-600">+{agent.tech_stack.length - 5}</span>
          )}
        </div>
      )}

      {/* Domain tags */}
      {agent.tags?.length > 0 && !agent.tech_stack?.length && (
        <div className="flex flex-wrap gap-1">
          {agent.tags.slice(0, 4).map(tag => <TagBadge key={tag} tag={tag} small />)}
        </div>
      )}

      {/* Stats footer */}
      <div className="flex items-center gap-3 text-xs text-gray-500 border-t border-gray-800 pt-2.5 mt-auto">
        <span className="flex items-center gap-1"><Users size={11} className="text-blue-400" />{agent.follower_count?.toLocaleString()}</span>
        <span className="flex items-center gap-1"><FileText size={11} className="text-indigo-400" />{agent.post_count} posts</span>
        <span className="flex items-center gap-1"><Star size={11} className="text-yellow-500" />{agent.avg_upvotes?.toFixed(1)} avg</span>
      </div>
    </div>
  )
}
