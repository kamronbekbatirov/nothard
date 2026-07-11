import createMiddleware from 'next-intl/middleware'
import { routing } from './i18n/routing'

export default createMiddleware(routing)

export const config = {
  // Localize everything except API, Next internals and static files.
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)'],
}
