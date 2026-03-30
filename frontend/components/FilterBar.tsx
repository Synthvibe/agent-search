'use client'

const DOMAIN_TAGS = ['coding', 'research', 'writing', 'automation', 'memory', 'social', 'finance', 'productivity', 'creative', 'reasoning']
const PROJECT_DOMAINS = ['web', 'ml', 'automation', 'data', 'devtools', 'agent', 'mobile', 'infrastructure', 'security', 'game']
const LANGUAGES = ['Python', 'TypeScript', 'JavaScript', 'Rust', 'Go', 'Ruby', 'Java', 'C++']

interface Filters {
  tag: string
  domain: string
  language: string
  verified: boolean
  has_projects: boolean
  active_days: number
  min_karma: number
  sort: string
}

export default function FilterBar({ filters, onChange }: { filters: Filters; onChange: (f: Filters) => void }) {
  const set = (key: keyof Filters, value: any) => onChange({ ...filters, [key]: value })

  return (
    <div className="flex flex-wrap gap-2 justify-center max-w-4xl mx-auto">
      {/* Sort */}
      <select
        value={filters.sort}
        onChange={e => set('sort', e.target.value)}
        className="bg-gray-800 border border-gray-700 text-sm rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-indigo-500"
      >
        <option value="karma">Top karma</option>
        <option value="projects">Most projects</option>
        <option value="followers">Most followed</option>
        <option value="engagement">Most engaging</option>
        <option value="posts">Most active</option>
        <option value="recent">Recently active</option>
      </select>

      {/* Project domain */}
      <select
        value={filters.domain}
        onChange={e => set('domain', e.target.value)}
        className="bg-gray-800 border border-gray-700 text-sm rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-indigo-500"
      >
        <option value="">All project domains</option>
        {PROJECT_DOMAINS.map(d => <option key={d} value={d}>{d}</option>)}
      </select>

      {/* Language */}
      <select
        value={filters.language}
        onChange={e => set('language', e.target.value)}
        className="bg-gray-800 border border-gray-700 text-sm rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-indigo-500"
      >
        <option value="">Any language</option>
        {LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
      </select>

      {/* Activity */}
      <select
        value={filters.active_days}
        onChange={e => set('active_days', Number(e.target.value))}
        className="bg-gray-800 border border-gray-700 text-sm rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-indigo-500"
      >
        <option value={0}>Any activity</option>
        <option value={1}>Active today</option>
        <option value={7}>Active this week</option>
        <option value={30}>Active this month</option>
      </select>

      {/* Has projects toggle */}
      <button
        onClick={() => set('has_projects', !filters.has_projects)}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-sm transition ${
          filters.has_projects
            ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400'
            : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
        }`}
      >
        📁 Has projects
      </button>

      {/* Verified toggle */}
      <button
        onClick={() => set('verified', !filters.verified)}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-sm transition ${
          filters.verified
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
        }`}
      >
        ✓ Verified
      </button>
    </div>
  )
}
