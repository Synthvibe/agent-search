const COLORS: Record<string, string> = {
  coding:         'bg-blue-500/10 text-blue-400 border-blue-500/20',
  research:       'bg-violet-500/10 text-violet-400 border-violet-500/20',
  writing:        'bg-pink-500/10 text-pink-400 border-pink-500/20',
  automation:     'bg-orange-500/10 text-orange-400 border-orange-500/20',
  memory:         'bg-teal-500/10 text-teal-400 border-teal-500/20',
  social:         'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  finance:        'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  productivity:   'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  creative:       'bg-rose-500/10 text-rose-400 border-rose-500/20',
  reasoning:      'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  security:       'bg-red-500/10 text-red-400 border-red-500/20',
  infrastructure: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  // project domains
  web:            'bg-blue-500/10 text-blue-400 border-blue-500/20',
  ml:             'bg-purple-500/10 text-purple-400 border-purple-500/20',
  data:           'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  devtools:       'bg-green-500/10 text-green-400 border-green-500/20',
  agent:          'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  mobile:         'bg-pink-500/10 text-pink-400 border-pink-500/20',
  game:           'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
}

const DEFAULT = 'bg-slate-800/60 text-slate-400 border-slate-700/50'

export default function TagBadge({ tag, small }: { tag: string; small?: boolean }) {
  const cls = COLORS[tag.toLowerCase()] ?? DEFAULT
  return (
    <span className={`tag border ${cls} ${small ? 'text-[10px] px-1.5 py-0' : ''}`}>
      {tag}
    </span>
  )
}
