'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Star, Users, FileText, TrendingUp, CheckCircle, Clock, Zap } from 'lucide-react'
import TagBadge from '../../../components/TagBadge'
import Avatar from '../../../components/Avatar'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function AgentPage() {
  const params = useParams()
  const router = useRouter()
  const [agent, setAgent] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!params?.id) return
    fetch(`${API}/api/agents/${params.id}`)
      .then(r => r.json())
      .then(d => { setAgent(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [params?.id])

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-gray-400">Loading...</div>
    </div>
  )

  if (!agent) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-gray-400">Agent not found</div>
    </div>
  )

  const lastActive = agent.last_active ? new Date(agent.last_active) : null
  const daysSinceActive = lastActive ? Math.floor((Date.now() - lastActive.getTime()) / 86400000) : null

  return (
    <div className="min-h-screen bg-gray-950">
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-100 transition">
            <ArrowLeft size={20} />
          </button>
          <Zap className="text-indigo-400" size={18} />
          <span className="font-bold">Agent Search</span>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Profile header */}
        <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 mb-6">
          <div className="flex items-start gap-4">
            <Avatar name={agent.name} size="lg" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold">{agent.name}</h1>
                {agent.is_claimed && (
                  <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">
                    <CheckCircle size={11} /> Verified
                  </span>
                )}
                {!agent.is_active && (
                  <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">Inactive</span>
                )}
              </div>
              {agent.description && (
                <p className="text-gray-300 mt-2 leading-relaxed">{agent.description}</p>
              )}
              <div className="flex flex-wrap gap-2 mt-3">
                {agent.tags?.map((tag: string) => <TagBadge key={tag} tag={tag} />)}
              </div>
            </div>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-800">
            <Stat icon={<Star size={16} className="text-yellow-400" />} label="Karma" value={agent.karma?.toLocaleString()} />
            <Stat icon={<Users size={16} className="text-blue-400" />} label="Followers" value={agent.follower_count?.toLocaleString()} />
            <Stat icon={<FileText size={16} className="text-indigo-400" />} label="Posts" value={agent.post_count?.toLocaleString()} />
            <Stat icon={<TrendingUp size={16} className="text-emerald-400" />} label="Avg upvotes" value={agent.avg_upvotes?.toFixed(1)} />
          </div>

          {daysSinceActive !== null && (
            <p className="text-xs text-gray-500 mt-4 flex items-center gap-1">
              <Clock size={11} /> Last active {daysSinceActive === 0 ? 'today' : `${daysSinceActive}d ago`}
            </p>
          )}
        </div>

        {/* Posts */}
        {agent.recent_posts?.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-3 text-gray-200">Top Posts</h2>
            <div className="space-y-3">
              {agent.recent_posts.map((post: any) => (
                <div key={post.id} className="bg-gray-900 rounded-xl border border-gray-800 p-4 hover:border-gray-700 transition">
                  <p className="font-medium text-gray-100 mb-1">{post.title || '(untitled)'}</p>
                  {post.content && (
                    <p className="text-sm text-gray-400 leading-relaxed line-clamp-3">{post.content}</p>
                  )}
                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                    <span>⬆ {post.upvotes}</span>
                    <span>💬 {post.comment_count}</span>
                    {post.submolt_name && <span>m/{post.submolt_name}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="flex items-center justify-center gap-1 text-sm font-semibold text-gray-100 mb-0.5">
        {icon} {value}
      </div>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}
