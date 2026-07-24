'use client'

import { useEffect, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { MapPin } from 'lucide-react'
import { Input } from './field'
import type { GeoResult } from '@/app/lib/api'

/**
 * Address field with Google-Maps-style suggestions. Typing fetches a debounced
 * list via the injected `search` fn (runner or admin geocode endpoint); picking
 * one stores exact coordinates so a trip never starts/edits against a mistyped or
 * ambiguous address. Free text without a pick falls back to server-side geocoding.
 */
export function AddressField({
  value,
  placeholder,
  search,
  onPick,
}: {
  value: string
  placeholder: string
  search: (q: string) => Promise<GeoResult[]>
  onPick: (label: string, coords: { lat: number; lng: number } | null) => void
}) {
  const t = useTranslations('Tracking')
  const [q, setQ] = useState(value)
  const [results, setResults] = useState<GeoResult[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => {
    setQ(value)
  }, [value])

  function change(v: string) {
    setQ(v)
    onPick(v, null) // typing invalidates any previously picked coordinates
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

  function pick(r: GeoResult) {
    setQ(r.label)
    onPick(r.label, { lat: r.lat, lng: r.lng })
    setResults([])
    setOpen(false)
  }

  return (
    <div className="relative">
      <Input
        value={q}
        onChange={(e) => change(e.target.value)}
        placeholder={placeholder}
        onFocus={() => results.length > 0 && setOpen(true)}
        onBlur={() => window.setTimeout(() => setOpen(false), 150)}
      />
      {open && (loading || results.length > 0 || q.trim().length >= 3) && (
        <div className="absolute z-30 mt-1 max-h-64 w-full overflow-y-auto rounded-lg border border-line bg-surface shadow-card">
          {loading && <div className="px-3 py-2.5 text-[13px] text-muted">{t('searching')}</div>}
          {!loading &&
            results.map((r, i) => (
              <button
                key={i}
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault()
                  pick(r)
                }}
                className="flex w-full items-start gap-2 border-b border-line/60 px-3 py-2.5 text-left text-[13px] leading-snug text-ink last:border-0 hover:bg-accent-bg/60"
              >
                <MapPin size={14} className="mt-0.5 shrink-0 text-accent" />
                <span className="min-w-0">{r.label}</span>
              </button>
            ))}
          {!loading && results.length === 0 && (
            <div className="px-3 py-2.5 text-[13px] text-muted">{t('noResults')}</div>
          )}
        </div>
      )}
    </div>
  )
}
