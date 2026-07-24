'use client'

import dynamic from 'next/dynamic'
import { useTranslations } from 'next-intl'
import { MapPin } from 'lucide-react'
import { Avatar } from './avatar'
import { MODE_ICON } from './travel-mode'
import { TransitLegs, activeLegIndex } from './transit-legs'
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
export function TripCard({ trip, minimal = false }: { trip: TripLive; minimal?: boolean }) {
  const t = useTranslations('Tracking')
  const arrived = trip.status === 'arrived'
  const eta = trip.eta
  const waiting = !trip.position
  const ModeIcon = MODE_ICON[trip.mode] ?? MODE_ICON.car
  // "approx"/"line" are estimates (no dedicated router for this mode yet).
  const isEstimate = trip.routeSource === 'approx' || trip.routeSource === 'line'
  // `minimal` = the client's view: hide the tech status line, battery, and the
  // step-by-step transit legs while the runner is coming (the client only wants
  // to see them once they're travelling together).

  const toPickup = trip.phase === 'toPickup'
  // The client's phase-1 view frames it as "your host will meet you" (the runner
  // is coming to the airport); phase 2 is "on the way to your destination".
  const title = arrived
    ? t('arrivedTitle')
    : minimal && toPickup
      ? t('clientOnWayPickup', { name: trip.runner.name })
      : minimal
        ? t('clientOnWayDest')
        : t('onWayTitle', { name: trip.runner.name })
  // In the client's phase-1 view, don't pin the final home yet (the route is
  // hidden too) — just show the host approaching.
  const showDestPin = !(minimal && toPickup)
  const subLabel = minimal && toPickup ? null : trip.dest.label

  // Which transit leg is in progress (from the live position along the route),
  // plus the next-station dot to drop on the map.
  const showLegs = !arrived && trip.legs.length > 0
  const active = showLegs ? activeLegIndex(trip.legs, trip.route, trip.position) : -1
  const activeLeg = active >= 0 ? trip.legs[active] : undefined
  const waypoint =
    activeLeg && activeLeg.toLat != null && activeLeg.toLng != null
      ? { lat: activeLeg.toLat, lng: activeLeg.toLng }
      : null

  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-card shadow-card">
      <div className="flex items-center gap-3 border-b border-line bg-accent-bg/60 px-4 py-3">
        <Avatar url={trip.runner.photoUrl} name={trip.runner.name || 'N'} size={38} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-[13.5px] font-semibold text-ink">
            <ModeIcon size={15} className="text-accent" />
            {title}
          </div>
          {subLabel && (
            <div className="mt-0.5 flex items-center gap-1 truncate text-[12px] text-muted">
              <MapPin size={12} className="shrink-0" /> {subLabel}
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
        dest={showDestPin ? trip.dest : null}
        route={trip.route}
        waypoint={waypoint}
        estimate={isEstimate}
        height={arrived ? 200 : 260}
      />

      {/* Transit step-by-step (which line / stations), with the active leg
          highlighted. The backend already hides these from the client in phase 1
          (legs is empty there), so a non-empty list means it's OK to show. */}
      {showLegs && (
        <div className="border-t border-line px-4 py-3">
          <div className="mb-2 text-[11.5px] font-medium text-ink-2">{t('howToTravel')}</div>
          <TransitLegs legs={trip.legs} active={active} />
        </div>
      )}

      {/* Tech status + battery — runner/family only, not the client's minimal card. */}
      {!minimal && (
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
      )}
    </div>
  )
}
