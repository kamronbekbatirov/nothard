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

## License

[MIT](LICENSE)
