import { Onest } from 'next/font/google'

// Onest — a modern geometric sans with full Latin + Cyrillic coverage, used for
// both display (heavier weights) and body text. One cohesive family.
export const onest = Onest({
  subsets: ['latin', 'latin-ext', 'cyrillic'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-onest',
  display: 'swap',
})
