'use client'

import dynamic from 'next/dynamic'
import { useTranslations } from 'next-intl'
import { MapPin } from 'lucide-react'
import { Avatar } from './avatar'
import { MODE_ICON } from './travel-mode'
import type { TripLive } from '@/app/lib/api'

// Leaflet touches `window`, so the map is loaded client-side only.
const LiveMap = dynamic(() => import('./live-map'), {
  ssr: false,
  loading: () => <div className="h-[260px] animate-pulse rounded-xl border border-line bg-card" />,
})

/**
 * Live "your host is on the way" card — a map with the runner's moving marker,
 * the destination and the route, plus a headline ETA. Shared by the client
 * cabinet and the read-only family page.
 */
export function TripCard({ trip }: { trip: TripLive }) {
  const t = useTranslations('Tracking')
  const arrived = trip.status === 'arrived'
  const eta = trip.eta
  const waiting = !trip.position
  const ModeIcon = MODE_ICON[trip.mode] ?? MODE_ICON.car
  // "approx"/"line" are estimates (no dedicated router for this mode yet).
  const isEstimate = !!eta && (eta.source === 'approx' || eta.source === 'line')

  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-card shadow-card">
      <div className="flex items-center gap-3 border-b border-line bg-accent-bg/60 px-4 py-3">
        <Avatar url={trip.runner.photoUrl} name={trip.runner.name || 'N'} size={38} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-[13.5px] font-semibold text-ink">
            <ModeIcon size={15} className="text-accent" />
            {arrived ? t('arrivedTitle') : t('onWayTitle', { name: trip.runner.name })}
          </div>
          {trip.dest.label && (
            <div className="mt-0.5 flex items-center gap-1 truncate text-[12px] text-muted">
              <MapPin size={12} className="shrink-0" /> {trip.dest.label}
            </div>
          )}
        </div>
        {!arrived && eta && (
          <div className="shrink-0 text-right">
            <div className="font-display text-[22px] leading-none text-accent">
              {t('etaMin', { min: eta.minutes })}
            </div>
            <div className="text-[11.5px] text-gray">{t('kmLeft', { km: eta.km })}</div>
          </div>
        )}
      </div>

      <LiveMap
        position={trip.position}
        dest={trip.dest}
        route={trip.route}
        estimate={isEstimate}
        height={arrived ? 200 : 260}
      />

      <div className="flex items-center justify-between gap-2 px-4 py-2.5 text-[12px] text-muted">
        <span>
          {arrived
            ? t('arrivedNote')
            : waiting
              ? t('waitingSignal')
              : isEstimate
                ? t('estimateNote')
                : t('liveNote')}
        </span>
        {trip.position?.battery != null && (
          <span className="shrink-0 text-gray">🔋 {trip.position.battery}%</span>
        )}
      </div>
    </div>
  )
}
