'use client'

import { useEffect } from 'react'
import { api, setTokens } from './api'

export type TelegramUser = {
  id?: number
  first_name?: string
  last_name?: string
  username?: string
  photo_url?: string
}

type TG = {
  initData?: string
  initDataUnsafe?: { user?: TelegramUser }
  requestContact?: (cb: (result: unknown) => void) => void
  ready?: () => void
  expand?: () => void
  colorScheme?: string
  themeParams?: Record<string, string>
  isVersionAtLeast?: (v: string) => boolean
  setHeaderColor?: (c: string) => void
  setBackgroundColor?: (c: string) => void
  setBottomBarColor?: (c: string) => void
  disableVerticalSwipes?: () => void
  enableClosingConfirmation?: () => void
  BackButton?: { hide?: () => void }
}

// Brand colors (must mirror the design tokens in globals.css / tailwind.config.js)
const ACCENT = '#2f5d45' // calm green — used for the Telegram header bar
const PAPER = '#e9e5dd' // warm paper — page background / bottom bar

export function getTelegram(): TG | null {
  if (typeof window === 'undefined') return null
  return (window as any).Telegram?.WebApp ?? null
}

export function isInTelegram(): boolean {
  const tg = getTelegram()
  return !!(tg && tg.initData && tg.initData.length > 0)
}

/**
 * Brands the native Telegram chrome (header/body colors, expand, lock swipes)
 * whenever we're rendered inside the Mini App. Does NOT log the user in — sign-in
 * is now an explicit action (see `loginWithTelegram`) so opening the bot shows the
 * landing first instead of silently creating an account.
 */
export function useTelegramChrome() {
  useEffect(() => {
    const tg = getTelegram()
    if (!tg) return
    try {
      tg.ready?.()
      tg.expand?.()
      // Brand the native Telegram chrome: green header, paper body/bottom bar.
      tg.setHeaderColor?.(ACCENT)
      tg.setBackgroundColor?.(PAPER)
      tg.setBottomBarColor?.(PAPER)
      // Lock the Mini App open — no swipe-to-minimize/close; only the
      // Telegram close button dismisses it (Bot API 7.7+, no-op if older).
      tg.disableVerticalSwipes?.()
    } catch {}
  }, [])

  return { inTelegram: isInTelegram() }
}

/**
 * Explicit Telegram sign-in from inside the Mini App: exchanges the signed
 * initData for JWT tokens. This is the method that works INSIDE Telegram (the
 * OIDC redirect can't open Telegram-in-Telegram). Returns true on success.
 */
export async function loginWithTelegram(): Promise<boolean> {
  const tg = getTelegram()
  if (!tg?.initData) return false
  try {
    const res = await api.telegram.miniapp({ init_data: tg.initData })
    if ('access_token' in res) {
      setTokens(res.access_token, res.refresh_token)
      return true
    }
    return false
  } catch {
    return false
  }
}

/**
 * The Telegram profile of whoever opened the Mini App (first/last name, username,
 * avatar). Comes from `initDataUnsafe` — fine for PREFILLING the UI, never for
 * trusting server-side; the signed `initData` is what the backend verifies.
 */
export function getTelegramUser(): TelegramUser | null {
  return getTelegram()?.initDataUnsafe?.user ?? null
}

/** A display name built from the Telegram profile ("First Last", else @username). */
export function telegramDisplayName(): string {
  const u = getTelegramUser()
  if (!u) return ''
  const full = [u.first_name, u.last_name].filter(Boolean).join(' ').trim()
  return full || u.username || ''
}

/** requestContact needs Bot API 6.9+; hide the button on older clients. */
export function canRequestContact(): boolean {
  const tg = getTelegram()
  return !!tg?.requestContact && (tg.isVersionAtLeast?.('6.9') ?? false)
}

/**
 * Shows Telegram's native "share your phone number" prompt (Bot API 6.9+).
 * Telegram delivers the number to the BOT as a contact message — it is NEVER
 * returned to the Mini App — so this only resolves whether the user agreed.
 * The caller must then poll the profile for the number the bot saved
 * (see `_save_contact_phone` in api/bot.py).
 */
export function requestTelegramContact(): Promise<boolean> {
  return new Promise((resolve) => {
    const tg = getTelegram()
    if (!tg?.requestContact) return resolve(false)
    let settled = false
    const done = (ok: boolean) => {
      if (!settled) {
        settled = true
        resolve(ok)
      }
    }
    try {
      tg.requestContact((result: unknown) => {
        // Older clients pass a boolean, newer ones an object with `status`.
        const ok =
          result === true ||
          (typeof result === 'object' &&
            result !== null &&
            (result as { status?: string }).status === 'sent')
        done(ok)
      })
    } catch {
      done(false)
    }
    // Some clients never fire the callback when dismissed — don't hang forever.
    setTimeout(() => done(false), 90_000)
  })
}

/**
 * Silent "resume" for the landing: if the Telegram user ALREADY has an account,
 * log them in and return true (so the caller can jump straight to the cabinet).
 * Returns false for first-time users WITHOUT creating an account — they stay on
 * the landing and sign up explicitly.
 */
export async function resumeTelegramSession(): Promise<boolean> {
  const tg = getTelegram()
  if (!tg?.initData) return false
  try {
    const res = await api.telegram.miniapp({ init_data: tg.initData, existing_only: true })
    if ('access_token' in res) {
      setTokens(res.access_token, res.refresh_token)
      return true
    }
  } catch {}
  return false
}
