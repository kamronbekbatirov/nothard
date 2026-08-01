'use client'

import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Check, ChevronRight, PersonStanding, Bus } from 'lucide-react'
import { MODE_ICON } from './travel-mode'
import type { RouteOption, TripLeg } from '@/app/lib/api'
import { cn } from '@/app/lib/utils'

/** Compact "🚶 › Piccadilly › Elizabeth line › 🚶" strip so a transit option is
 *  legible at a glance — which lines it uses — before picking it. */
function LegStrip({ legs }: { legs: TripLeg[] }) {
  if (!legs.length) return null
  return (
    <span className="mt-1 flex flex-wrap items-center gap-x-1 gap-y-1">
      {legs.map((leg, i) => {
        const walk = leg.mode.toLowerCase().includes('walk')
        const bus = leg.mode.toLowerCase().includes('bus')
        return (
          <span key={i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={11} className="text-gray-lt" />}
            {walk ? (
              <PersonStanding size={14} className="text-gray" />
            ) : bus ? (
              <span className="flex items-center gap-0.5 rounded bg-[#d3341c]/12 px-1.5 py-0.5 text-[11px] font-medium text-[#d3341c]">
                <Bus size={11} /> {leg.line || ''}
              </span>
            ) : (
              <span className="rounded bg-accent/12 px-1.5 py-0.5 text-[11px] font-medium text-accent">
                {leg.line || leg.mode}
              </span>
            )}
          </span>
        )
      })}
    </span>
  )
}

/**
 * A list of candidate routes (car / transit alternatives / walk / cycle) the
 * runner or operator picks from — instead of the app auto-choosing the fastest.
 * `load` fetches the options; `onChoose` applies the picked one.
 */
export function RouteOptions({
  load,
  onChoose,
  currentSource,
}: {
  load: () => Promise<RouteOption[]>
  onChoose: (opt: RouteOption) => Promise<void>
  currentSource?: string | null
}) {
  const t = useTranslations('Tracking')
  const [options, setOptions] = useState<RouteOption[] | null>(null)
  const [choosing, setChoosing] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    load()
      .then((o) => alive && setOptions(o))
      .catch(() => alive && setOptions([]))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (options === null) {
    return <div className="nd-skeleton h-16 rounded-lg" />
  }
  if (options.length === 0) {
    return <p className="text-center text-[12.5px] text-muted">{t('routeNone')}</p>
  }

  return (
    <div className="flex flex-col gap-2">
      {options.map((o, i) => {
        const Icon = MODE_ICON[o.mode] ?? MODE_ICON.car
        const estimate = o.source === 'approx' || o.source === 'line'
        const busy = choosing === o.id
        return (
          <button
            key={o.id}
            disabled={busy}
            onClick={async () => {
              setChoosing(o.id)
              try {
                await onChoose(o)
              } finally {
                setChoosing(null)
              }
            }}
            className={cn(
              'flex items-center gap-3 rounded-lg border bg-card px-3 py-2.5 text-left transition-colors hover:border-accent/40',
              i === 0 ? 'border-accent/30' : 'border-line'
            )}
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-bg">
              <Icon size={16} className="text-accent" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-1.5 text-[13.5px] font-semibold text-ink">
                {t(`mode.${o.mode}`)}
                {i === 0 && (
                  <span className="rounded-full bg-accent/15 px-1.5 py-0.5 text-[9.5px] font-semibold uppercase text-accent">
                    {t('routeFastest')}
                  </span>
                )}
                {estimate && <span className="text-[11px] font-normal text-gray">≈</span>}
              </span>
              <span className="text-[12px] text-muted">
                {t('etaMin', { min: o.minutes })} · {t('kmLeft', { km: o.km })}
              </span>
              {/* Which lines the route uses — walk icon + line chips. */}
              {o.legs.length > 0 && <LegStrip legs={o.legs} />}
            </span>
            {busy && <span className="shrink-0 text-[11px] text-accent">…</span>}
            <Check size={15} className="shrink-0 text-gray-lt" />
          </button>
        )
      })}
    </div>
  )
}
