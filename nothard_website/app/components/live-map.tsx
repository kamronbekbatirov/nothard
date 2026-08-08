'use client'

import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Crosshair, Maximize2, X } from 'lucide-react'
import type { LatLng } from '@/app/lib/api'

// Emoji pin icons built as div-icons — avoids Leaflet's default marker-image
// asset paths breaking under the bundler.
function pin(emoji: string, ring: string) {
  return L.divIcon({
    className: '',
    html: `<div style="width:34px;height:34px;border-radius:50%;background:#fff;border:2px solid ${ring};
      box-shadow:0 2px 6px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;
      font-size:17px;line-height:1">${emoji}</div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  })
}
const RUNNER_ICON = pin('🧍', '#2f5d45')
const HOME_ICON = pin('🏠', '#c26a3d')
const AIRPORT_ICON = pin('✈️', '#2f5d45')

// Small accent dot for the current transit waypoint (next station).
const WAYPOINT_ICON = L.divIcon({
  className: '',
  html: `<div style="width:14px;height:14px;border-radius:50%;background:#2f5d45;border:3px solid #fff;
    box-shadow:0 1px 4px rgba(0,0,0,.35)"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
})

/**
 * Leaflet renders grey tiles when its container is sized after mount (e.g. the
 * trip card appears in an already-open cabinet). Nudging invalidateSize() after
 * mount + on resize fixes it. `bump` re-invalidates when the container resizes
 * (e.g. entering/leaving fullscreen).
 */
function Resizer({ bump }: { bump: unknown }) {
  const map = useMap()
  useEffect(() => {
    const t1 = setTimeout(() => map.invalidateSize(), 150)
    const t2 = setTimeout(() => map.invalidateSize(), 600)
    const onResize = () => map.invalidateSize()
    window.addEventListener('resize', onResize)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
      window.removeEventListener('resize', onResize)
    }
  }, [map, bump])
  return null
}

/** Keeps the whole route (runner + destination) in view as positions change.
 *  Exposes the fit function to the parent so the "recenter" button can reuse it. */
function FitBounds({ points, onReady }: { points: LatLng[]; onReady: (fit: () => void) => void }) {
  const map = useMap()
  const key = JSON.stringify(points)
  useEffect(() => {
    const fit = () => {
      if (points.length === 1) map.setView(points[0], 14)
      else if (points.length > 1) {
        map.fitBounds(L.latLngBounds(points as [number, number][]), { padding: [42, 42], maxZoom: 15 })
      }
    }
    onReady(fit)
    fit()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  return null
}

export default function LiveMap({
  position,
  dest,
  route,
  waypoint = null,
  destKind = 'home',
  estimate = false,
  height = 260,
}: {
  position: { lat: number; lng: number } | null
  dest: { lat: number | null; lng: number | null } | null
  route: LatLng[]
  waypoint?: { lat: number; lng: number } | null
  /** Which pin to use for the leg endpoint: the airport (going to pick up) or home. */
  destKind?: 'home' | 'airport'
  /** Dash the line to signal an estimated (not real-router) route. */
  estimate?: boolean
  height?: number
}) {
  const [fullscreen, setFullscreen] = useState(false)
  const fitRef = useRef<(() => void) | null>(null)

  const runnerPt: LatLng | null = position ? [position.lat, position.lng] : null
  const destPt: LatLng | null =
    dest && dest.lat != null && dest.lng != null ? [dest.lat, dest.lng] : null
  const wayPt: LatLng | null = waypoint ? [waypoint.lat, waypoint.lng] : null

  const fitPoints = useMemo(() => {
    const pts: LatLng[] = []
    if (route.length) pts.push(...route)
    if (runnerPt) pts.push(runnerPt)
    if (destPt) pts.push(destPt)
    return pts
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(route), JSON.stringify(runnerPt), JSON.stringify(destPt)])

  const center: LatLng = runnerPt || destPt || [51.5074, -0.1278] // London fallback

  // Esc closes fullscreen; lock body scroll while open.
  useEffect(() => {
    if (!fullscreen) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setFullscreen(false)
    window.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [fullscreen])

  const CtrlBtn = ({ onClick, label, children }: { onClick: () => void; label: string; children: ReactNode }) => (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      // Theme-aware surface so the icon always contrasts — on a fixed-white button
      // the dark-theme `text-ink` icon was near-invisible and looked un-pressable.
      className="flex h-9 w-9 items-center justify-center rounded-full bg-card text-ink shadow-md ring-1 ring-line transition hover:bg-surface active:scale-95"
    >
      {children}
    </button>
  )

  return (
    // `isolate` + z-0 keep Leaflet's high internal pane/control z-indexes contained
    // below the sticky header. In fullscreen the wrapper covers the viewport.
    <div
      style={fullscreen ? undefined : { height }}
      className={
        fullscreen
          ? 'fixed inset-0 z-[100000] bg-paper'
          : 'isolate relative z-0 overflow-hidden rounded-xl border border-line'
      }
    >
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom
        style={{ height: fullscreen ? '100vh' : '100%', width: '100%' }}
        attributionControl={false}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={19} />
        {route.length > 1 && (
          <Polyline
            positions={route as [number, number][]}
            pathOptions={{ color: '#2f5d45', weight: 5, opacity: 0.85, dashArray: estimate ? '8 10' : undefined }}
          />
        )}
        {wayPt && <Marker position={wayPt} icon={WAYPOINT_ICON} />}
        {destPt && <Marker position={destPt} icon={destKind === 'airport' ? AIRPORT_ICON : HOME_ICON} />}
        {runnerPt && <Marker position={runnerPt} icon={RUNNER_ICON} />}
        <Resizer bump={fullscreen} />
        <FitBounds points={fitPoints} onReady={(fit) => (fitRef.current = fit)} />
      </MapContainer>

      {/* Controls — recenter (find the route again) + fullscreen toggle. */}
      <div className="absolute right-3 top-3 z-[1000] flex flex-col gap-2">
        <CtrlBtn onClick={() => fitRef.current?.()} label="recenter">
          <Crosshair size={17} className="text-accent" />
        </CtrlBtn>
        <CtrlBtn onClick={() => setFullscreen((f) => !f)} label="fullscreen">
          {fullscreen ? <X size={18} /> : <Maximize2 size={16} />}
        </CtrlBtn>
      </div>
    </div>
  )
}
