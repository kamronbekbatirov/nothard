'use client'

import { useTranslations } from 'next-intl'
import { PersonStanding, Train, Bus } from 'lucide-react'
import type { TripLeg, LatLng } from '@/app/lib/api'
import { cn } from '@/app/lib/utils'

/**
 * Which transit leg the runner is currently on, from their position along the
 * route. Finds the nearest route vertex, then maps that index to a leg via the
 * per-leg point counts. Returns 0 when it can't tell (e.g. no position yet).
 */
export function activeLegIndex(
  legs: TripLeg[],
  route: LatLng[],
  pos: { lat: number; lng: number } | null
): number {
  if (!legs.length || !route.length || !pos) return 0
  // Nearest route vertex to the live position (squared distance is enough).
  let nearest = 0
  let best = Infinity
  for (let i = 0; i < route.length; i++) {
    const dx = route[i][0] - pos.lat
    const dy = route[i][1] - pos.lng
    const d = dx * dx + dy * dy
    if (d < best) {
      best = d
      nearest = i
    }
  }
  // Map the vertex index to a leg via cumulative point counts.
  let cum = 0
  for (let i = 0; i < legs.length; i++) {
    cum += legs[i].points ?? 0
    if (nearest < cum) return i
  }
  return legs.length - 1
}

// Pick an icon + accent colour for a TfL leg mode.
function legStyle(mode: string): { Icon: typeof Train; color: string } {
  const m = mode.toLowerCase()
  if (m.includes('walk')) return { Icon: PersonStanding, color: '#6b7280' }
  if (m.includes('bus')) return { Icon: Bus, color: '#d3341c' }
  // tube / overground / elizabeth-line / dlr / tram / river…
  return { Icon: Train, color: '#2f5d45' }
}

/**
 * Google-Maps-style step-by-step transit directions: which line to take and to
 * which station. Fed by the TfL Journey Planner legs.
 */
export function TransitLegs({
  legs,
  active = -1,
  className,
}: {
  legs: TripLeg[]
  /** Index of the leg currently in progress — highlighted; earlier ones dimmed. */
  active?: number
  className?: string
}) {
  const t = useTranslations('Tracking')
  if (!legs?.length) return null
  return (
    <ol className={cn('flex flex-col gap-1.5', className)}>
      {legs.map((leg, i) => {
        const { Icon, color } = legStyle(leg.mode)
        const isActive = i === active
        const isPast = active >= 0 && i < active
        // Build a localized instruction from the leg's parts (station/line names
        // stay as-is — they're proper nouns) instead of TfL's English summary.
        const isWalk = leg.mode.toLowerCase().includes('walk')
        const text = isWalk
          ? leg.to
            ? t('legWalkTo', { place: leg.to })
            : t('legWalk')
          : leg.line && leg.to
            ? t('legLineTo', { line: leg.line, station: leg.to })
            : leg.summary || leg.line || leg.mode
        return (
          <li
            key={i}
            className={cn(
              'flex items-start gap-2.5 rounded-lg px-2 py-1 transition-colors',
              isActive && 'bg-accent/10',
              isPast && 'opacity-45'
            )}
          >
            <span
              className={cn(
                'mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full',
                isActive && 'nd-pulse ring-2 ring-accent'
              )}
              style={{ backgroundColor: `${color}1a` }}
            >
              <Icon size={14} style={{ color }} />
            </span>
            <span className="min-w-0 flex-1 pt-0.5">
              <span className={cn('block text-[13px] leading-snug', isActive ? 'font-semibold text-ink' : 'text-ink')}>
                {text}
              </span>
              {leg.minutes > 0 && (
                <span className={cn('text-[11.5px]', isActive ? 'text-accent' : 'text-gray')}>
                  {t('minShort', { min: leg.minutes })}
                </span>
              )}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
