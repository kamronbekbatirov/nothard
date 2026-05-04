'use client'

import { useState, useRef, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
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

function LandingPageContent() {
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

  const individualServices = [
    {
      name: '✈️ Встреча в аэропорту + транспорт (общественный)',
      price: '£99',
      priceUSD: '$130',
      priceUZS: '1,612,000 сум',
      description:
        'Встреча и сопровождение до места проживания в Лондоне или до вокзала. Общественный транспорт включён в стоимость. ⚠️ Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '✈️ Встреча в аэропорту + частный трансфер (такси)',
      price: '£228',
      priceUSD: '$300',
      priceUZS: '3,720,000 сум',
      description:
        'Встреча и сопровождение до места проживания в Лондоне или до вокзала. Такси бронируется и оплачивается компанией (включено в стоимость). ⚠️ Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '📱 SIM-карта',
      price: '£15',
      priceUSD: '$20',
      priceUZS: '248,000 сум',
      description:
        'Предоставление SIM-карты и помощь в активации. Тариф оплачивает клиент. ⚠️ Услуга предоставляется в Лондоне. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '🎫 Oyster-карта',
      price: '£15',
      priceUSD: '$20',
      priceUZS: '248,000 сум',
      description:
        'Покупка Oyster-карты для общественного транспорта. Карта включена, пополнения оплачивает клиент. ⚠️ Услуга предоставляется в Лондоне. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '🔍 Поиск и подбор жилья',
      price: '£38',
      priceUSD: '$50',
      priceUZS: '620,000 сум',
      description:
        '• Обзвон и подбор неограниченного количества вариантов по вашим критериям. • Итоговый список квартир предоставляется клиенту. • Каждый выезд на просмотр (viewing) оплачивается отдельно — £38 ($50). ⚠️ Просмотры организуются в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '🏨 Помощь с временным жильём',
      price: '£38',
      priceUSD: '$50',
      priceUZS: '620,000 сум',
      description: 'Подбор и бронирование отеля/хостела на первые дни. Оплата проживания за клиентом.',
    },
    {
      name: '🚚 Перевозка вещей',
      price: '£76',
      priceUSD: '$100',
      priceUZS: '1,240,000 сум',
      description:
        'Помощь в выборе и заказе перевозочной компании. Стоимость перевозки оплачивается клиентом. ⚠️ Услуга предоставляется в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '📝 Регистрация в Local GP (NHS)',
      price: '£76',
      priceUSD: '$100',
      priceUZS: '1,240,000 сум',
      description:
        'Личное сопровождение при регистрации у местного врача. ⚠️ Услуга предоставляется в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '🕐 Поддержка на первые 7 дней (9:00–17:00)',
      price: '£76',
      priceUSD: '$100',
      priceUZS: '1,240,000 сум',
      description:
        'Поддержка и консультации через Telegram и лично при необходимости. ⚠️ Услуга предоставляется в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '📊 Оценка района проживания',
      price: '£38',
      priceUSD: '$50',
      priceUZS: '620,000 сум',
      description:
        'Выезд в выбранный район, фото/видеоотчёт, обзор инфраструктуры. ⚠️ Услуга предоставляется в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '💡 Подключение коммунальных услуг',
      price: '£76',
      priceUSD: '$100',
      priceUZS: '1,240,000 сум',
      description:
        'Помощь в подключении интернета, газа и электричества. ⚠️ Услуга предоставляется в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '🏦 Помощь с открытием счёта (онлайн-банкинг)',
      price: '£38',
      priceUSD: '$50',
      priceUZS: '620,000 сум',
      description: 'Поддержка при открытии цифрового счёта с возможностью интернет-банкинга. ✅ Доступно онлайн, в любом городе.',
    },
    {
      name: '📜 Перевод и помощь с договором аренды',
      price: '£38',
      priceUSD: '$50',
      priceUZS: '620,000 сум',
      description:
        'Перевод договора аренды и сопровождение при подписании. ⚠️ Услуга предоставляется в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: '📄 Перевод документов',
      price: '£20',
      priceUSD: '$26',
      priceUZS: '322,000 сум',
      description: 'Перевод официальных документов (можно онлайн).',
    },
  ]

  const packages = [
    {
      name: 'Пакет «Встреть меня»',
      price: '£114',
      priceUSD: '$150',
      priceUZS: '1,860,000 сум',
      tagline: 'Первый шаг в Лондоне',
      includes: [
        '✈️ Встреча в аэропорту',
        '🚌 Оплата общественного транспорта и сопровождение до места проживания в Лондоне или до вокзала',
        '📱 SIM-карта (тариф оплачивает клиент при активации)',
        '🎫 Oyster-карта (карта включена, пополнение оплачивает клиент)',
      ],
      note: '⚠️ Услуга предоставляется в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: 'Пакет «Жильё»',
      price: '£342',
      priceUSD: '$450',
      priceUZS: '5,580,000 сум',
      tagline: 'Помощь с поиском дома',
      featured: true,
      includes: [
        'Всё из пакета «Встреть меня»',
        '🏠 Обзвон неограниченного количества вариантов по вашим критериям',
        '🏢 Организация просмотров до 3 квартир',
        '🏨 Помощь с временным жильём',
        '🚚 Организация перевозки вещей',
      ],
      note: '⚠️ Все услуги предоставляются в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
    {
      name: 'Премиум пакет',
      price: '£647',
      priceUSD: '$850',
      priceUZS: '10,540,000 сум',
      tagline: 'Полная релокация «под ключ»',
      includes: [
        'Всё из пакета «Жильё»',
        '📝 Регистрация в Local GP (NHS)',
        '🕐 Поддержка 7 дней (9:00–17:00)',
        '📊 Оценка района проживания',
        '💡 Подключение коммунальных услуг',
        '🏦 Открытие цифрового счёта',
        '📜 Перевод и сопровождение договора аренды',
        '🎁 Подарок от компании',
      ],
      note: '⚠️ Все офлайн-услуги предоставляются в пределах Лондона. Для других городов стоимость рассчитывается индивидуально.',
    },
  ]

  const scrollToSection = (ref: React.RefObject<HTMLDivElement>) => {
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const addToCart = (name: string, price: string, priceUSD: string, priceUZS: string, type: 'package' | 'service') => {
    if (type === 'package') {
      if (cartItems.packages.length > 0) {
        toast({
          title: 'Ошибка',
          description: 'В корзине уже есть пакет. Пожалуйста, удалите его перед добавлением нового.',
          variant: 'destructive',
          duration: 5000,
        })
        return
      }
      setCartItems((prev) => ({ ...prev, packages: [{ name, price, priceUSD, priceUZS, type }] }))
    } else {
      if (cartItems.services.some((s) => s.name === name)) {
        toast({
          title: 'Ошибка',
          description: 'Эта услуга уже добавлена в корзину.',
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
    toast({ title: 'Успешно', description: 'Элемент добавлен в корзину.', duration: 5000 })
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
    toast({ title: 'Успешно', description: 'Элемент удалён из корзины.', duration: 5000 })
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
                Релокация · Лондон · 2026
              </div>
              <h1 className="text-balance text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
                Переезд в Лондон <span className="text-muted-foreground">без лишних забот</span>
              </h1>
              <p className="mt-6 text-pretty text-base text-muted-foreground sm:text-lg md:text-xl">
                Встреча в аэропорту, поиск жилья, документы, банк, NHS — мы берём на себя всё, что обычно отнимает
                недели. Вы просто приезжаете и начинаете жить.
              </p>
              <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Button size="lg" onClick={() => scrollToSection(packagesRef)}>
                  Смотреть пакеты
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                <Button size="lg" variant="outline" onClick={() => scrollToSection(servicesRef)}>
                  Отдельные услуги
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Packages */}
        <section id="packages" ref={packagesRef} className="border-b border-border py-20 sm:py-24">
          <div className="container mx-auto px-4">
            <div className="mx-auto mb-12 max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Пакеты</h2>
              <p className="mt-3 text-muted-foreground">
                Выберите объём поддержки, который подходит вам — от встречи в аэропорту до полного сопровождения.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              {packages.map((pkg) => (
                <Card
                  key={pkg.name}
                  className={`flex flex-col ${
                    pkg.featured
                      ? 'border-foreground shadow-lg ring-1 ring-foreground/10'
                      : ''
                  }`}
                >
                  <CardHeader>
                    {pkg.featured && (
                      <div className="mb-2 inline-flex w-fit items-center rounded-full bg-foreground px-2.5 py-0.5 text-xs font-medium text-background">
                        Популярный выбор
                      </div>
                    )}
                    <CardTitle className="text-2xl">{pkg.name}</CardTitle>
                    <CardDescription className="text-sm text-muted-foreground">{pkg.tagline}</CardDescription>
                    <div className="mt-4 flex items-baseline gap-2">
                      <span className="text-4xl font-bold tracking-tight">{pkg.price}</span>
                      <span className="text-sm text-muted-foreground">/ {pkg.priceUSD}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">{pkg.priceUZS}</div>
                  </CardHeader>
                  <CardContent className="flex-grow">
                    <ul className="space-y-3 text-sm">
                      {pkg.includes.map((item, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <Check className="mt-0.5 h-4 w-4 shrink-0 text-foreground" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                    <p className="mt-4 text-xs text-muted-foreground">{pkg.note}</p>
                  </CardContent>
                  <CardFooter>
                    <Button
                      className="w-full"
                      variant={pkg.featured ? 'default' : 'outline'}
                      onClick={() => addToCart(pkg.name, pkg.price, pkg.priceUSD, pkg.priceUZS, 'package')}
                    >
                      <ShoppingCart className="mr-2 h-4 w-4" />
                      Добавить в корзину
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Individual services */}
        <section id="services" ref={servicesRef} className="py-20 sm:py-24">
          <div className="container mx-auto px-4">
            <div className="mx-auto mb-12 max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Индивидуальные услуги</h2>
              <p className="mt-3 text-muted-foreground">
                Нужна только одна или две вещи? Возьмите ровно то, что необходимо — без переплаты.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {individualServices.map((service, index) => (
                <Card key={index} className="flex h-full flex-col transition-shadow hover:shadow-md">
                  <CardHeader>
                    <CardTitle className="text-lg">{service.name}</CardTitle>
                    <CardDescription className="text-sm">
                      <span className="font-semibold text-foreground">{service.price}</span>
                      <span className="text-muted-foreground"> · {service.priceUSD} · {service.priceUZS}</span>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-grow">
                    <p className="text-sm text-muted-foreground">{service.description}</p>
                  </CardContent>
                  <CardFooter>
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() =>
                        addToCart(service.name, service.price, service.priceUSD, service.priceUZS, 'service')
                      }
                    >
                      <ShoppingCart className="mr-2 h-4 w-4" />
                      Добавить
                    </Button>
                  </CardFooter>
                </Card>
              ))}
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
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Загрузка...</div>}>
      <LandingPageContent />
    </Suspense>
  )
}
