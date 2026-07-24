'use client'

import { useTranslations } from 'next-intl'
import { Car, Train, PersonStanding, Bike, type LucideIcon } from 'lucide-react'
import type { TravelMode } from '@/app/lib/api'
import { cn } from '@/app/lib/utils'

export const MODE_ICON: Record<TravelMode, LucideIcon> = {
  car: Car,
  transit: Train,
  walk: PersonStanding,
  cycle: Bike,
}

// Order shown in the picker (mirrors Google/Apple Maps).
export const TRAVEL_MODES: TravelMode[] = ['car', 'transit', 'walk', 'cycle']

/** Segmented Car / Transit / Walk / Cycle picker. */
export function ModeSelector({
  value,
  onChange,
  disabled,
}: {
  value: TravelMode
  onChange: (m: TravelMode) => void
  disabled?: boolean
}) {
  const t = useTranslations('Tracking')
  return (
    <div className="flex gap-1.5">
      {TRAVEL_MODES.map((m) => {
        const Icon = MODE_ICON[m]
        const on = value === m
        return (
          <button
            key={m}
            type="button"
            disabled={disabled}
            onClick={() => onChange(m)}
            className={cn(
              'flex flex-1 flex-col items-center gap-1 rounded-lg border px-1 py-2 text-[11px] font-medium transition-colors disabled:opacity-50',
              on
                ? 'border-accent bg-accent-bg text-accent'
                : 'border-line bg-card text-muted hover:border-accent/40'
            )}
          >
            <Icon size={18} />
            {t(`mode.${m}`)}
          </button>
        )
      })}
    </div>
  )
}
