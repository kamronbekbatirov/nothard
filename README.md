# Nothard

> **A concierge platform for relocating to London** — airport pickup, housing search, tenancy, bank account and NHS, all coordinated in one place and tracked live.

[nothard.uz](https://nothard.uz) helps people (often students from Uzbekistan and the wider CIS) move to London without the usual chaos. A client buys a **package** or individual **services**; the airport meet, finding a flat, the tenancy, opening a bank account and registering with the NHS are then coordinated by an **operator**, carried out on the ground by a **runner** (field companion), and tracked step‑by‑step in the client's **cabinet**. Sign‑in and push notifications run through a **Telegram Mini App**.

[![Live](https://img.shields.io/badge/live-nothard.uz-000?style=flat-square)](https://nothard.uz)
[![Next.js](https://img.shields.io/badge/Next.js-16-000?style=flat-square&logo=next.js)](https://nextjs.org)
[![Flask](https://img.shields.io/badge/Flask-3-000?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Telegram](https://img.shields.io/badge/Telegram-Mini%20App-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://core.telegram.org/bots/webapps)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

> ### ⚠️ Project status — the honest version
> This is an **actively‑developed, pre‑launch** build. The web app and all four panels are real and working. **Payments are currently simulated** — checkout marks an order paid without charging a card — and a few integrations are stubbed or gated behind config. The **[“What's real vs. what's pending”](#whats-real-vs-whats-pending)** section spells this out; that transparency is the point of this README.

---

## The four sides

Nothard is a set of role‑based panels over one backend. Everyone signs in at `/login`.

| Role | Where | What they do |
| --- | --- | --- |
| 🧳 **Client** | `/profile` cabinet (+ Telegram Mini App) | Buy a package or à‑la‑carte services, enter arrival details, watch the relocation path update live, chat with their manager & companion, shortlist flats, request accompanied viewings, leave a review, and share progress with family via a read‑only link |
| 🛠️ **Operator / admin** | `/admin` | Manage clients, assign managers & runners, set task statuses, moderate agency listings, track payments & refunds, read reviews, manage the team, and handle **runner payouts** |
| 🚶 **Runner** (field companion) | `/runner` | See assigned clients and every field visit, advance a visit's stage (*on my way → arrived → done*), open a route in Maps, chat with the client, and track their own earnings history |
| 🏠 **Agency** | `/agency` | Post & manage property listings, see moderation status, and view **real** analytics — page views and which clients showed interest (matches) |

---

## Tech stack

A small monorepo of independently‑deployed services behind a Caddy edge.

| Service | Stack | Port | systemd unit |
| --- | --- | --- | --- |
| 🌐 [`nothard_website/`](nothard_website/) | Next.js 16 · React 19 · next‑intl · next‑themes · Tailwind · Radix UI | 3005 | `nothard.service` |
| ⚙️ [`api/`](api/) | Flask 3 · SQLAlchemy 2 · **PostgreSQL** · PyJWT · bcrypt · python‑jose | 5010 | `nothard-api2.service` |
| 🤖 `api/bot.py` | Telegram Bot API (long polling) | — | `nothard-bot.service` |
| 💳 [`payme/`](payme/) | Flask — Payme JSON‑RPC merchant webhook | 5001 | `nothard-payme.service` |
| 🧭 Caddy | TLS + routing (`/api/*` → API, `/payme/*` → webhook, rest → frontend) | 80/443 | `caddy.service` |

- Data lives in **PostgreSQL** (no SQLite, no Redis).
- The frontend is fully **multilingual** — Russian, English, Uzbek (Latin) and Uzbek (Cyrillic) — with **light + dark** themes and Telegram‑webview theming.
- Auth is **session‑backed JWTs**: email + password, passwordless email codes, and Telegram Mini App sign‑in. Sessions are per‑device and revocable.
- No Alembic — the schema is created with SQLAlchemy `create_all`; new columns are added with manual `ALTER TABLE … ADD COLUMN IF NOT EXISTS`.

---

## What's real vs. what's pending

### ✅ Working today
- The full web app and all four panels (client, admin, runner, agency).
- **Client cabinet**: intent‑based packages (*Meet me* / *Housing* / *Premium*), à‑la‑carte services, a **parallel relocation path** where steps carry independent statuses, a documents checklist, manager & companion cards with in‑app chat, order history, and a **“share with family”** public read‑only page.
- **Housing**: agency‑submitted listings, a public Rightmove‑style catalog with detail pages, favourites, a shortlist, and **£30 accompanied viewings** requested from the cabinet.
- **Telegram Mini App** sign‑in and best‑effort push notifications (a step done, a new chat message, “all done — leave a review”, housing updates, …).
- **Runner** field‑visit tracking with **operator‑set per‑visit payouts**; **agency** real page‑views and client‑interest matches.
- Reviews, four languages, dark mode, and device/session management.

### ⚠️ Simulated or config‑gated — please read
- **Payments are simulated.** Checkout marks orders `paid` immediately — **no card is charged**. A Payme JSON‑RPC merchant webhook lives in [`payme/`](payme/) (and is routed at `/payme/*`), but it is **not yet wired into the client checkout**. Treat every money flow in the app as demo.
- **Email delivery is off by default.** Passwordless / email‑link codes are logged to the server journal unless `RESEND_API_KEY` (Resend) or SMTP is configured — a one‑line env change, no code change.
- **No live flight lookup.** The arrival form offers a typeahead of common Tashkent↔London flights; you can also type any flight number.
- **Link previews are best‑effort.** Rightmove OpenGraph is parsed for pasted links; Zoopla blocks bots and falls back to a plain card.
- **Demo accounts** exist with a shared password for testing, and the footer address/phone are placeholders. This is **not production‑hardened**.

---

## Architecture

```
                        ┌──────────────────────────────┐
        Browser ──────▶ │   Caddy   (TLS + routing)    │
        Telegram        └───────────────┬──────────────┘
                                        │
             /api/* ┌──────────────┬────┴────┬──────────────┐ /payme/*
                    │              │  (rest)  │              │
                    ▼              ▼          ▼              ▼
          ┌───────────────┐ ┌──────────────┐        ┌───────────────┐
          │  Flask API    │ │  Next.js app │        │ Payme webhook │
          │  :5010        │ │  :3005       │        │  :5001        │
          │  auth,cabinet,│ │  cabinet UI, │        │  JSON‑RPC     │
          │  packages,    │ │  /admin,     │        │  (not yet     │
          │  housing,     │ │  /runner,    │        │  wired to     │
          │  runners,     │ │  /agency     │        │  checkout)    │
          │  agency, chat │ └──────────────┘        └───────────────┘
          └──────┬────────┘
                 │  shares the same DB
          ┌──────┴───────┐        ┌───────────────────────┐
          │ PostgreSQL   │        │  Telegram bot          │
          │ (all data)   │◀───────│  api/bot.py (polling)  │
          └──────────────┘        └───────────────────────┘
```

---

## Repository layout

```
nothard/
├── nothard_website/   Next.js frontend — every page under app/[locale]/…
│                      (client cabinet, /admin, /runner, /agency, landing, /search)
│                      messages/*.json hold the 4 locales
├── api/               Flask API + Telegram bot
│   ├── app.py         all HTTP endpoints (auth, cabinet, admin, runner, agency)
│   ├── bot.py         Telegram bot (Mini App + account linking)
│   ├── models.py      SQLAlchemy models
│   ├── catalog.py     packages, services, prices, runner fee
│   ├── notify.py      Telegram notifications
│   ├── deploy/        systemd units + Caddy snippet
│   └── README.md      ops notes
└── payme/             standalone Payme JSON‑RPC webhook (not yet wired to checkout)
```

---

## Running locally

**Frontend**

```bash
cd nothard_website
npm install
npm run dev          # http://localhost:3000
```

**API + bot** (needs a PostgreSQL database)

```bash
cd api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# create api/.env with at least:
#   DATABASE_URL=postgresql+psycopg2://user:pass@127.0.0.1/nothard
#   TELEGRAM_BOT_TOKEN=…        (optional; enables Telegram sign‑in + notifications)
#   JWT_SECRET=…
python app.py        # dev server on :5000 (prod runs gunicorn on :5010)
python bot.py        # optional: the Telegram bot
```

The frontend talks to the API at `/api` (Caddy strips the prefix in production).

---

## Notes

- **Secrets** live in `api/.env` (gitignored): `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `JWT_SECRET`, plus optional mail/Payme keys. Uploaded files under `api/uploads/` are gitignored.
- Deploy artifacts (systemd units, Caddy snippet) are committed under [`api/deploy/`](api/deploy/); operational notes are in [`api/README.md`](api/README.md).

## License

MIT — see [LICENSE](LICENSE). © 2026 Kamronbek Batirov.
