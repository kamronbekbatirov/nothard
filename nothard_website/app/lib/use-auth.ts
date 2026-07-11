'use client'

import { useCallback, useEffect, useState } from 'react'
import { api, clearTokens, getAccess, type User } from './api'

type State = { user: User | null; loading: boolean }

/** Reads the stored token and resolves the current user. Reacts to `nh-auth`. */
export function useAuth() {
  const [state, setState] = useState<State>({ user: null, loading: true })

  const refresh = useCallback(async () => {
    if (!getAccess()) {
      setState({ user: null, loading: false })
      return
    }
    try {
      const user = await api.whoami()
      setState({ user, loading: false })
    } catch {
      clearTokens()
      setState({ user: null, loading: false })
    }
  }, [])

  useEffect(() => {
    refresh()
    const onChange = () => refresh()
    window.addEventListener('nh-auth', onChange)
    window.addEventListener('storage', onChange)
    return () => {
      window.removeEventListener('nh-auth', onChange)
      window.removeEventListener('storage', onChange)
    }
  }, [refresh])

  const logout = useCallback(() => {
    clearTokens()
  }, [])

  return { ...state, refresh, logout }
}
