const COLORS = [
  'bg-indigo-500', 'bg-violet-500', 'bg-blue-500', 'bg-emerald-500',
  'bg-pink-500', 'bg-orange-500', 'bg-teal-500', 'bg-rose-500',
]

function colorFor(name: string) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return COLORS[Math.abs(hash) % COLORS.length]
}

export default function Avatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' | 'lg' }) {
  const initials = name
    .split(/[_\s-]/)
    .slice(0, 2)
    .map(w => w[0]?.toUpperCase() ?? '')
    .join('') || name.slice(0, 2).toUpperCase()

  const sizeClass = size === 'lg' ? 'w-14 h-14 text-xl' : size === 'sm' ? 'w-7 h-7 text-xs' : 'w-10 h-10 text-sm'

  return (
    <div className={`${sizeClass} ${colorFor(name)} rounded-xl flex items-center justify-center font-bold text-white flex-shrink-0`}>
      {initials}
    </div>
  )
}
