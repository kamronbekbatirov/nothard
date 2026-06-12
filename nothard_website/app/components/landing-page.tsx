'use client'

import { useState, useRef, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { ShoppingCart, ArrowRight, Check } from 'lucide-react'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '../components/ui/card'
import { useToast } from '../components/ui/use-toast'
import { Cart } from './cart'
import { Navbar } from './navbar'
import { Footer } from './footer'

type CartItem = {
  name: string
  price: string
  priceUSD: string
  priceUZS: string
  type: 'package' | 'service'
}

const SERVICE_KEYS = [
  { key: 'airportPublic', price: '£99', priceUSD: '$130', priceUZS: '1,612,000' },
  { key: 'airportTaxi', price: '£228', priceUSD: '$300', priceUZS: '3,720,000' },
  { key: 'sim', price: '£15', priceUSD: '$20', priceUZS: '248,000' },
  { key: 'oyster', price: '£15', priceUSD: '$20', priceUZS: '248,000' },
  { key: 'housingSearch', price: '£38', priceUSD: '$50', priceUZS: '620,000' },
  { key: 'tempHousing', price: '£38', priceUSD: '$50', priceUZS: '620,000' },
  { key: 'moving', price: '£76', priceUSD: '$100', priceUZS: '1,240,000' },
  { key: 'gp', price: '£76', priceUSD: '$100', priceUZS: '1,240,000' },
  { key: 'support', price: '£76', priceUSD: '$100', priceUZS: '1,240,000' },
  { key: 'neighborhood', price: '£38', priceUSD: '$50', priceUZS: '620,000' },
  { key: 'utilities', price: '£76', priceUSD: '$100', priceUZS: '1,240,000' },
  { key: 'bank', price: '£38', priceUSD: '$50', priceUZS: '620,000' },
  { key: 'lease', price: '£38', priceUSD: '$50', priceUZS: '620,000' },
  { key: 'docs', price: '£20', priceUSD: '$26', priceUZS: '322,000' },
] as const

const PACKAGE_KEYS = [
  { key: 'meet', price: '£114', priceUSD: '$150', priceUZS: '1,860,000', includesCount: 4, featured: false },
  { key: 'housing', price: '£342', priceUSD: '$450', priceUZS: '5,580,000', includesCount: 5, featured: true },
  { key: 'premium', price: '£647', priceUSD: '$850', priceUZS: '10,540,000', includesCount: 8, featured: false },
] as const

function LandingPageContent() {
  const t = useTranslations('Landing')
  const tPackages = useTranslations('Packages')
  const tServices = useTranslations('Services')
  const currencySum = t('currency.sum')

  const formatUZS = (raw: string) => `${raw} ${currencySum}`

  const [cartItems, setCartItems] = useState<{ packages: CartItem[]; services: CartItem[] }>({
    packages: [],
    services: [],
  })
  const [isCartOpen, setIsCartOpen] = useState(false)

  const { toast } = useToast()

  const packagesRef = useRef<HTMLDivElement>(null)
  const servicesRef = useRef<HTMLDivElement>(null)

  const searchParams = useSearchParams()

  useEffect(() => {
    const section = searchParams.get('section')
    if (section) {
      const element = document.getElementById(section)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' })
      }
    }
  }, [searchParams])

  const scrollToSection = (ref: React.RefObject<HTMLDivElement>) => {
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const addToCart = (name: string, price: string, priceUSD: string, priceUZS: string, type: 'package' | 'service') => {
    if (type === 'package') {
      if (cartItems.packages.length > 0) {
        toast({
          title: t('errors.error'),
          description: t('errors.packageExists'),
          variant: 'destructive',
          duration: 5000,
        })
        return
      }
      setCartItems((prev) => ({ ...prev, packages: [{ name, price, priceUSD, priceUZS, type }] }))
    } else {
      if (cartItems.services.some((s) => s.name === name)) {
        toast({
          title: t('errors.error'),
          description: t('errors.serviceExists'),
          variant: 'destructive',
          duration: 5000,
        })
        return
      }
      setCartItems((prev) => ({
        ...prev,
        services: [...prev.services, { name, price, priceUSD, priceUZS, type }],
      }))
    }
    toast({ title: t('errors.success'), description: t('errors.added'), duration: 5000 })
  }

  const removeFromCart = (item: CartItem) => {
    if (item.type === 'package') {
      setCartItems((prev) => ({ ...prev, packages: [] }))
    } else {
      setCartItems((prev) => ({
        ...prev,
        services: prev.services.filter((s) => s.name !== item.name),
      }))
    }
    toast({ title: t('errors.success'), description: t('errors.removed'), duration: 5000 })
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="sticky top-0 z-50">
        <Navbar
          cartItemsCount={cartItems.packages.length + cartItems.services.length}
          onCartClick={() => setIsCartOpen(true)}
        />
      </header>

      <main className="flex-grow">
        {/* Hero */}
        <section className="relative overflow-hidden border-b border-border">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,hsl(var(--foreground)/0.06),transparent_60%)]" />
          <div className="container mx-auto px-4 py-20 sm:py-28 md:py-32">
            <div className="mx-auto max-w-3xl text-center">
              <div className="mb-6 inline-flex items-center rounded-full border border-border px-3 py-1 text-xs font-medium text-muted-foreground">
                {t('badge')}
              </div>
              <h1 className="text-balance text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
                {t('heroTitleA')} <span className="text-muted-foreground">{t('heroTitleB')}</span>
              </h1>
              <p className="mt-6 text-pretty text-base text-muted-foreground sm:text-lg md:text-xl">
                {t('heroSubtitle')}
              </p>
              <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Button size="lg" onClick={() => scrollToSection(packagesRef)}>
                  {t('viewPackages')}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                <Button size="lg" variant="outline" onClick={() => scrollToSection(servicesRef)}>
                  {t('individualServices')}
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Packages */}
        <section id="packages" ref={packagesRef} className="border-b border-border py-20 sm:py-24">
          <div className="container mx-auto px-4">
            <div className="mx-auto mb-12 max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{t('packagesTitle')}</h2>
              <p className="mt-3 text-muted-foreground">{t('packagesSubtitle')}</p>
            </div>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              {PACKAGE_KEYS.map((pkg) => {
                const name = tPackages(`${pkg.key}.name`)
                const tagline = tPackages(`${pkg.key}.tagline`)
                const note = tPackages(`${pkg.key}.note`)
                const includes = Array.from({ length: pkg.includesCount }, (_, i) =>
                  tPackages(`${pkg.key}.includes.${i}`),
                )
                return (
                  <Card
                    key={pkg.key}
                    className={`flex flex-col ${
                      pkg.featured ? 'border-foreground shadow-lg ring-1 ring-foreground/10' : ''
                    }`}
                  >
                    <CardHeader>
                      {pkg.featured && (
                        <div className="mb-2 inline-flex w-fit items-center rounded-full bg-foreground px-2.5 py-0.5 text-xs font-medium text-background">
                          {t('popular')}
                        </div>
                      )}
                      <CardTitle className="text-2xl">{name}</CardTitle>
                      <CardDescription className="text-sm text-muted-foreground">{tagline}</CardDescription>
                      <div className="mt-4 flex items-baseline gap-2">
                        <span className="text-4xl font-bold tracking-tight">{pkg.price}</span>
                        <span className="text-sm text-muted-foreground">/ {pkg.priceUSD}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">{formatUZS(pkg.priceUZS)}</div>
                    </CardHeader>
                    <CardContent className="flex-grow">
                      <ul className="space-y-3 text-sm">
                        {includes.map((item, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <Check className="mt-0.5 h-4 w-4 shrink-0 text-foreground" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                      <p className="mt-4 text-xs text-muted-foreground">{note}</p>
                    </CardContent>
                    <CardFooter>
                      <Button
                        className="w-full"
                        variant={pkg.featured ? 'default' : 'outline'}
                        onClick={() => addToCart(name, pkg.price, pkg.priceUSD, formatUZS(pkg.priceUZS), 'package')}
                      >
                        <ShoppingCart className="mr-2 h-4 w-4" />
                        {t('addToCart')}
                      </Button>
                    </CardFooter>
                  </Card>
                )
              })}
            </div>
          </div>
        </section>

        {/* Individual services */}
        <section id="services" ref={servicesRef} className="py-20 sm:py-24">
          <div className="container mx-auto px-4">
            <div className="mx-auto mb-12 max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{t('servicesTitle')}</h2>
              <p className="mt-3 text-muted-foreground">{t('servicesSubtitle')}</p>
            </div>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {SERVICE_KEYS.map((service) => {
                const name = tServices(`${service.key}.name`)
                const description = tServices(`${service.key}.description`)
                const priceUZSFormatted = formatUZS(service.priceUZS)
                return (
                  <Card key={service.key} className="flex h-full flex-col transition-shadow hover:shadow-md">
                    <CardHeader>
                      <CardTitle className="text-lg">{name}</CardTitle>
                      <CardDescription className="text-sm">
                        <span className="font-semibold text-foreground">{service.price}</span>
                        <span className="text-muted-foreground"> · {service.priceUSD} · {priceUZSFormatted}</span>
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="flex-grow">
                      <p className="text-sm text-muted-foreground">{description}</p>
                    </CardContent>
                    <CardFooter>
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={() => addToCart(name, service.price, service.priceUSD, priceUZSFormatted, 'service')}
                      >
                        <ShoppingCart className="mr-2 h-4 w-4" />
                        {t('add')}
                      </Button>
                    </CardFooter>
                  </Card>
                )
              })}
            </div>
          </div>
        </section>
      </main>

      <Footer />

      {isCartOpen && (
        <Cart
          items={[...cartItems.packages, ...cartItems.services]}
          onRemoveItem={removeFromCart}
          onClose={() => setIsCartOpen(false)}
        />
      )}
    </div>
  )
}

export default function LandingPage() {
  const t = useTranslations('Landing')
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">{t('loading')}</div>}>
      <LandingPageContent />
    </Suspense>
  )
}
