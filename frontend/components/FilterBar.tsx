'use client'

const TAGS = ['coding', 'research', 'writing', 'automation', 'memory', 'social', 'finance', 'productivity', 'creative', 'reasoning']

interface Filters {
  tag: string
  verified: boolean
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
        <option value="followers">Most followed</option>
        <option value="engagement">Most engaging</option>
        <option value="posts">Most active</option>
        <option value="recent">Recently active</option>
      </select>

      {/* Tag filter */}
      <select
        value={filters.tag}
        onChange={e => set('tag', e.target.value)}
        className="bg-gray-800 border border-gray-700 text-sm rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-indigo-500"
      >
        <option value="">All domains</option>
        {TAGS.map(t => <option key={t} value={t}>{t}</option>)}
      </select>

      {/* Active filter */}
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

      {/* Verified toggle */}
      <button
        onClick={() => set('verified', !filters.verified)}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-sm transition ${
          filters.verified
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
        }`}
      >
        ✓ Verified only
      </button>

      {/* Min karma */}
      <select
        value={filters.min_karma}
        onChange={e => set('min_karma', Number(e.target.value))}
        className="bg-gray-800 border border-gray-700 text-sm rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-indigo-500"
      >
        <option value={0}>Any karma</option>
        <option value={1000}>1k+ karma</option>
        <option value={5000}>5k+ karma</option>
        <option value={10000}>10k+ karma</option>
        <option value={50000}>50k+ karma</option>
      </select>
    </div>
  )
}
