'use client'

import { useEffect } from 'react'
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// A teardrop pin (div-icon so Leaflet's default marker asset paths don't break).
const PIN = L.divIcon({
  className: '',
  html: `<div style="transform:translate(-50%,-100%);font-size:30px;line-height:1;
    filter:drop-shadow(0 2px 3px rgba(0,0,0,.35))">📍</div>`,
  iconSize: [0, 0],
  iconAnchor: [0, 0],
})

// Greater London — the map is clamped here (this service only covers London).
const LONDON_CENTER: [number, number] = [51.5074, -0.1278]
const LONDON_BOUNDS = L.latLngBounds([51.28, -0.53], [51.705, 0.335])

function ClickHandler({ onPick }: { onPick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

/** Recenter when the pin coords change from outside (search pick / initial). */
function Recenter({ coords }: { coords: { lat: number; lng: number } | null }) {
  const map = useMap()
  useEffect(() => {
    if (coords) map.setView([coords.lat, coords.lng], Math.max(map.getZoom(), 15))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [coords?.lat, coords?.lng])
  return null
}

/** Leaflet paints grey tiles when sized after mount (inside a modal) — nudge it. */
function Resizer() {
  const map = useMap()
  useEffect(() => {
    const t1 = setTimeout(() => map.invalidateSize(), 120)
    const t2 = setTimeout(() => map.invalidateSize(), 500)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [map])
  return null
}

export default function LocationPickerMap({
  coords,
  onPick,
  height = 260,
}: {
  coords: { lat: number; lng: number } | null
  onPick: (lat: number, lng: number) => void
  height?: number
}) {
  return (
    <MapContainer
      center={coords ? [coords.lat, coords.lng] : LONDON_CENTER}
      zoom={coords ? 15 : 11}
      minZoom={10}
      maxBounds={LONDON_BOUNDS}
      maxBoundsViscosity={1}
      style={{ height, width: '100%' }}
      attributionControl={false}
      className="z-0"
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={19} />
      <ClickHandler onPick={onPick} />
      <Recenter coords={coords} />
      <Resizer />
      {coords && (
        <Marker
          position={[coords.lat, coords.lng]}
          icon={PIN}
          draggable
          eventHandlers={{
            dragend: (e) => {
              const ll = (e.target as L.Marker).getLatLng()
              onPick(ll.lat, ll.lng)
            },
          }}
        />
      )}
    </MapContainer>
  )
}
