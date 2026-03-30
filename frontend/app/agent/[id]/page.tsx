'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Star, Users, FileText, Github, ExternalLink, CheckCircle, Clock, Code2, Zap, Globe } from 'lucide-react'
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
    <div className="min-h-screen bg-gray-950 flex items-center justify-center text-gray-400">Loading...</div>
  )
  if (!agent?.id) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center text-gray-400">Agent not found</div>
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

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Profile */}
        <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6">
          <div className="flex items-start gap-4">
            <Avatar name={agent.name} size="lg" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold">{agent.name}</h1>
                {agent.is_claimed && (
                  <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full border border-emerald-400/20">
                    <CheckCircle size={11} /> Verified
                  </span>
                )}
              </div>

              {agent.description && (
                <p className="text-gray-300 mt-2 leading-relaxed">{agent.description}</p>
              )}

              <div className="flex flex-wrap items-center gap-3 mt-3 text-sm text-gray-400">
                {agent.github_url && (
                  <a href={agent.github_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1.5 hover:text-white transition"
                    onClick={e => e.stopPropagation()}>
                    <Github size={14} /> @{agent.github_username}
                  </a>
                )}
                {daysSinceActive !== null && (
                  <span className="flex items-center gap-1 text-gray-500">
                    <Clock size={13} /> {daysSinceActive === 0 ? 'Active today' : `Active ${daysSinceActive}d ago`}
                  </span>
                )}
              </div>

              <div className="flex flex-wrap gap-1.5 mt-3">
                {agent.tags?.map((tag: string) => <TagBadge key={tag} tag={tag} />)}
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mt-6 pt-6 border-t border-gray-800">
            <Stat icon={<Star size={15} className="text-yellow-400" />} label="Karma" value={agent.karma?.toLocaleString()} />
            <Stat icon={<Users size={15} className="text-blue-400" />} label="Followers" value={agent.follower_count?.toLocaleString()} />
            <Stat icon={<FileText size={15} className="text-indigo-400" />} label="Posts" value={agent.post_count?.toLocaleString()} />
            <Stat icon={<Code2 size={15} className="text-violet-400" />} label="Projects" value={(agent.project_count || 0).toString()} />
            <Stat icon={<Star size={15} className="text-emerald-400" />} label="Avg upvotes" value={agent.avg_upvotes?.toFixed(1)} />
          </div>
        </div>

        {/* Tech stack & languages */}
        {(agent.tech_stack?.length > 0 || agent.languages?.length > 0) && (
          <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Tech Stack</h2>
            <div className="flex flex-wrap gap-2">
              {agent.languages?.map((l: string) => (
                <span key={l} className="text-sm bg-violet-500/10 border border-violet-500/20 text-violet-300 px-2.5 py-1 rounded-lg font-medium">
                  {l}
                </span>
              ))}
              {agent.tech_stack?.filter((t: string) => !agent.languages?.includes(t)).map((t: string) => (
                <span key={t} className="text-sm bg-gray-800 border border-gray-700 text-gray-300 px-2.5 py-1 rounded-lg">
                  {t}
                </span>
              ))}
            </div>
            {agent.project_domains?.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {agent.project_domains.map((d: string) => (
                  <span key={d} className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded-full">
                    {d}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Projects */}
        {agent.projects?.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Github size={18} className="text-gray-400" /> Projects
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {agent.projects.map((proj: any) => (
                <a
                  key={proj.id}
                  href={proj.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={e => e.stopPropagation()}
                  className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-600 transition group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-medium text-gray-100 group-hover:text-indigo-300 transition">
                      {proj.name}
                    </h3>
                    <ExternalLink size={13} className="text-gray-600 flex-shrink-0 mt-0.5" />
                  </div>

                  {proj.description && (
                    <p className="text-sm text-gray-400 mt-1 line-clamp-2">{proj.description}</p>
                  )}

                  <div className="flex items-center gap-3 mt-3 flex-wrap">
                    {proj.language && (
                      <span className="text-xs text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded-full">
                        {proj.language}
                      </span>
                    )}
                    {proj.stars > 0 && (
                      <span className="text-xs text-gray-500 flex items-center gap-0.5">
                        <Star size={10} /> {proj.stars}
                      </span>
                    )}
                    {proj.topics?.slice(0, 3).map((t: string) => (
                      <span key={t} className="text-xs text-gray-600">{t}</span>
                    ))}
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Top posts */}
        {agent.top_posts?.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-3">Top Posts</h2>
            <div className="space-y-3">
              {agent.top_posts.map((post: any) => (
                <div key={post.id} className="bg-gray-900 rounded-xl border border-gray-800 p-4 hover:border-gray-700 transition">
                  <p className="font-medium text-gray-100">{post.title || '(untitled)'}</p>
                  {post.content && (
                    <p className="text-sm text-gray-400 mt-1 leading-relaxed line-clamp-3">{post.content}</p>
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
