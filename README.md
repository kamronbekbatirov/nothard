# nothard.uz

The full source for **nothard.uz** — a property and services platform for the Uzbek market that connects three sides: tenants (often students), agencies that list properties, and runners who execute on-the-ground tasks for both. The repository is a small monorepo with three independent services that communicate over HTTP and Telegram.

| Service | Stack | Live port | What it does |
| --- | --- | --- | --- |
| [`nothard_website/`](nothard_website/) | Next.js 16 frontend + Flask 3 backend | 3005 + 5000 | Public site, agency dashboard, admin panel, runner panel |
| [`telegram_bot/`](telegram_bot/) | Python + python-telegram-bot 20 | — | Conversational entry point: search, cart, orders, payments |
| [`payme/`](payme/) | Python + Flask | 5001 | Payme.uz JSON-RPC merchant webhook |

[![Live](https://img.shields.io/badge/live-nothard.uz-000?style=flat-square)](https://nothard.uz)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

## What the platform does, end to end

A tenant — typically an international student — opens the bot, completes a 4-step registration (name, phone, email, password that is verified against the website account) and is routed into the search flow. They specify rooms, price, location, furnishing, living type — the bot returns matching listings, and they can:

- **Like** properties they find interesting (`property_search.py`)
- **Add to cart** and **place an order** with multiple properties at once
- **Buy supplementary services** (cleaning, paperwork, transport) from the runner side
- **Pay through Telegram Payments** — invoices are issued via the bot and confirmed by the Payme webhook
- **Track their order's tasks** as runners complete them
- **Earn linking bonuses** for connecting their bot account to the website (`subscribe.py`)
- **Leave feedback** on completed orders

On the operator side:

- **Agencies** log into the website, post properties, and respond to tenant requests
- **Runners** receive tasks assigned by the admin and update task status from their own panel
- **Admins** approve agencies, manage events, view feedback, change order status, and credit bonuses

## Architecture at a glance

```
                       ┌───────────────────────────────┐
       Browsers ───▶   │  Caddy (TLS + edge cache)     │
                       └──────────────┬────────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
       ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
       │ Next.js frontend │  │  Flask API       │  │  Payme webhook   │
       │  (port 3005)     │  │  (port 5000)     │  │  (port 5001)     │
       │  Public site,    │  │  Auth + students │  │  JSON-RPC merch- │
       │  /agency,        │  │  + agencies +    │  │  ant protocol    │
       │  /admin,         │  │  service-        │  │  (7 methods)     │
       │  /runner         │  │  requests/tasks  │  │                  │
       └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
                │                     │                     │
                └─────────┬───────────┴─────────┬───────────┘
                          ▼                     ▼
                  ┌────────────────┐    ┌──────────────────┐
                  │  SQLite        │    │  Redis           │
                  │  (auth/data)   │    │  (sessions,      │
                  │                │    │   rate limits)   │
                  └────────────────┘    └──────────────────┘
                          ▲
                          │
                  ┌──────────────────┐
                  │  Telegram bot    │       (long-running Python process)
                  │  python-telegram │       conversational state machine
                  │     -bot 20      │
                  └──────────────────┘
```

Every service can be developed and deployed independently. They share two things: a SQLite database (read by the Flask API and the bot) and Redis (for sessions and short-lived state).

---

## 1. `nothard_website/` — frontend + API

### Next.js frontend (port 3005)
Eight pages built on Next.js 16 + React 19 + Radix UI + Tailwind CSS:

| Page | What it does |
| --- | --- |
| `/` | Landing page |
| `/login`, `/register` | Tenant authentication |
| `/profile` | Tenant profile and order history |
| `/search` | Property search with filters |
| `/agency` | Agency dashboard — manage listed properties |
| `/runner` | Runner panel — see and update assigned tasks |
| `/admin` | Admin console — users, events, feedback, orders |

### Flask API (port 5000)
21 endpoints in `app.py`, grouped by responsibility:

```
Authentication (Telegram-driven and password)
  POST /telegram_auth_request, /check_telegram_auth, /telegram_auth_confirm
  POST /validate_login_token
  POST /register, /login

Profile
  POST /update_profile
  GET  /profile/<user_id>

Students
  GET  /api/students         (list)
  POST /api/students         (create)

Service requests + tasks
  GET  /api/service-requests
  POST /api/service-requests
  GET  /api/service-requests/<id>/tasks
  PUT  /api/service-requests/<id>/status
  PUT  /api/tasks/<id>/status

Catalogue & people
  GET  /api/service-types
  GET  /api/agencies
  GET  /api/runners

Assignment
  POST /api/assign-runner
```

Auth uses bcrypt-hashed passwords plus Redis-backed Telegram one-time tokens that are issued by the bot and consumed by the website to log in without typing a password.

### Stack
- Next.js 16, React 19, Tailwind CSS, Radix UI primitives, lucide-react
- Flask 3, Flask-CORS, SQLite via `sqlite3`, bcrypt, Redis client, python-dotenv

### Running locally

```bash
cd nothard_website
cp .env.example .env.local
npm install
npm run dev          # Next.js dev server on http://localhost:3000

# in a second terminal — the Flask API:
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors bcrypt python-dotenv redis
python app.py        # Flask dev server on http://localhost:5000
```

---

## 2. `telegram_bot/` — conversational entry point

A long-running Python process built on `python-telegram-bot 20.0`. The state machine is large — 13 handler modules in `bot/handlers/`:

| Handler | Responsibility |
| --- | --- |
| `registration.py` | 4-step sign-up, phone capture, password creation, **website-account verification** (so the bot account is linked to a website user from day one) |
| `property_search.py` | Multi-step filter (rooms → price → property type → furnish → living type → results), pagination, likes, cart, order placement, **Telegram Payments + Payme** flow |
| `addproperty.py` | Agencies post listings via shared cloud-storage link |
| `services.py` | Catalogue of supplementary services (cleaning, paperwork, transport) — added to cart alongside properties |
| `subscribe.py` | Linking bonuses: when a bot account also has a website account, the user unlocks bonus property suggestions |
| `orders.py` | Order timeline view |
| `profile_management.py` | Edit profile fields one at a time |
| `feedback.py` | Post-order feedback flow |
| `admin.py` | Operator commands: events, view users, view orders, view feedback, send broadcast, credit bonuses, update task / order / payment status |
| `common.py`, `info.py`, `oferta.py`, `contact.py`, `language.py` | Static screens, language switcher, ToS, contact card |

### Database

A single SQLite file (`bot.db`, ignored by git) holds users, properties, orders, tasks, feedback, events, bonuses. The Flask API reads the same file. The schema is bootstrapped by `bot/utils/database.py:init_db()` on first launch.

### Stack
- python-telegram-bot 20.0
- Flask 3 + Flask-Login + Flask-WTF + email_validator (the bot bundles a small auxiliary Flask app, mostly for the admin web view)
- SQLAlchemy 1.4 (used in a few helpers)
- python-dotenv, requests, beautifulsoup4 (for parsing shared listing links)
- httpx 0.23, cryptography 43

### Running locally

```bash
cd telegram_bot
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## 3. `payme/` — Payme.uz webhook

A minimal Flask service that implements **the seven JSON-RPC methods** required by the Payme merchant cabinet:

```
CheckPerformTransaction   ↩ check that the user / amount is valid
CreateTransaction         ↩ create a pending transaction
CheckTransaction          ↩ poll status
PerformTransaction        ↩ confirm successful payment
CancelTransaction         ↩ refund / void
GetStatement              ↩ daily reconciliation
ChangePassword            ↩ rotate merchant password
```

On a successful `PerformTransaction` the service forwards a confirmation message to the bot using the `BOT_TOKEN` from its `.env`. The transaction log is kept in SQLite.

### Running locally

```bash
cd payme
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
gunicorn -w 2 -b 127.0.0.1:5001 wsgi:app
```

---

## Configuration

Each subproject documents its own variables in its own `.env.example`:

- [`nothard_website/.env.example`](nothard_website/.env.example) — `NEXT_PUBLIC_API_URL`, `API_URL`
- [`telegram_bot/.env.example`](telegram_bot/.env.example) — full set: bot tokens, Payme keys, Redis, admin credentials
- [`payme/.env.example`](payme/.env.example) — bot token used to forward payment confirmations

Never commit a real `.env`. The repository's root `.gitignore` already blocks them, plus `*.db`, `__pycache__/`, `venv/`, `node_modules/`, and runtime artefacts (`gunicorn.ctl`, `*.log`).

## Production deployment

The services run on a single VPS as four systemd units, each as its own user, fronted by Caddy:

| Unit | Binds to | Purpose |
| --- | --- | --- |
| `nothard.service` | `127.0.0.1:3005` | Next.js frontend |
| `nothard-api.service` | `127.0.0.1:5000` | Flask API (gunicorn, 2 workers) |
| `nothard-payme.service` | `127.0.0.1:5001` | Payme webhook (gunicorn, 2 workers) |
| `nothard-bot.service` | n/a | Long-running Telegram bot process |

Reference Caddy configuration:

```caddy
nothard.uz, www.nothard.uz {
    handle /api/*    { reverse_proxy 127.0.0.1:5000 }
    handle /payme/*  { reverse_proxy 127.0.0.1:5001 }
    handle           { reverse_proxy 127.0.0.1:3005 }
}
```

## License

Released under the [MIT License](LICENSE).
