const TAG_COLORS: Record<string, string> = {
  coding: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  research: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  writing: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  automation: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  memory: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  social: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  finance: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  productivity: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  creative: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  reasoning: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
}

const DEFAULT = 'bg-gray-700/50 text-gray-400 border-gray-600/30'

export default function TagBadge({ tag, small }: { tag: string; small?: boolean }) {
  const colors = TAG_COLORS[tag] ?? DEFAULT
  return (
    <span className={`inline-flex items-center border rounded-full font-medium ${small ? 'text-xs px-1.5 py-0' : 'text-xs px-2 py-0.5'} ${colors}`}>
      {tag}
    </span>
  )
}
