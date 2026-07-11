// Shared, locale-independent domain data for Nothard.
// Translatable names/descriptions live in messages (keyed by these ids).

export const FX = { usd: 1.3, uzs: 16300 } // £→$ and £→сум (indicative; backend should use live rates)

export function fmtGBP(gbp: number) {
  return `£${gbp.toLocaleString('en-GB')}`
}
export function fmtUSD(gbp: number) {
  return `$${Math.round(gbp * FX.usd).toLocaleString('en-US')}`
}
export function fmtUZS(gbp: number) {
  return `${Math.round(gbp * FX.uzs).toLocaleString('ru-RU').replace(/,/g, ' ')} сум`
}

export type ServiceStage = 'arrival' | 'housing' | 'setup' | 'documents'

export type Service = {
  id: string
  price: number // GBP
  stage: ServiceStage
  online?: boolean
}

export const SERVICE_STAGES: ServiceStage[] = ['arrival', 'housing', 'setup', 'documents']

export const SERVICES: Service[] = [
  { id: 'airportTransport', price: 99, stage: 'arrival' },
  { id: 'airportTaxi', price: 228, stage: 'arrival' },
  { id: 'sim', price: 15, stage: 'arrival' },
  { id: 'oyster', price: 15, stage: 'arrival' },
  { id: 'housingSearch', price: 38, stage: 'housing' },
  { id: 'tempHousing', price: 38, stage: 'housing' },
  { id: 'moving', price: 76, stage: 'housing' },
  { id: 'nhs', price: 76, stage: 'setup' },
  { id: 'support7', price: 76, stage: 'setup' },
  { id: 'neighborhood', price: 38, stage: 'setup' },
  { id: 'utilities', price: 76, stage: 'setup' },
  { id: 'bankOnline', price: 38, stage: 'documents', online: true },
  { id: 'lease', price: 38, stage: 'documents' },
  { id: 'docTranslate', price: 20, stage: 'documents', online: true },
]

export function serviceById(id: string) {
  return SERVICES.find((s) => s.id === id)
}

// Teaser on the landing page — six highlighted services.
export const TEASER_SERVICE_IDS = [
  'airportTransport',
  'housingSearch',
  'nhs',
  'bankOnline',
  'lease',
  'sim',
]

export type Pkg = {
  id: string
  gbp: number
  usd: number
  uzs: number
  popular?: boolean
  featureCount: number
}

export const PACKAGES: Pkg[] = [
  { id: 'meet', gbp: 114, usd: 150, uzs: 1860000, featureCount: 4 },
  { id: 'housing', gbp: 342, usd: 450, uzs: 5580000, popular: true, featureCount: 5 },
  { id: 'premium', gbp: 647, usd: 850, uzs: 10540000, featureCount: 6 },
]

// London arrival airports (for the airport-pickup intake question).
// Every London airport with each of its terminals. These are proper nouns that
// appear the same on any boarding pass, so we keep one shared list (identical in
// every locale) used by both the client cabinet and the operator panel.
export const LONDON_AIRPORT_TERMINALS = [
  'Heathrow (LHR) · Terminal 2',
  'Heathrow (LHR) · Terminal 3',
  'Heathrow (LHR) · Terminal 4',
  'Heathrow (LHR) · Terminal 5',
  'Gatwick (LGW) · North Terminal',
  'Gatwick (LGW) · South Terminal',
  'Stansted (STN)',
  'Luton (LTN)',
  'London City (LCY)',
  'London Southend (SEN)',
] as const

// Common Tashkent ↔ London flights, shown as typing suggestions (free text — the
// user can enter any flight number). Uzbekistan Airways flies the direct route.
export const LONDON_FLIGHTS = [
  'HY201',
  'HY202',
  'HY211',
  'HY213',
  'HY214',
  'HY215',
  'U6 707',
  'U6 709',
  'W6 6501',
  'BA875',
  'BA876',
  'TK1979',
] as const

// Packages that include an airport pickup → ask arrival details at checkout.
export const AIRPORT_PACKAGES = new Set(['meet', 'housing', 'premium'])

// 9-step relocation path shown in the client cabinet.
export const CABINET_STEPS = [
  'airportMeet',
  'transfer',
  'tempStay',
  'housingSearch',
  'viewings',
  'lease',
  'bank',
  'nhs',
  'moveIn',
] as const

// "How it works" — 5 public steps.
export const HOW_STEPS = ['meet', 'housing', 'documents', 'bank', 'moveIn'] as const

// Sample housing listings (until agency listings are wired to the backend).
export type Property = {
  id: number
  priceGBP: number
  area: 'whitechapel' | 'stratford' | 'canadaWater' | 'woolwich'
  rooms: 0 | 1 | 2 | 3 // 0 = studio
  baths: number
  furnished: boolean
  addr: string
}

export const SAMPLE_PROPERTIES: Property[] = [
  { id: 1, priceGBP: 1450, area: 'whitechapel', rooms: 0, baths: 1, furnished: true, addr: 'Whitechapel High St, E1' },
  { id: 2, priceGBP: 1750, area: 'stratford', rooms: 1, baths: 1, furnished: true, addr: 'Great Eastern Rd, E15' },
  { id: 3, priceGBP: 1950, area: 'canadaWater', rooms: 2, baths: 1, furnished: false, addr: 'Surrey Quays Rd, SE16' },
  { id: 4, priceGBP: 1300, area: 'woolwich', rooms: 0, baths: 1, furnished: true, addr: 'Mast Quay, SE18' },
  { id: 5, priceGBP: 2200, area: 'stratford', rooms: 2, baths: 2, furnished: true, addr: 'Olympic Park Ave, E20' },
  { id: 6, priceGBP: 2650, area: 'canadaWater', rooms: 3, baths: 2, furnished: false, addr: 'Deal Porters Way, SE16' },
  { id: 7, priceGBP: 1600, area: 'whitechapel', rooms: 1, baths: 1, furnished: true, addr: 'Commercial Rd, E1' },
  { id: 8, priceGBP: 1850, area: 'woolwich', rooms: 2, baths: 1, furnished: true, addr: 'Warren Lane, SE18' },
]

// Which intake fields each item needs at checkout (only the relevant ones).
export type CheckoutFieldKey =
  | 'arrivalDate'
  | 'flight'
  | 'bank'
  | 'budget'
  | 'area'
  | 'address'
  | 'nights'

export const FIELD_TYPE: Record<CheckoutFieldKey, 'date' | 'text' | 'number' | 'bank' | 'area'> = {
  arrivalDate: 'date',
  flight: 'text',
  bank: 'bank',
  budget: 'number',
  area: 'area',
  address: 'text',
  nights: 'number',
}

export const ITEM_FIELDS: Record<string, CheckoutFieldKey[]> = {
  // packages (arrival based)
  meet: ['arrivalDate', 'flight'],
  housing: ['arrivalDate', 'flight'],
  premium: ['arrivalDate', 'flight'],
  // services
  airportTransport: ['arrivalDate', 'flight'],
  airportTaxi: ['arrivalDate', 'flight'],
  tempHousing: ['arrivalDate', 'nights'],
  housingSearch: ['budget', 'area'],
  neighborhood: ['area'],
  utilities: ['address'],
  moving: ['address', 'arrivalDate'],
  bankOnline: ['bank'],
  // sim, oyster, nhs, support7, lease, docTranslate → no extra fields
}

/** Ordered, de-duplicated union of fields needed for a set of item ids. */
export function fieldsForItems(ids: string[]): CheckoutFieldKey[] {
  const out: CheckoutFieldKey[] = []
  for (const id of ids) {
    for (const f of ITEM_FIELDS[id] || []) {
      if (!out.includes(f)) out.push(f)
    }
  }
  return out
}
