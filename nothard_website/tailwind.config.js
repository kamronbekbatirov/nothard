/** @type {import('tailwindcss').Config} */

// Colors are driven by CSS variables (RGB triplets, e.g. --paper: 233 229 221)
// defined in app/globals.css for light and [data-theme="dark"]. Using the
// `rgb(var(--x) / <alpha-value>)` form keeps Tailwind opacity modifiers working
// (e.g. bg-accent/15) while letting the whole palette flip for dark mode.
const c = (v) => `rgb(var(${v}) / <alpha-value>)`

module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '1.25rem',
      screens: { '2xl': '1200px' },
    },
    extend: {
      colors: {
        // Surfaces — warm paper
        paper: c('--paper'),
        surface: c('--surface'),
        card: c('--card'),
        sub: c('--sub'),
        // Ink / text
        ink: c('--ink'),
        'ink-2': c('--ink-2'),
        'ink-hero': c('--ink-hero'),
        muted: c('--muted'),
        gray: c('--gray'),
        'gray-lt': c('--gray-lt'),
        'gray-lt2': c('--gray-lt2'),
        // Lines / tracks
        line: c('--line'),
        track: c('--track'),
        capsule: c('--capsule'),
        // Accent — calm green
        accent: c('--accent'),
        'accent-bg': c('--accent-bg'),
        'accent-dark': c('--accent-dark'),
        // Status — terracotta
        terracotta: c('--terracotta'),
        'terracotta-bg': c('--terracotta-bg'),
        success: c('--success'),
        // Emphasis surfaces that INVERT (dark button on light theme → light on dark)
        inverse: c('--inverse'),
        'inverse-fg': c('--inverse-fg'),
        // A panel that stays dark in both themes (decorative dark CTA blocks)
        'panel-dark': c('--panel-dark'),
      },
      fontFamily: {
        serif: ['var(--font-onest)', 'system-ui', 'sans-serif'],
        sans: ['var(--font-onest)', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm: '6px',
        md: '9px',
        lg: '13px',
        xl: '16px',
        '2xl': '20px',
      },
      boxShadow: {
        card: '0 20px 50px -30px rgba(0,0,0,.35)',
        lift: '0 16px 34px -20px rgba(0,0,0,.45)',
        svc: '0 14px 30px -20px rgba(0,0,0,.45)',
        drawer: '-24px 0 60px -30px rgba(0,0,0,.55)',
        toast: '0 18px 44px -16px rgba(0,0,0,.6)',
      },
      keyframes: {
        ndPulse: {
          '0%': { boxShadow: '0 0 0 0 rgb(var(--accent) / .35)' },
          '70%': { boxShadow: '0 0 0 9px rgb(var(--accent) / 0)' },
          '100%': { boxShadow: '0 0 0 0 rgb(var(--accent) / 0)' },
        },
      },
      animation: {
        pulse: 'ndPulse 2s infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
