'use client'

import { useEffect, useState } from 'react'
import { cn } from '@/app/lib/utils'

/**
 * Telegram's own placeholder palette — the gradients its clients draw for users
 * with no profile photo. Index is `abs(user_id) % 7`, same as the apps, so a
 * given person gets the exact colour they're used to seeing in Telegram.
 */
const TG_GRADIENTS: readonly (readonly [string, string])[] = [
  ['#ff845e', '#d45246'], // red
  ['#febb5b', '#f68136'], // orange / yellow
  ['#b694f9', '#6c61df'], // violet
  ['#9ad164', '#46ba43'], // green
  ['#5bcbe3', '#359ad4'], // cyan
  ['#5caffa', '#408acf'], // blue
  ['#ff8aac', '#d95574'], // pink
]

export function telegramGradient(tgId: string | number): readonly [string, string] {
  const n = Math.abs(Number(tgId) || 0) % TG_GRADIENTS.length
  return TG_GRADIENTS[n]
}

/** "Kamron Batirov" → "KB"; "Kamron" → "K" — the way Telegram builds initials. */
function initials(name?: string | null): string {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean).slice(0, 2)
  const s = parts.map((p) => p.charAt(0)).join('').toUpperCase()
  return s || '?'
}

/**
 * Round avatar with a robust fallback. When there's no photo — or the photo URL
 * fails to load (e.g. a Telegram photo that isn't ready / 404s) — it shows the
 * initials on a coloured circle.
 *
 * Pass `tgId` for a Telegram user: the fallback then uses Telegram's own
 * gradient palette instead of the green Nothard circle, so inside the Mini App
 * the avatar looks native and — crucially — looks the SAME whether or not the
 * photo happens to have downloaded yet (it's fetched in a background thread
 * server-side, so it can arrive a moment late).
 */
export function Avatar({
  url,
  name,
  size = 40,
  tgId,
  className,
}: {
  url?: string | null
  name?: string | null
  size?: number
  tgId?: string | number | null
  className?: string
}) {
  const [broken, setBroken] = useState(false)
  useEffect(() => setBroken(false), [url])

  const showImg = !!url && !broken
  const gradient = tgId != null && tgId !== '' ? telegramGradient(tgId) : null

  return showImg ? (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={url!}
      alt={name || ''}
      onError={() => setBroken(true)}
      referrerPolicy="no-referrer"
      style={{ width: size, height: size }}
      className={cn('shrink-0 rounded-full object-cover', className)}
    />
  ) : (
    <span
      style={{
        width: size,
        height: size,
        fontSize: Math.round(size * (gradient ? 0.4 : 0.42)),
        ...(gradient
          ? { backgroundImage: `linear-gradient(180deg, ${gradient[0]}, ${gradient[1]})` }
          : {}),
      }}
      className={cn(
        'flex shrink-0 select-none items-center justify-center rounded-full font-semibold text-white',
        !gradient && 'bg-accent',
        className
      )}
    >
      {gradient ? initials(name) : initials(name).charAt(0)}
    </span>
  )
}
