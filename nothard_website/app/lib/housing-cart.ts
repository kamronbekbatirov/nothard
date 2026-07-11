'use client'

// Browser-persisted housing selections for the search page. Favourites, the
// shortlist and pasted links survive reloads and, crucially, a sign-up: when a
// guest hits "submit" we stash the selection and a pending flag, then replay it
// into the cabinet once they're authenticated (`flushPendingHousing`).

import { api } from './api'

const FAV = 'nh_fav'
const SHORTLIST = 'nh_shortlist'
const LINKS = 'nh_links'
const PENDING = 'nh_pending_housing'

export type ShortlistItem = { id: number; addr: string; priceGBP: number }

function read<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback
  try {
    const v = localStorage.getItem(key)
    return v ? (JSON.parse(v) as T) : fallback
  } catch {
    return fallback
  }
}
function write(key: string, val: unknown) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(key, JSON.stringify(val))
  } catch {}
}

export const cart = {
  getFav: () => new Set(read<number[]>(FAV, [])),
  setFav: (s: Set<number>) => write(FAV, [...s]),
  getShortlist: () => read<ShortlistItem[]>(SHORTLIST, []),
  setShortlist: (items: ShortlistItem[]) => write(SHORTLIST, items),
  getLinks: () => read<string[]>(LINKS, []),
  setLinks: (urls: string[]) => write(LINKS, urls),
  markPending: () => write(PENDING, true),
  clear: () => {
    write(SHORTLIST, [])
    write(LINKS, [])
    if (typeof window !== 'undefined') localStorage.removeItem(PENDING)
  },
}

/** After sign-in: replay a guest's saved shortlist + links into the cabinet.
 * Returns how many housing items were created (0 if nothing pending). */
export async function flushPendingHousing(): Promise<number> {
  if (typeof window === 'undefined') return 0
  if (!read<boolean>(PENDING, false)) return 0
  const shortlist = read<ShortlistItem[]>(SHORTLIST, [])
  const links = read<string[]>(LINKS, [])
  let n = 0
  for (const p of shortlist) {
    try {
      await api.me.addHousing({
        source: 'catalog',
        ref: `catalog:${p.id}`,
        title: p.addr,
        priceGBP: p.priceGBP,
        addr: p.addr,
      })
      n++
    } catch {}
  }
  for (const url of links) {
    let host = url
    try {
      host = new URL(url).hostname.replace(/^www\./, '')
    } catch {}
    try {
      await api.me.addHousing({ source: 'link', ref: url, title: host })
      n++
    } catch {}
  }
  cart.clear()
  return n
}
