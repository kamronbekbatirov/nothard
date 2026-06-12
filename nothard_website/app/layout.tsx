import './globals.css'
import Script from 'next/script'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { NextIntlClientProvider } from 'next-intl'
import ruMessages from '../messages/ru.json'
import { Toaster } from './components/ui/toaster'
import { ThemeProvider } from './components/theme-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Nothard — Услуги по релокации в Лондон',
  description:
    'Мы предоставляем комплексные услуги по релокации, чтобы сделать ваш переезд в Лондон лёгким и беззаботным.',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [{ url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' }],
  },
  manifest: '/site.webmanifest',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body className={inter.className}>
        <NextIntlClientProvider locale="ru" messages={ruMessages}>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            {children}
            <Toaster />
          </ThemeProvider>
        </NextIntlClientProvider>
        <Script src="https://stats.kama.uz/script.js" data-website-id="91960825-e17c-4235-b874-3cf3f6a23315" data-domains="nothard.uz" strategy="afterInteractive" />
      </body>
    </html>
  )
}
