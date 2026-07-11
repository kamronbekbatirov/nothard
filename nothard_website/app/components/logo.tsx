import { Link } from '@/i18n/navigation'
import { cn } from '@/app/lib/utils'

/**
 * Wordmark "nothard." — Newsreader 500, tracking -.02em.
 * "not" in ink, "hard." (incl. the dot) in accent green. No icon-square.
 */
export function Logo({
  className,
  size = 26,
  href = '/',
  asLink = true,
}: {
  className?: string
  size?: number
  href?: string
  asLink?: boolean
}) {
  const inner = (
    <span
      className={cn('font-display leading-none select-none', className)}
      style={{ fontSize: size, letterSpacing: '-0.02em' }}
    >
      <span style={{ color: 'rgb(var(--ink))' }}>not</span>
      <span style={{ color: 'rgb(var(--accent))' }}>hard.</span>
    </span>
  )
  if (!asLink) return inner
  return (
    <Link href={href} aria-label="Nothard" className="inline-flex items-center">
      {inner}
    </Link>
  )
}

/** The rounded-square N mark (favicon / avatar fallback). */
export function LogoMark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" style={{ display: 'block', flex: 'none' }}>
      <rect width="32" height="32" rx="8" fill="#1b1a17" />
      <text
        x="16"
        y="16.8"
        textAnchor="middle"
        dominantBaseline="central"
        fontFamily="Newsreader, Georgia, serif"
        fontSize="21"
        fontWeight="600"
        fill="#f4f1ea"
      >
        N
      </text>
    </svg>
  )
}
