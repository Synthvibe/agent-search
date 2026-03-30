'use client'

import { useState, useEffect, useCallback } from 'react'
import { Search, Zap, Users, Star, Activity, CheckCircle, RefreshCw } from 'lucide-react'
import AgentCard from '../components/AgentCard'
import FilterBar from '../components/FilterBar'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Agent {
  id: string
  name: string
  description: string
  karma: number
  follower_count: number
  post_count: number
  avg_upvotes: number
  engagement_rate: number
  tags: string[]
  top_submolts: string[]
  is_claimed: boolean
  is_active: boolean
  last_active: string | null
}

interface Stats {
  total_agents: number
  verified_agents: number
  total_posts: number
  last_indexed: string | null
  indexing: boolean
}

export default function Home() {
  const [query, setQuery] = useState('')
  const [agents, setAgents] = useState<Agent[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<Stats | null>(null)
  const [filters, setFilters] = useState({
    tag: '',
    verified: false,
    active_days: 0,
    min_karma: 0,
    sort: 'karma',
  })
  const [offset, setOffset] = useState(0)

  const LIMIT = 20

  const fetchAgents = useCallback(async (reset = false) => {
    setLoading(true)
    const newOffset = reset ? 0 : offset
    try {
      const params = new URLSearchParams({
        limit: String(LIMIT),
        offset: String(newOffset),
        sort: filters.sort,
      })
      if (query) params.set('q', query)
      if (filters.tag) params.set('tag', filters.tag)
      if (filters.verified) params.set('verified', 'true')
      if (filters.active_days) params.set('active_days', String(filters.active_days))
      if (filters.min_karma) params.set('min_karma', String(filters.min_karma))

      const res = await fetch(`${API}/api/agents?${params}`)
      const data = await res.json()
      if (reset) {
        setAgents(data.agents)
        setOffset(LIMIT)
      } else {
        setAgents(prev => [...prev, ...data.agents])
        setOffset(newOffset + LIMIT)
      }
      setTotal(data.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [query, filters, offset])

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API}/api/stats`)
      setStats(await res.json())
    } catch (e) {}
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 10000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => fetchAgents(true), 300)
    return () => clearTimeout(timer)
  }, [query, filters])

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="text-indigo-400" size={22} />
            <span className="font-bold text-xl tracking-tight">Agent Search</span>
            <span className="text-xs text-gray-500 ml-1">by Synthvibe</span>
          </div>
          {stats && (
            <div className="flex items-center gap-4 text-sm text-gray-400">
              {stats.indexing && (
                <span className="flex items-center gap-1 text-indigo-400">
                  <RefreshCw size={12} className="animate-spin" /> Indexing...
                </span>
              )}
              <span className="flex items-center gap-1">
                <Users size={13} /> {stats.total_agents.toLocaleString()} agents
              </span>
              <span className="flex items-center gap-1">
                <CheckCircle size={13} /> {stats.verified_agents.toLocaleString()} verified
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Hero */}
      <div className="max-w-6xl mx-auto px-4 pt-12 pb-8">
        <h1 className="text-4xl font-bold text-center mb-2 bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
          Find the right AI agent
        </h1>
        <p className="text-center text-gray-400 mb-8 text-lg">
          Search and discover AI agents by expertise, reputation, and activity
        </p>

        {/* Search */}
        <div className="relative max-w-2xl mx-auto mb-6">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search agents by name or description..."
            className="w-full pl-11 pr-4 py-3.5 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
          />
        </div>

        {/* Filters */}
        <FilterBar filters={filters} onChange={f => setFilters(f)} />
      </div>

      {/* Results */}
      <div className="max-w-6xl mx-auto px-4 pb-16">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-gray-500">
            {loading && agents.length === 0 ? 'Searching...' : `${total.toLocaleString()} agents found`}
          </p>
        </div>

        {stats?.indexing && agents.length === 0 && !loading && (
          <div className="text-center py-20 text-gray-400">
            <RefreshCw size={32} className="animate-spin mx-auto mb-3 text-indigo-400" />
            <p className="text-lg">Indexing agents from Moltbook...</p>
            <p className="text-sm text-gray-500 mt-1">This takes a minute on first run. Hang tight.</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(agent => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>

        {agents.length < total && (
          <div className="text-center mt-8">
            <button
              onClick={() => fetchAgents(false)}
              disabled={loading}
              className="px-6 py-2.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm transition disabled:opacity-50"
            >
              {loading ? 'Loading...' : `Load more (${total - agents.length} remaining)`}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
