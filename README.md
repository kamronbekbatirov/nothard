# nothard.uz

> **The student-housing platform for Uzbekistan, run from a Telegram bot.**

[nothard.uz](https://nothard.uz) connects three sides of the rental market in Uzbekistan: **tenants** — usually international students arriving in Tashkent, **agencies** that post listings, and **runners** — local helpers who handle the on-the-ground stuff (cleaning, paperwork, transport). The whole experience starts in Telegram: search for a flat, like the ones you want, drop them in a cart, place an order, pay through Payme, and watch tasks get completed by the runner team.

[![Live](https://img.shields.io/badge/live-nothard.uz-000?style=flat-square)](https://nothard.uz)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://telegram.org)
[![Payme](https://img.shields.io/badge/Pay-Payme-32B2FF?style=flat-square)](https://payme.uz)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

---

## What's in the box

A small monorepo with three independent services that talk over HTTP and Telegram.

| Service | Stack | Port | Role |
| --- | --- | --- | --- |
| 🌐 [`nothard_website/`](nothard_website/) | Next.js 16 + Flask 3 | 3005 + 5000 | Public site, agency dashboard, admin console, runner panel |
| 🤖 [`telegram_bot/`](telegram_bot/) | python-telegram-bot 20 | — | The conversational front door — search, cart, orders, payments |
| 💳 [`payme/`](payme/) | Flask | 5001 | Payme.uz JSON-RPC merchant webhook |

## How it actually works

A student opens the bot, registers in 4 quick steps, and lands in the search flow. They pick: rooms, price, location, furnishing, living type — the bot returns matching listings. From there they can:

- ❤️ **Like** properties they're interested in
- 🛒 **Add to cart** and **place an order** with multiple flats at once
- 🧹 **Buy supplementary services** — cleaning, paperwork, transport — from the runner side
- 💳 **Pay via Telegram Payments** — invoices issued in the bot, confirmed by the Payme webhook
- 📋 **Track each task** as runners complete it
- 🎁 **Earn linking bonuses** for connecting their bot account to the website
- ⭐ **Leave feedback** when the order is done

On the operator side:

- **Agencies** log into the website and post properties
- **Runners** see assigned tasks in their panel and update statuses
- **Admins** approve agencies, manage events, moderate feedback, change order statuses, credit bonuses

## Architecture

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
                  │  Telegram bot    │
                  │  python-telegram │   long-running Python process
                  │     -bot 20      │   conversational state machine
                  └──────────────────┘
```

Every service can be developed and deployed independently. They share two things: a SQLite database (read by the Flask API and the bot) and Redis (for sessions and short-lived state).

## A tour of the three services

### 🌐 `nothard_website/` — the web side

Eight pages on the frontend (Next.js 16 + React 19 + Radix UI + Tailwind) and a small Flask API that serves them:

| Page | What it does |
| --- | --- |
| `/` | Landing |
| `/login`, `/register` | Tenant auth |
| `/profile` | Profile + order history |
| `/search` | Property search |
| `/agency` | Agency dashboard |
| `/runner` | Runner panel |
| `/admin` | Admin console |

The Flask API exposes ~20 endpoints — auth (password + Telegram one-time tokens), profile, students, service requests + tasks, agencies, runners, runner assignment.

### 🤖 `telegram_bot/` — the conversational front door

A long-running Python process (`python-telegram-bot 20`) with 13 handler modules covering:

- 4-step registration with website-account linking
- Multi-step property search (rooms → price → type → furnishing → living type → paginated results, likes, cart, order)
- Property posting for agencies (via shared cloud-storage links)
- Service catalogue (cleaning, paperwork, transport) added to cart alongside properties
- Telegram Payments + Payme flow
- Order timeline, profile editing, feedback
- Admin commands: events, broadcasts, status updates, bonus crediting

### 💳 `payme/` — the payments webhook

A minimal Flask service that implements the seven JSON-RPC methods required by Payme:

```
CheckPerformTransaction   CheckTransaction       CancelTransaction       ChangePassword
CreateTransaction         PerformTransaction     GetStatement
```

On a successful `PerformTransaction`, it forwards a confirmation message to the bot.

## Run it locally

Each subproject has its own `.env.example` and its own commands:

```bash
# 1. The website (Next.js + Flask)
cd nothard_website
cp .env.example .env.local && npm install && npm run dev    # :3000
# in another terminal:
python3 -m venv venv && source venv/bin/activate
pip install flask flask-cors bcrypt python-dotenv redis
python app.py                                                # :5000

# 2. The bot
cd telegram_bot
cp .env.example .env
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py

# 3. Payme webhook
cd payme
cp .env.example .env
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
gunicorn -w 2 -b 127.0.0.1:5001 wsgi:app
```

## Production

Four systemd units on a single VPS, each as its own user, fronted by Caddy:

| Unit | Binds | Role |
| --- | --- | --- |
| `nothard.service` | `127.0.0.1:3005` | Next.js |
| `nothard-api.service` | `127.0.0.1:5000` | Flask API (gunicorn) |
| `nothard-payme.service` | `127.0.0.1:5001` | Payme webhook (gunicorn) |
| `nothard-bot.service` | n/a | Telegram bot process |

```caddy
nothard.uz, www.nothard.uz {
    handle /api/*    { reverse_proxy 127.0.0.1:5000 }
    handle /payme/*  { reverse_proxy 127.0.0.1:5001 }
    handle           { reverse_proxy 127.0.0.1:3005 }
}
```

---

## For contributors / AI agents

> A short technical orientation for anyone (human or AI) being handed this repo for the first time.

### Mental model
**A monorepo with three independent processes**, each with its own runtime, its own deploy unit, and its own job:

1. **`nothard_website/`** — Next.js (TS) for the public site, agency dashboard, admin console, and runner panel + a small Flask app exposing a REST API.
2. **`telegram_bot/`** — Long-running Python process (python-telegram-bot 20). The conversational front door for tenants. Has its own auxiliary Flask app for ops views.
3. **`payme/`** — A tiny Flask service that implements the seven Payme.uz JSON-RPC merchant methods.

They share **two persistence layers**: a SQLite file (`bot.db` — read by the Flask API and the bot) and Redis (sessions + short-lived state). Communication between services goes over HTTP (Next.js → Flask) and Telegram (bot ↔ user, payme → bot for payment confirmation).

### Project tree

```
.
├── nothard_website/                    Next.js + Flask
│   ├── app/                            Next.js App Router pages
│   │   ├── page.tsx                    Landing
│   │   ├── login/, register/           Tenant auth
│   │   ├── profile/                    Tenant profile + order history
│   │   ├── search/                     Property search
│   │   ├── agency/                     Agency dashboard
│   │   ├── runner/                     Runner panel
│   │   └── admin/                      Admin console
│   ├── components/                     React components
│   ├── lib/, app/api/                  Frontend helpers + Next API routes
│   ├── app.py                          ★ Flask backend (~21 endpoints)
│   ├── wsgi.py                         gunicorn entrypoint
│   ├── property_typefinder.py          Listing categorisation helper
│   └── DOCUMENTATION.md                Internal API doc
│
├── telegram_bot/                       Conversational entry point
│   ├── main.py                         Bootstrap: registers handlers, starts polling
│   ├── web_app.py · app_ready.py       Auxiliary Flask (admin web view)
│   ├── bot/
│   │   ├── handlers/                   13 handler modules (state machine)
│   │   │   ├── registration.py         4-step sign-up + website link
│   │   │   ├── property_search.py      Filter wizard, cart, order, Payme flow
│   │   │   ├── addproperty.py          Agency listing posting
│   │   │   ├── services.py             Supplementary-services catalogue
│   │   │   ├── subscribe.py            Bot↔website linking bonuses
│   │   │   ├── orders.py               Order timeline
│   │   │   ├── profile_management.py   Edit profile fields
│   │   │   ├── feedback.py             Post-order feedback
│   │   │   ├── admin.py                Operator commands
│   │   │   └── common.py · info.py · oferta.py · contact.py · language.py
│   │   ├── keyboards/                  Inline keyboards
│   │   └── utils/database.py           init_db() + helpers (writes to bot.db)
│   ├── bot.db                          SQLite (gitignored) — shared with Flask API
│   ├── images/, templates/             Bot media + Flask templates
│   ├── payme.py                        Bot-side Payme helper
│   ├── group.py · get.py · forms.py    Misc helpers
│   └── requirements.txt
│
├── payme/                              Payme.uz JSON-RPC webhook
│   ├── app.py                          7 merchant methods
│   ├── wsgi.py                         gunicorn entrypoint
│   ├── payme.db                        Transaction log (gitignored)
│   ├── add_sample_transactions.py      Dev seed
│   └── requirements.txt
│
├── README.md
└── LICENSE
```

### Where things live

| You want to … | Open … |
| --- | --- |
| Add a website page | `nothard_website/app/<route>/page.tsx` |
| Add a website API endpoint | A handler in `nothard_website/app.py` (Flask) |
| Add a bot screen / state | A new handler in `telegram_bot/bot/handlers/` + register it in `main.py` |
| Change the search wizard logic | `telegram_bot/bot/handlers/property_search.py` |
| Touch DB schema | `telegram_bot/bot/utils/database.py` (`init_db()` is the source of truth — both bot and Flask read the same file). Add a migration shim if existing rows need backfill. |
| Touch payment flow | `telegram_bot/bot/handlers/property_search.py` (invoice creation) + `payme/app.py` (merchant webhook). Both must agree on the order ID format. |
| Localise bot copy | The handler files themselves — strings live inline, language comes from the user's `language_code` |
| Cron-like sweepers | None right now — orders / tasks are state-machine driven |

### Conventions and gotchas

- ⚠️ **One SQLite file. Two writers.** `telegram_bot/bot.db` is opened both by the Flask API and the bot process. SQLite handles this fine for low-write workloads (default journal mode + `-wal` keeps reads non-blocking), but **never run heavy migrations while the bot is up** — stop the bot, migrate, restart. There is no separate migration tool; `init_db()` in `database.py` is the source of truth.
- ⚠️ **Telegram Payments + Payme are two-stage.** The bot issues an invoice via Telegram Payments; Payme then hits the `/payme/` webhook with a `CreateTransaction`/`PerformTransaction` cycle; on `PerformTransaction`, the Payme service forwards a confirmation back to the bot. Both sides must agree on the order/account ID format — see `bot/handlers/property_search.py` and `payme/app.py`.
- ⚠️ **The 7 Payme methods are non-negotiable.** Implementing only some of them gets the merchant account flagged. If you change anything in `payme/app.py`, run through all 7 in a sandbox before deploying.
- ⚠️ **Two Flask apps live in this repo.** `nothard_website/app.py` is the user-facing API; `telegram_bot/web_app.py` is an admin-facing view. Don't conflate them or move endpoints between them — they're deployed as separate systemd units.
- ⚠️ **Bot ↔ website account linking is the trust boundary.** The 4-step bot registration verifies the password against an existing website account before promoting the bot user. The "linking bonus" subsystem in `subscribe.py` rewards users who connect both. Don't add bot-only registration that skips this verification.
- **Each service has its own venv and `requirements.txt`.** Don't share a virtualenv across `nothard_website/`, `telegram_bot/`, and `payme/`. Their dependency sets diverge.
- **Each service has its own `.env.example`.** Never commit a real `.env`. The root `.gitignore` blocks `.env`, `*.db`, `__pycache__/`, `venv/`, `node_modules/`, `gunicorn.ctl`, `*.log`.
- **Production = four systemd units.** `nothard.service` (Next.js), `nothard-api.service` (Flask, gunicorn 2 workers), `nothard-payme.service` (Flask, gunicorn 2 workers), `nothard-bot.service` (long-running Python). Each as its own user. The reference Caddy config above routes `/api/*` and `/payme/*` to the right services.
- **The bot uses python-telegram-bot v20** — async-first. `Update`, `ContextTypes`, conversation handlers all follow the v20 API. v13 patterns will not work.
- **Photos for property listings are pulled by URL** (cloud-storage links pasted by agencies into the bot). The bot parses with BeautifulSoup. Don't rewire to a self-hosted upload — the agency workflow specifically wants Google Drive / Dropbox-style sharing.

### Run / build / deploy

```bash
# nothard_website (two processes — Next.js + Flask)
cd nothard_website
cp .env.example .env.local && npm install && npm run dev    # :3000
python3 -m venv venv && source venv/bin/activate
pip install flask flask-cors bcrypt python-dotenv redis
python app.py                                                # :5000

# telegram_bot
cd telegram_bot
cp .env.example .env
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py

# payme
cd payme
cp .env.example .env
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
gunicorn -w 2 -b 127.0.0.1:5001 wsgi:app
```

In production each service runs as a systemd unit on a fixed port — see the table in the *Production* section above. Caddy is the single TLS terminator and router.

## License

[MIT](LICENSE)
