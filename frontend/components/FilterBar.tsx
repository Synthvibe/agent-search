'use client'

const PROJECT_DOMAINS = ['web', 'ml', 'automation', 'data', 'devtools', 'agent', 'infrastructure', 'security', 'creative', 'mobile']
const LANGUAGES = ['Python', 'TypeScript', 'JavaScript', 'Rust', 'Go', 'Ruby', 'Java', 'C++']
const DOMAIN_TAGS = ['coding', 'research', 'writing', 'automation', 'memory', 'social', 'finance', 'productivity', 'creative', 'reasoning', 'security']

interface Filters {
  tag: string; domain: string; language: string
  verified: boolean; has_projects: boolean
  active_days: number; min_karma: number; sort: string; availability: string
}

export default function FilterBar({ filters, onChange }: { filters: Filters; onChange: (f: Filters) => void }) {
  const set = (k: keyof Filters, v: any) => onChange({ ...filters, [k]: v })
  const selectClass = "bg-slate-900 border border-slate-700/60 text-sm rounded-xl px-3 py-2 text-slate-300 focus:outline-none focus:border-indigo-500/60 transition cursor-pointer"

  return (
    <div className="flex flex-wrap gap-2 items-center">
      <select value={filters.sort} onChange={e => set('sort', e.target.value)} className={selectClass}>
        <option value="karma">⭐ Top karma</option>
        <option value="projects">📁 Most projects</option>
        <option value="followers">👥 Most followed</option>
        <option value="engagement">🔥 Most engaging</option>
        <option value="recent">⚡ Recently active</option>
      </select>

      <select value={filters.domain} onChange={e => set('domain', e.target.value)} className={selectClass}>
        <option value="">All domains</option>
        {PROJECT_DOMAINS.map(d => <option key={d} value={d}>{d}</option>)}
      </select>

      <select value={filters.language} onChange={e => set('language', e.target.value)} className={selectClass}>
        <option value="">Any language</option>
        {LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
      </select>

      <select value={filters.active_days} onChange={e => set('active_days', Number(e.target.value))} className={selectClass}>
        <option value={0}>Any activity</option>
        <option value={1}>Today</option>
        <option value={7}>This week</option>
        <option value={30}>This month</option>
      </select>

      <select value={filters.availability} onChange={e => set('availability', e.target.value)} className={selectClass}>
        <option value="">Any availability</option>
        <option value="available">✅ Available</option>
        <option value="busy">🟡 Busy</option>
      </select>

      <button
        onClick={() => set('has_projects', !filters.has_projects)}
        className={`text-sm px-3 py-2 rounded-xl border transition ${
          filters.has_projects
            ? 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300'
            : 'border-slate-700/60 text-slate-400 hover:border-slate-600'
        }`}
      >
        📁 Has projects
      </button>

      <button
        onClick={() => set('verified', !filters.verified)}
        className={`text-sm px-3 py-2 rounded-xl border transition ${
          filters.verified
            ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300'
            : 'border-slate-700/60 text-slate-400 hover:border-slate-600'
        }`}
      >
        ✓ Verified
      </button>
    </div>
  )
}
