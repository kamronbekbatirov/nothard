'use client'

import dynamic from 'next/dynamic'
import { useEffect, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { MapPin } from 'lucide-react'
import { Input } from './field'
import type { GeoResult } from '@/app/lib/api'

const PickerMap = dynamic(() => import('./location-picker-map'), {
  ssr: false,
  loading: () => <div className="nd-skeleton h-[240px] w-full" />,
})

/**
 * Uber-style destination picker: type an address (London-only autocomplete) OR
 * drop / drag a pin on the map. Either way the exact coordinates are captured and
 * the pin is reverse-geocoded to a readable label. Calls `onChange(label, coords)`.
 */
export function LocationPicker({
  value,
  coords,
  placeholder,
  search,
  reverse,
  onChange,
  height = 240,
}: {
  value: string
  coords: { lat: number; lng: number } | null
  placeholder: string
  search: (q: string) => Promise<GeoResult[]>
  reverse: (lat: number, lng: number) => Promise<GeoResult | null>
  onChange: (label: string, coords: { lat: number; lng: number } | null) => void
  height?: number
}) {
  const t = useTranslations('Tracking')
  const [q, setQ] = useState(value)
  const [pin, setPin] = useState<{ lat: number; lng: number } | null>(coords)
  const [results, setResults] = useState<GeoResult[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => setQ(value), [value])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => setPin(coords), [coords?.lat, coords?.lng])

  function onType(v: string) {
    setQ(v)
    window.clearTimeout(timer.current)
    if (v.trim().length < 3) {
      setResults([])
      setOpen(false)
      return
    }
    setLoading(true)
    setOpen(true)
    timer.current = window.setTimeout(async () => {
      try {
        setResults(await search(v.trim()))
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 400)
  }

  function pickResult(r: GeoResult) {
    const c = { lat: r.lat, lng: r.lng }
    setQ(r.label)
    setPin(c)
    setResults([])
    setOpen(false)
    onChange(r.label, c)
  }

  // Pin dropped/dragged on the map → reverse-geocode for a label (fall back to
  // the typed text if the reverse lookup is unavailable).
  async function onMapPick(lat: number, lng: number) {
    const c = { lat, lng }
    setPin(c)
    setOpen(false)
    let label = q
    try {
      const r = await reverse(lat, lng)
      if (r?.label) label = r.label
    } catch {}
    setQ(label)
    onChange(label, c)
  }

  return (
    <div>
      <div className="relative">
        <Input
          value={q}
          onChange={(e) => onType(e.target.value)}
          placeholder={placeholder}
          onFocus={() => results.length > 0 && setOpen(true)}
          onBlur={() => window.setTimeout(() => setOpen(false), 150)}
        />
        {open && (loading || results.length > 0 || q.trim().length >= 3) && (
          <div className="absolute z-[30] mt-1 max-h-56 w-full overflow-y-auto rounded-lg border border-line bg-surface shadow-card">
            {loading && <div className="px-3 py-2.5 text-[13px] text-muted">{t('searching')}</div>}
            {!loading &&
              results.map((r, i) => (
                <button
                  key={i}
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => pickResult(r)}
                  className="flex w-full items-start gap-2 px-3 py-2.5 text-left text-[13px] text-ink-2 transition-colors hover:bg-card"
                >
                  <MapPin size={14} className="mt-0.5 shrink-0 text-accent" />
                  <span className="min-w-0">{r.label}</span>
                </button>
              ))}
            {!loading && results.length === 0 && q.trim().length >= 3 && (
              <div className="px-3 py-2.5 text-[13px] text-muted">{t('noResults')}</div>
            )}
          </div>
        )}
      </div>

      <div className="mt-2 overflow-hidden rounded-xl border border-line">
        <PickerMap coords={pin} onPick={onMapPick} height={height} />
      </div>
      <p className="mt-1.5 text-[11.5px] leading-snug text-gray">{t('pinHint')}</p>
    </div>
  )
}
