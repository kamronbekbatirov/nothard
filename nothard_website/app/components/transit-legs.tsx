'use client'

import { useTranslations } from 'next-intl'
import { PersonStanding, Train, Bus } from 'lucide-react'
import type { TripLeg } from '@/app/lib/api'
import { cn } from '@/app/lib/utils'

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
export function TransitLegs({ legs, className }: { legs: TripLeg[]; className?: string }) {
  const t = useTranslations('Tracking')
  if (!legs?.length) return null
  return (
    <ol className={cn('flex flex-col gap-1.5', className)}>
      {legs.map((leg, i) => {
        const { Icon, color } = legStyle(leg.mode)
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
          <li key={i} className="flex items-start gap-2.5">
            <span
              className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full"
              style={{ backgroundColor: `${color}1a` }}
            >
              <Icon size={14} style={{ color }} />
            </span>
            <span className="min-w-0 flex-1 pt-0.5">
              <span className="block text-[13px] leading-snug text-ink">{text}</span>
              {leg.minutes > 0 && (
                <span className="text-[11.5px] text-gray">{t('minShort', { min: leg.minutes })}</span>
              )}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
