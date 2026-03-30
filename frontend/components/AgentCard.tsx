'use client'

import { useRouter } from 'next/navigation'
import { Star, Users, FileText, TrendingUp, CheckCircle } from 'lucide-react'
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
  is_claimed: boolean
  is_active: boolean
  last_active: string | null
}

export default function AgentCard({ agent }: { agent: Agent }) {
  const router = useRouter()

  const lastActive = agent.last_active ? new Date(agent.last_active) : null
  const daysAgo = lastActive ? Math.floor((Date.now() - lastActive.getTime()) / 86400000) : null

  return (
    <div
      onClick={() => router.push(`/agent/${agent.id}`)}
      className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-indigo-500/50 hover:bg-gray-800/50 cursor-pointer transition group"
    >
      <div className="flex items-start gap-3 mb-3">
        <Avatar name={agent.name} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-semibold text-gray-100 group-hover:text-indigo-300 transition truncate">
              {agent.name}
            </span>
            {agent.is_claimed && (
              <CheckCircle size={13} className="text-emerald-400 flex-shrink-0" />
            )}
          </div>
          {daysAgo !== null && (
            <p className="text-xs text-gray-500 mt-0.5">
              Active {daysAgo === 0 ? 'today' : `${daysAgo}d ago`}
            </p>
          )}
        </div>
      </div>

      {agent.description ? (
        <p className="text-sm text-gray-400 line-clamp-2 mb-3 leading-relaxed">{agent.description}</p>
      ) : (
        <p className="text-sm text-gray-600 italic mb-3">No description</p>
      )}

      {agent.tags?.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {agent.tags.slice(0, 4).map(tag => <TagBadge key={tag} tag={tag} small />)}
          {agent.tags.length > 4 && (
            <span className="text-xs text-gray-500">+{agent.tags.length - 4}</span>
          )}
        </div>
      )}

      <div className="flex items-center gap-3 text-xs text-gray-500 border-t border-gray-800 pt-3 mt-1">
        <span className="flex items-center gap-1"><Star size={11} className="text-yellow-500" />{agent.karma?.toLocaleString()}</span>
        <span className="flex items-center gap-1"><Users size={11} className="text-blue-400" />{agent.follower_count?.toLocaleString()}</span>
        <span className="flex items-center gap-1"><FileText size={11} className="text-indigo-400" />{agent.post_count}</span>
        <span className="flex items-center gap-1"><TrendingUp size={11} className="text-emerald-400" />{agent.avg_upvotes?.toFixed(1)} avg</span>
      </div>
    </div>
  )
}
