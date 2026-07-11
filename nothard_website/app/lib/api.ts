// Lightweight API client for the Nothard backend (JWT bearer auth).

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || '/api'

const ACCESS_KEY = 'nh_access'
const REFRESH_KEY = 'nh_refresh'
const DEVICE_KEY = 'nh_device'

/** A stable per-browser id used to dedup sessions. Persists across logout (we
 * only clear tokens on logout), so logout→login on the same device maps back to
 * one session instead of creating a new one each time. */
export function getDeviceId(): string {
  if (typeof window === 'undefined') return ''
  const existing = localStorage.getItem(DEVICE_KEY)
  if (existing) return existing
  const id: string =
    (crypto as any)?.randomUUID?.() ??
    `d-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
  localStorage.setItem(DEVICE_KEY, id)
  return id
}

export type Role = 'client' | 'operator' | 'agency' | 'runner' | 'admin'

export type User = {
  id: number
  email: string | null
  name: string
  phone?: string | null
  role: Role
  telegram_id?: string | null
  telegram_username?: string | null
  photo_url?: string | null
  termsAccepted?: boolean
  locale?: string
}

export type ChatMessage = {
  id: number
  sender: 'client' | 'manager' | 'runner'
  channel?: 'manager' | 'runner'
  author: string
  body: string
  createdAt: string
}

export type OrderHistoryItem = {
  type: 'package' | 'service' | 'viewing'
  id: string
  amountGBP: number
  paid: boolean
  createdAt: string | null
  status: 'done' | 'active'
  completedAt: string | null
  steps?: { key: string; status: string; completedAt: string | null }[]
}

export type DeviceSession = {
  id: number
  browser: string
  os: string
  device: string
  ip: string
  current: boolean
  createdAt: string | null
  lastSeenAt: string | null
}

export function getAccess(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(ACCESS_KEY)
}

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  window.dispatchEvent(new Event('nh-auth'))
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  window.dispatchEvent(new Event('nh-auth'))
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = getAccess()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (typeof window !== 'undefined') headers.set('X-Device-Id', getDeviceId())
  // Never set JSON content-type for FormData — the browser must add the multipart boundary.
  const isForm = typeof FormData !== 'undefined' && init.body instanceof FormData
  if (init.body && !isForm && !headers.has('Content-Type'))
    headers.set('Content-Type', 'application/json')
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })
  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) {
    // Our session/token is no longer valid (account deleted, session revoked,
    // deactivated). Drop the stale token so the page guards bounce to /login —
    // this is what kicks connected users out without a manual reload.
    if (res.status === 401 && token) clearTokens()
    const err = new Error(data?.error || data?.detail || res.statusText) as Error & {
      status?: number
      code?: string
    }
    err.status = res.status
    err.code = data?.code
    throw err
  }
  return data as T
}

export const api = {
  register: (body: {
    email: string
    password: string
    name: string
    phone?: string
    locale?: string
  }) =>
    req<{ access_token: string; refresh_token?: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  login: (body: { email: string; password: string }) =>
    req<{ access_token: string; refresh_token?: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  whoami: () => req<User>('/auth/me'),
  // Best-effort: revoke the current session server-side on logout.
  logout: () => req<{ ok: boolean }>('/auth/logout', { method: 'POST' }).catch(() => null),
  listings: () => req<{ listings: CatalogListing[] }>('/listings'),
  listingDetail: (id: number) => req<ListingDetail>(`/listings/${id}`),
  // Public read-only relocation snapshot (shared with family). No auth.
  sharedRelocation: (token: string) => req<SharedRelocation>(`/share/${token}`),
  // Public OpenGraph preview for a pasted listing URL (photo/title/price).
  ogPreview: (url: string) =>
    req<{ photo?: string; title?: string; description?: string; price?: number }>(
      `/og?url=${encodeURIComponent(url)}`
    ),
  emailRequest: (email: string) =>
    req<{ ok: boolean }>('/auth/email/request', { method: 'POST', body: JSON.stringify({ email }) }),
  emailLogin: (email: string, code: string) =>
    req<{ access_token: string; refresh_token?: string; user: User }>('/auth/email/verify', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    }),
  telegram: {
    startUrl: () => `${API_BASE}/auth/telegram/start`,
    exchange: (ticket: string) =>
      req<{ access_token: string; refresh_token?: string; user: User }>(
        '/auth/telegram/exchange',
        { method: 'POST', body: JSON.stringify({ ticket }) }
      ),
    linkStart: () => req<{ url: string }>('/auth/telegram/link-start'),
    unlink: () => req<{ ok: boolean }>('/auth/telegram/unlink', { method: 'POST' }),
    // existing_only=true → resume a returning user without creating an account
    // (response is { exists: false } when there is no account yet).
    miniapp: (body: { init_data: string; existing_only?: boolean }) =>
      req<
        | { access_token: string; refresh_token?: string; user: User }
        | { exists: false }
      >('/auth/telegram/miniapp', { method: 'POST', body: JSON.stringify(body) }),
  },
  me: {
    dashboard: () => req<DashboardData>('/me/dashboard'),
    checkout: (
      items: { type: 'package' | 'service'; id: string }[],
      details?: Record<string, string>
    ) =>
      req<DashboardData>('/me/checkout', {
        method: 'POST',
        body: JSON.stringify({ items, details: details ?? {} }),
      }),
    changePassword: (old: string, next: string) =>
      req<{ ok: boolean }>('/me/password', { method: 'POST', body: JSON.stringify({ old, new: next }) }),
    updateName: (name: string) =>
      req<User>('/me/update', { method: 'POST', body: JSON.stringify({ name }) }),
    deleteAccount: () => req<{ ok: boolean }>('/me', { method: 'DELETE' }),
    acceptTerms: () => req<User>('/me/accept-terms', { method: 'POST' }),
    setLocale: (locale: string) =>
      req<User>('/me/locale', { method: 'POST', body: JSON.stringify({ locale }) }),
    emailStart: (email: string) =>
      req<{ ok: boolean; delivered: boolean }>('/me/email/start', {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),
    emailVerify: (code: string) =>
      req<User>('/me/email/verify', { method: 'POST', body: JSON.stringify({ code }) }),
    emailVerifyWithPassword: (code: string, password: string) =>
      req<User>('/me/email/verify', {
        method: 'POST',
        body: JSON.stringify({ code, password }),
      }),
    updateArrival: (fields: Record<string, string>) =>
      req<DashboardData>('/me/arrival', { method: 'POST', body: JSON.stringify(fields) }),
    review: (orderId: number, stars: number, text: string) =>
      req<DashboardData>('/me/review', {
        method: 'POST',
        body: JSON.stringify({ orderId, stars, text }),
      }),
    skipReview: (orderId: number) =>
      req<DashboardData>('/me/review/skip', {
        method: 'POST',
        body: JSON.stringify({ orderId }),
      }),
    messages: (channel: 'manager' | 'runner' = 'manager') =>
      req<{ messages: ChatMessage[] }>(`/me/messages?channel=${channel}`),
    sendMessage: (body: string, channel: 'manager' | 'runner' = 'manager') =>
      req<ChatMessage>('/me/messages', { method: 'POST', body: JSON.stringify({ body, channel }) }),
    addHousing: (body: {
      source: 'catalog' | 'link'
      ref: string
      title?: string
      priceGBP?: number
      addr?: string
    }) => req<HousingItem>('/me/housing', { method: 'POST', body: JSON.stringify(body) }),
    deleteHousing: (id: number) =>
      req<{ ok: boolean }>(`/me/housing/${id}`, { method: 'DELETE' }),
    // Request (and pay £30 for) an accompanied viewing of a shortlisted property.
    requestViewing: (id: number) =>
      req<HousingItem>(`/me/housing/${id}/viewing`, { method: 'POST' }),
    // Create/return the stable public share token for the family view.
    shareLink: () => req<{ token: string }>('/me/share', { method: 'POST' }),
    sessions: () =>
      req<{ sessions: DeviceSession[]; currentId: number | null }>('/me/sessions'),
    revokeSession: (id: number) =>
      req<{ ok: boolean }>(`/me/sessions/${id}`, { method: 'DELETE' }),
    revokeOtherSessions: () =>
      req<{ ok: boolean; revoked: number }>('/me/sessions/revoke-others', { method: 'POST' }),
  },

  admin: {
    overview: () => req<AdminOverview>('/admin/overview'),
    // undefined → key omitted (backend auto-assigns); null → explicit clear; number → set
    assignRunner: (clientId: number, runnerId?: number | null) =>
      req<AdminClient>(`/admin/clients/${clientId}/assign-runner`, {
        method: 'POST',
        body: JSON.stringify({ runner_id: runnerId }),
      }),
    assignManager: (clientId: number, managerId?: number | null) =>
      req<AdminClient>(`/admin/clients/${clientId}/assign-manager`, {
        method: 'POST',
        body: JSON.stringify({ manager_id: managerId }),
      }),
    setTaskStatus: (taskId: number, status: string) =>
      req<AdminClient>(`/admin/tasks/${taskId}/status`, {
        method: 'POST',
        body: JSON.stringify({ status }),
      }),
    messages: (clientId: number) =>
      req<{ messages: ChatMessage[] }>(`/admin/clients/${clientId}/messages`),
    sendMessage: (clientId: number, body: string) =>
      req<ChatMessage>(`/admin/clients/${clientId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ body }),
      }),
    updateClient: (clientId: number, name: string) =>
      req<AdminClient>(`/admin/clients/${clientId}/update`, {
        method: 'POST',
        body: JSON.stringify({ name }),
      }),
    deleteClient: (clientId: number) =>
      req<{ ok: boolean }>(`/admin/clients/${clientId}`, { method: 'DELETE' }),
    accounts: () => req<{ accounts: AdminAccount[] }>('/admin/accounts'),
    runnerDetail: (id: number) => req<RunnerDetail>(`/admin/runners/${id}`),
    getRunnerFee: () => req<{ fee: number }>('/admin/settings/runner-fee'),
    setRunnerFee: (fee: number) =>
      req<{ fee: number }>('/admin/settings/runner-fee', { method: 'POST', body: JSON.stringify({ fee }) }),
    setRunnerPaid: (taskId: number, paid: boolean) =>
      req<{ ok: boolean; id: number; runnerPaid: boolean }>(`/admin/tasks/${taskId}/runner-paid`, {
        method: 'POST',
        body: JSON.stringify({ paid }),
      }),
    payRunnerAll: (id: number) =>
      req<{ ok: boolean; paid: number }>(`/admin/runners/${id}/pay-all`, { method: 'POST' }),
    createAccount: (body: {
      name: string
      role: Role
      email?: string
      password?: string
      phone?: string
      telegram?: string
    }) => req<AdminAccount>('/admin/accounts', { method: 'POST', body: JSON.stringify(body) }),
    updateAccount: (
      id: number,
      body: {
        name?: string
        role?: Role
        email?: string
        active?: boolean
        password?: string
        phone?: string
        telegram?: string
      }
    ) => req<AdminAccount>(`/admin/accounts/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    deleteAccount: (id: number) =>
      req<{ ok: boolean }>(`/admin/accounts/${id}`, { method: 'DELETE' }),
    uploadPhoto: (id: number, file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return req<AdminAccount>(`/admin/accounts/${id}/photo`, { method: 'POST', body: fd })
    },
    reviews: () => req<AdminReviews>('/admin/reviews'),
    setHousingStatus: (
      id: number,
      status: HousingStatus,
      opts?: { note?: string; viewingAt?: string }
    ) =>
      req<AdminClient>(`/admin/housing/${id}/status`, {
        method: 'POST',
        body: JSON.stringify({ status, ...opts }),
      }),
    uploadHousingMedia: (id: number, file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return req<AdminClient>(`/admin/housing/${id}/media`, { method: 'POST', body: fd })
    },
    deleteHousingMedia: (mediaId: number) =>
      req<AdminClient>(`/admin/housing/media/${mediaId}`, { method: 'DELETE' }),
    uploadAttachment: (orderId: number, file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return req<AdminClient>(`/admin/orders/${orderId}/attachment`, { method: 'POST', body: fd })
    },
    uploadTaskAttachment: (taskId: number, file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return req<AdminClient>(`/admin/tasks/${taskId}/attachment`, { method: 'POST', body: fd })
    },
    deleteAttachment: (id: number) =>
      req<AdminClient>(`/admin/attachments/${id}`, { method: 'DELETE' }),
    payments: () => req<AdminPayments>('/admin/payments'),
    setOrderPaid: (orderId: number, paid: boolean) =>
      req<AdminPayment>(`/admin/orders/${orderId}/paid`, {
        method: 'POST',
        body: JSON.stringify({ paid }),
      }),
    refundOrder: (orderId: number) =>
      req<AdminPayment>(`/admin/orders/${orderId}/refund`, { method: 'POST' }),
    setPackage: (clientId: number, packageId: string) =>
      req<AdminClient>(`/admin/clients/${clientId}/package`, {
        method: 'POST',
        body: JSON.stringify({ packageId }),
      }),
    addService: (clientId: number, serviceId: string) =>
      req<AdminClient>(`/admin/clients/${clientId}/service`, {
        method: 'POST',
        body: JSON.stringify({ serviceId }),
      }),
    deleteOrder: (orderId: number) =>
      req<AdminClient>(`/admin/orders/${orderId}`, { method: 'DELETE' }),
    setArrival: (clientId: number, fields: Record<string, string>) =>
      req<AdminClient>(`/admin/clients/${clientId}/arrival`, {
        method: 'POST',
        body: JSON.stringify(fields),
      }),
    listings: () => req<AdminListings>('/admin/listings'),
    setListingStatus: (id: number, status: ListingStatus) =>
      req<AdminListing>(`/admin/listings/${id}/status`, {
        method: 'POST',
        body: JSON.stringify({ status }),
      }),
    updateListing: (
      id: number,
      body: Partial<ListingInput> & { photos?: string[] }
    ) => req<AdminListing>(`/admin/listings/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    uploadListingPhoto: (id: number, file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return req<AdminListing>(`/admin/listings/${id}/photo`, { method: 'POST', body: fd })
    },
    deleteListing: (id: number) =>
      req<{ ok: boolean }>(`/admin/listings/${id}`, { method: 'DELETE' }),
  },
  agency: {
    listings: () => req<AgencyData>('/agency/listings'),
    add: (body: ListingInput) =>
      req<Listing>('/agency/listings', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: number, body: Partial<ListingInput>) =>
      req<Listing>(`/agency/listings/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    remove: (id: number) =>
      req<{ ok: boolean }>(`/agency/listings/${id}`, { method: 'DELETE' }),
    uploadPhoto: (id: number, file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return req<Listing>(`/agency/listings/${id}/photo`, { method: 'POST', body: fd })
    },
  },
  runner: {
    tasks: () => req<RunnerData>('/runner/tasks'),
    dashboard: () => req<RunnerDashboard>('/runner/dashboard'),
    advance: (taskId: number) =>
      req<RunnerTask>(`/runner/tasks/${taskId}/advance`, { method: 'POST' }),
    clients: () => req<{ clients: RunnerClient[] }>('/runner/clients'),
    messages: (clientId: number) =>
      req<{ messages: ChatMessage[] }>(`/runner/clients/${clientId}/messages`),
    sendMessage: (clientId: number, body: string) =>
      req<ChatMessage>(`/runner/clients/${clientId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ body }),
      }),
  },
}

// ---- panel/cabinet response types -----------------------------------------
export type PathTask = {
  kind: 'step' | 'service'
  key: string
  status: string // todo | onWay | arrived | done
  time: string
  addr: string
}
export type CatalogListing = {
  id: number
  priceGBP: number
  addr: string
  area: string
  rooms: number
  baths: number
  furnished: boolean
  photoUrl?: string | null
  propertyType?: string
}

export type ListingDetail = CatalogListing & {
  photos: string[]
  description: string
  amenities: string[]
  availableFrom: string
  depositGBP: number
}
export type Attachment = { id: number; filename: string; url: string }
export type HousingMedia = { id: number; url: string; filename: string; kind: 'image' | 'video' }
export type HousingStatus =
  | 'new'
  | 'viewing'
  | 'viewed'
  | 'reached'
  | 'busy'
  | 'secured'
  | 'completed'
  | 'declined'
export type HousingItem = {
  id: number
  source: 'catalog' | 'link'
  ref: string
  title: string
  description: string
  priceGBP: number
  addr: string
  photoUrl: string | null
  status: HousingStatus
  viewingAt: string
  note: string
  media: HousingMedia[]
  viewingRequested?: boolean
}
export type ServiceItem = {
  id: string
  amountGBP: number
  paid: boolean
  taskStatus: string
  done: boolean
  attachments: Attachment[]
}
export type PendingReview = {
  orderId: number
  itemType: 'package' | 'service'
  itemId: string
  amountGBP: number
}
export type SharedRelocation = {
  clientName: string
  package: { id: string } | null
  packageComplete: boolean
  progress: { done: number; total: number }
  path: { key: string; status: string }[]
  services: { id: string; done: boolean }[]
  manager: { name: string; photoUrl: string | null } | null
  runner: { name: string; photoUrl: string | null } | null
}

export type DashboardData = {
  user: User
  telegram: { linked: boolean; username: string | null }
  hasPassword: boolean
  hasOrders: boolean
  state: 'empty' | 'active' | 'completed'
  manager: {
    assigned: boolean
    name: string | null
    hours: string
    photoUrl: string | null
    telegram: string | null
    phone: string | null
  }
  documents: Record<string, boolean>
  runner: {
    assigned: boolean
    name: string | null
    photoUrl: string | null
    telegram: string | null
    phone: string | null
  }
  // True only when the active work actually needs a field companion (airport
  // meet / transport / moving). Plain services (Oyster, etc.) don't.
  needsRunner: boolean
  package: {
    id: string
    amountGBP: number
    paid: boolean
    status: string
    complete: boolean
    orderId: number
    details: Record<string, string>
    hasAirportMeet: boolean
  } | null
  packageComplete: boolean
  pendingReview: PendingReview | null
  services: ServiceItem[]
  completedServices: ServiceItem[]
  path: PathTask[]
  documentFiles: Record<string, Attachment[]>
  housingSearch: boolean
  housing: HousingItem[]
  history: OrderHistoryItem[]
  runnerChatAvailable: boolean
}

export type AdminTaskRef = {
  taskId: number | null
  key: string
  status: string
  canUpload: boolean
  attachments: Attachment[]
}
export type AdminServiceRef = {
  id: string
  orderId: number
  paid: boolean
  taskId: number | null
  status: string
  done: boolean
  attachments: Attachment[]
}
export type AdminClient = {
  id: number
  name: string
  package: string | null
  amount: number
  stepIndex: number
  stepTotal: number
  hasPackage: boolean
  packageOrderId: number | null
  packageComplete: boolean
  packageDetails: Record<string, string>
  hasServices: boolean
  active: boolean
  completed: boolean
  activeService: string | null
  steps: AdminTaskRef[]
  services: AdminServiceRef[]
  housing: HousingItem[]
  history: AdminHistoryOrder[]
  runner: string | null
  runnerId: number | null
  manager: string | null
  managerId: number | null
  paid: boolean
  photoUrl: string | null
  email: string | null
  telegram: string | null
  phone: string | null
}
export type AdminHistoryStep = {
  key: string
  status: string
  completedAt: string | null
}
export type AdminHistoryOrder = {
  type: 'package' | 'service'
  id: string
  amountGBP: number
  paid: boolean
  createdAt: string | null
  completedAt: string | null
  status: 'done' | 'active'
  steps?: AdminHistoryStep[]
}
export type AttentionItem = {
  id: string
  type: 'noRunner' | 'awaitingPayment' | 'noManager'
  who: string
  clientId: number
}
export type AdminOverview = {
  kpis: { activeClients: number; tasksToday: number; awaitingPayment: number; newWeek: number }
  clients: AdminClient[]
  attention: AttentionItem[]
  runners: { id: number; name: string }[]
  managers: { id: number; name: string }[]
}

export type AdminAccount = {
  id: number
  name: string
  email: string | null
  role: Role
  active: boolean
  telegram: string | null
  phone: string | null
  photoUrl: string | null
  createdAt: string | null
  taskTotal?: number
  taskDone?: number
  clientId?: number
  package?: string | null
  paid?: boolean
  // Runner payout summary (present for role === 'runner')
  visitFee?: number
  visitsDone?: number
  visitsUnpaid?: number
  owedGBP?: number
  clientCount?: number
}

export type RunnerVisit = {
  id: number
  kind: 'step' | 'service'
  key: string
  status: string
  time: string
  addr: string
  completedAt: string | null
  runnerPaid: boolean
}

export type RunnerDetail = {
  runner: AdminAccount
  clients: { id: number; name: string; tasks: RunnerVisit[] }[]
  payout: { visitFee: number; visitsDone: number; visitsUnpaid: number; owedGBP: number; paidGBP: number }
}
export type AdminPayment = {
  id: number
  clientId: number
  clientName: string
  itemType: 'package' | 'service'
  itemId: string
  amountGBP: number
  paid: boolean
  status: string
  createdAt: string | null
}
export type AdminPayments = {
  orders: AdminPayment[]
  totals: { paid: number; unpaid: number; refunded: number; count: number }
}
export type AdminReview = {
  id: number
  clientId: number
  clientName: string
  itemType: 'package' | 'service'
  itemId: string
  stars: number
  body: string
  createdAt: string | null
}
export type AdminReviews = { reviews: AdminReview[]; count: number; avg: number }
export type ListingStatus = 'published' | 'moderation' | 'rejected'
export type AdminListing = {
  id: number
  priceGBP: number
  addr: string
  area: string
  rooms: number
  baths: number
  furnished: boolean
  status: ListingStatus
  photoUrl: string | null
  photos?: string[]
  propertyType?: string
  description?: string
  amenities?: string[]
  availableFrom?: string
  depositGBP?: number
  agency: string
  createdAt: string | null
}
export type AdminListings = { listings: AdminListing[] }

export type Listing = {
  id: number
  priceGBP: number
  addr: string
  area: string
  rooms: number
  baths: number
  furnished: boolean
  status: 'published' | 'moderation' | 'rejected'
  matches: number
  photoUrl?: string | null
  photos?: string[]
  propertyType?: string
  description?: string
  amenities?: string[]
  availableFrom?: string
  depositGBP?: number
}

export type ListingInput = {
  priceGBP: number
  addr: string
  area: string
  rooms: number
  baths: number
  furnished: boolean
  propertyType?: string
  description?: string
  amenities?: string[]
  availableFrom?: string
  depositGBP?: number
}
export type AgencyData = {
  kpis: { published: number; moderation: number; matches: number; views: number }
  listings: Listing[]
}

export type RunnerTask = {
  id: number
  time: string
  kind: 'step' | 'service'
  key: string
  clientId: number
  client: string
  addr: string
  stage: string
}

export type RunnerClient = { id: number; name: string; photoUrl: string | null }
export type RunnerData = { name: string; total: number; done: number; tasks: RunnerTask[] }

export type RunnerVisitRow = {
  id: number
  kind: 'step' | 'service'
  key: string
  stage: string
  time: string
  addr: string
  completedAt: string | null
}
export type RunnerClientRow = {
  id: number
  name: string
  photoUrl: string | null
  phone: string | null
  telegram: string | null
  package: string | null
  tasks: RunnerVisitRow[]
}
export type RunnerDashboard = {
  name: string
  photoUrl: string | null
  stats: { clients: number; visitsTotal: number; visitsDone: number; visitsActive: number }
  payout: { visitFee: number; visitsDone: number; owedGBP: number; paidGBP: number }
  clients: RunnerClientRow[]
}

export { req as apiRequest }
