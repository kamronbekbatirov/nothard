'use client'

import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { ArrowLeft } from 'lucide-react'
import { Link, useRouter } from '@/i18n/navigation'
import { SiteNav } from '@/app/components/site-nav'
import { Footer } from '@/app/components/footer'
import { PackagePicker } from '@/app/components/package-picker'
import { useAuth } from '@/app/lib/use-auth'
import { api } from '@/app/lib/api'
import { PACKAGES, SERVICES, serviceById, coveredServices } from '@/app/lib/data'

/**
 * The public "Услуги" page now uses the exact same guided picker as the cabinet
 * onboarding and the cabinet's "add services": pick a package and/or services in
 * one flow with a running total. Checkout routes a guest to sign-up, and a
 * signed-in client to the cabinet, which owns arrival intake + payment.
 */
export default function ServicesPage() {
  const t = useTranslations('Services')
  const tcommon = useTranslations('Common')
  const router = useRouter()
  const { user } = useAuth()

  const [initialPkg, setInitialPkg] = useState<string | null>(null)
  const [initialServices, setInitialServices] = useState<string[]>([])
  const [owned, setOwned] = useState<string[]>([])

  // Services a signed-in client already has (bought separately OR covered by their
  // active package) — shown as owned so they can't be re-picked/paid twice.
  useEffect(() => {
    if (!user) {
      setOwned([])
      return
    }
    api.me
      .dashboard()
      .then((d) => {
        const bought = (d.services || []).map((s) => s.id)
        const covered = coveredServices(d.package?.id ?? null, SERVICES.map((s) => s.id))
        setOwned(Array.from(new Set([...bought, ...covered])))
      })
      .catch(() => {})
  }, [user])

  // Preselect from the URL: ?pkg=<id> (package) and ?add=<id> (a service).
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const p = params.get('pkg')
    if (p && PACKAGES.some((x) => x.id === p)) setInitialPkg(p)
    const add = params.get('add')
    if (add && serviceById(add)) setInitialServices([add])
    if (p || add || params.get('tab')) window.history.replaceState(null, '', window.location.pathname)
  }, [])

  function checkout(pkgId: string | null, serviceIds: string[]) {
    // Guests sign up first; the cabinet then completes intake + payment.
    if (!user) {
      router.push('/register')
      return
    }
    const qs = new URLSearchParams({ buy: '1' })
    if (pkgId) qs.set('pkg', pkgId)
    if (serviceIds.length) qs.set('add', serviceIds.join(','))
    router.push(`/profile?${qs.toString()}`)
  }

  return (
    <div className="min-h-screen bg-paper">
      <SiteNav />
      <main className="mx-auto max-w-[1100px] px-5 py-10 sm:px-8">
        {user && (
          <Link
            href="/profile"
            className="mb-2 inline-flex items-center gap-1.5 text-[14px] font-medium text-muted transition-colors hover:text-accent"
          >
            <ArrowLeft size={16} /> {tcommon('toCabinet')}
          </Link>
        )}
        <PackagePicker
          onCheckout={checkout}
          buying={false}
          barMode="inline"
          initialPkg={initialPkg}
          initialServices={initialServices}
          ownedServices={owned}
          heading={
            <div className="text-center">
              <h1 className="font-display text-[30px] text-ink sm:text-[38px]">{t('title')}</h1>
              <p className="mx-auto mt-3 max-w-[56ch] text-[15px] leading-relaxed text-muted">
                {t('subtitle')}
              </p>
            </div>
          }
        />
      </main>
      <Footer />
    </div>
  )
}
