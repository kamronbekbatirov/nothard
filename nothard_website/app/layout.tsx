import './globals.css'
import Script from 'next/script'
import type { Metadata, Viewport } from 'next'
import { cookies } from 'next/headers'
import { NextIntlClientProvider, hasLocale } from 'next-intl'
import { routing } from '@/i18n/routing'
import { onest } from './fonts'
import { ToastProvider } from './components/toast'
import { ThemeProviders } from './components/theme'

export const metadata: Metadata = {
  metadataBase: new URL('https://nothard.uz'),
  title: {
    default: 'Nothard — переезд в Лондон без лишних забот',
    template: '%s · Nothard',
  },
  description:
    'Сервис релокации в Лондон «под ключ»: встреча в аэропорту, поиск жилья, документы, банк, NHS. Приезжайте — остальное на нас.',
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon.ico' },
    ],
    apple: [{ url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' }],
  },
  manifest: '/site.webmanifest',
}

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#e9e5dd' },
    { media: '(prefers-color-scheme: dark)', color: '#181613' },
  ],
  width: 'device-width',
  initialScale: 1,
  // Stop the browser/Telegram WebView from auto-zooming when a text field is
  // focused (the field would otherwise "jump" larger on phones).
  maximumScale: 1,
  userScalable: false,
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Non-localized routes (panels) render in the language chosen via cookie.
  const store = await cookies()
  const cookieLocale = store.get('NEXT_LOCALE')?.value
  const locale = hasLocale(routing.locales, cookieLocale)
    ? cookieLocale
    : routing.defaultLocale
  const messages = (await import(`../messages/${locale}.json`)).default

  // No React-controlled className on <html>: next-themes toggles the `.dark`
  // class there, and a controlled className would strip it. The font variable
  // lives on <body> instead.
  return (
    <html lang={locale} suppressHydrationWarning>
      <body className={`${onest.variable} bg-paper font-sans text-ink antialiased`}>
        {/* Telegram Mini App bridge — no-op outside Telegram */}
        <Script src="https://telegram.org/js/telegram-web-app.js?62" strategy="beforeInteractive" />
        <ThemeProviders>
          <NextIntlClientProvider locale={locale} messages={messages}>
            <ToastProvider>{children}</ToastProvider>
          </NextIntlClientProvider>
        </ThemeProviders>
        <Script
          src="https://stats.kama.uz/script.js"
          data-website-id="91960825-e17c-4235-b874-3cf3f6a23315"
          data-domains="nothard.uz"
          strategy="afterInteractive"
        />
      </body>
    </html>
  )
}
