'use client'

import { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
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
const DEST_ICON = pin('🏠', '#c26a3d')

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
 * mount + on resize fixes it, so the map is correct without a page reload.
 */
function Resizer() {
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
  }, [map])
  return null
}

/** Keeps the whole route (runner + destination) in view as positions change. */
function FitBounds({ points }: { points: LatLng[] }) {
  const map = useMap()
  const key = JSON.stringify(points)
  useEffect(() => {
    if (points.length === 1) {
      map.setView(points[0], 14)
    } else if (points.length > 1) {
      map.fitBounds(L.latLngBounds(points as [number, number][]), {
        padding: [42, 42],
        maxZoom: 15,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  return null
}

export default function LiveMap({
  position,
  dest,
  route,
  waypoint = null,
  estimate = false,
  height = 260,
}: {
  position: { lat: number; lng: number } | null
  dest: { lat: number | null; lng: number | null } | null
  route: LatLng[]
  /** Current transit waypoint (next station) — an accent dot on the route. */
  waypoint?: { lat: number; lng: number } | null
  /** Dash the line to signal an estimated (not real-router) route. */
  estimate?: boolean
  height?: number
}) {
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
  // Dashed = estimated route (no dedicated router for this mode); solid = real.
  const isEstimate = estimate

  return (
    // `isolate` + z-0 keep Leaflet's high internal pane/control z-indexes (400/1000)
    // contained in their own stacking context, below the sticky header (z-30).
    <div style={{ height }} className="isolate relative z-0 overflow-hidden rounded-xl border border-line">
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom
        style={{ height: '100%', width: '100%' }}
        attributionControl={false}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={19} />
        {route.length > 1 && (
          <Polyline
            positions={route as [number, number][]}
            pathOptions={{
              color: '#2f5d45',
              weight: 5,
              opacity: 0.85,
              dashArray: isEstimate ? '8 10' : undefined,
            }}
          />
        )}
        {wayPt && <Marker position={wayPt} icon={WAYPOINT_ICON} />}
        {destPt && <Marker position={destPt} icon={DEST_ICON} />}
        {runnerPt && <Marker position={runnerPt} icon={RUNNER_ICON} />}
        <Resizer />
        <FitBounds points={fitPoints} />
      </MapContainer>
    </div>
  )
}
