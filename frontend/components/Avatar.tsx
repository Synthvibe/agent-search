const GRADIENTS = [
  'from-indigo-500 to-violet-600',
  'from-blue-500 to-indigo-600',
  'from-violet-500 to-purple-600',
  'from-emerald-500 to-teal-600',
  'from-rose-500 to-pink-600',
  'from-orange-500 to-amber-600',
  'from-cyan-500 to-blue-600',
  'from-fuchsia-500 to-purple-600',
]

function gradientFor(name: string) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return GRADIENTS[Math.abs(hash) % GRADIENTS.length]
}

export default function Avatar({ name, size = 'md', src }: { name: string; size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; src?: string | null }) {
  const initials = name
    .split(/[_\s\-.]/)
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0]?.toUpperCase() ?? '')
    .join('') || name.slice(0, 2).toUpperCase()

  const sizeClass = {
    xs: 'w-6 h-6 text-xs rounded-lg',
    sm: 'w-8 h-8 text-xs rounded-xl',
    md: 'w-11 h-11 text-sm rounded-xl',
    lg: 'w-16 h-16 text-xl rounded-2xl',
    xl: 'w-20 h-20 text-2xl rounded-2xl',
  }[size]

  if (src) {
    return (
      <img src={src} alt={name} className={`${sizeClass} object-cover flex-shrink-0`} />
    )
  }

  return (
    <div className={`${sizeClass} bg-gradient-to-br ${gradientFor(name)} flex items-center justify-center font-bold text-white flex-shrink-0 select-none`}>
      {initials}
    </div>
  )
}
