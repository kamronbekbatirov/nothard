'use client'

import { useEffect } from 'react'
import { api, setTokens } from './api'

type TG = {
  initData?: string
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
