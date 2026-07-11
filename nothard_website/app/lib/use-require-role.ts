'use client'

import { useEffect } from 'react'
import { useRouter } from '@/i18n/navigation'
import { useAuth } from './use-auth'
import type { Role } from './api'

const DASH: Record<string, string> = {
  operator: '/admin',
  admin: '/admin',
  agency: '/agency',
  runner: '/runner',
  client: '/profile',
}

/**
 * Gate a panel to specific roles. Unauthenticated users go to /login;
 * authenticated users lacking the role are sent to their own dashboard.
 * Returns { ready } — render the panel only when ready is true.
 */
export function useRequireRole(roles: Role[]) {
  const router = useRouter()
  const { user, loading } = useAuth()

  const allowed = !!user && (roles.includes(user.role) || (roles.includes('operator') && user.role === 'admin'))

  useEffect(() => {
    if (loading) return
    if (!user) {
      router.replace('/login')
    } else if (!allowed) {
      router.replace((DASH[user.role] || '/profile') as any)
    }
  }, [loading, user, allowed, router])

  return { ready: !loading && allowed, user, loading }
}
