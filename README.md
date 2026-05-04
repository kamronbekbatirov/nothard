# nothard.uz

The full source for **nothard.uz** — a property platform that connects landlords, agencies, and tenants in Tashkent. The repository is a small monorepo with three independent services that talk to each other over HTTP and Telegram:

| Service | Stack | What it does |
| --- | --- | --- |
| [`nothard_website/`](nothard_website/) | Next.js 16 frontend + Flask backend | Public listings, agency dashboard, admin panel. |
| [`telegram_bot/`](telegram_bot/) | Python + python-telegram-bot | The conversational entry point: registration, listing posting, search, and payment confirmation. |
| [`payme/`](payme/) | Python + Flask | Webhook handler for the Payme.uz payment provider. |

[![Live](https://img.shields.io/badge/live-nothard.uz-000?style=flat-square)](https://nothard.uz)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

## Architecture at a glance

```
                       ┌───────────────────────────────┐
       Browsers ───▶   │  Caddy (TLS, WAF, edge cache) │
                       └──────────────┬────────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
       ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
       │ Next.js frontend │  │  Flask API       │  │  Payme webhook   │
       │  (port 3005)     │  │  (port 5000)     │  │  (port 5001)     │
       └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
                │                     │                     │
                └─────────┬───────────┴─────────┬───────────┘
                          ▼                     ▼
                  ┌────────────────┐    ┌──────────────────┐
                  │  PostgreSQL    │    │  Redis (queues)  │
                  └────────────────┘    └──────────────────┘
                          ▲
                          │
                  ┌──────────────────┐
                  │  Telegram bot    │       (long-running Python process)
                  │  python-telegram │
                  │     -bot         │
                  └──────────────────┘
```

Every service can be developed and deployed independently. The Next.js frontend, the Flask API, the Payme webhook, and the Telegram bot each ship with their own `package.json` / `requirements.txt` and their own `.env.example`.

---

## 1. `nothard_website/` — frontend + API

A Next.js 16 frontend (App Router, React 19, Radix UI, Tailwind) that consumes a Flask + Flask-CORS backend in the same directory. The frontend covers:

- Public landing and search pages
- Authenticated agency dashboard (`/agency`)
- Property registration flow (`/register`)
- Tenant profile (`/profile`)
- Admin console (`/admin`)
- Custom 404, error, and loading states

The Flask backend (`app.py`, `wsgi.py`) exposes the JSON API consumed by both the frontend and the Telegram bot. Sessions are HMAC-signed; CORS is locked to the production origin.

### Running locally

```bash
cd nothard_website
cp .env.example .env.local
npm install
npm run dev          # Next.js dev server on http://localhost:3000

# in a second terminal — the Flask API:
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors gunicorn python-dotenv
python app.py        # Flask dev server on http://localhost:5000
```

---

## 2. `telegram_bot/` — conversational entry point

A Python bot built on `python-telegram-bot` v20+. It is the primary onboarding surface for tenants and small landlords who do not want to use the web UI. Conversation flows live in `bot/handlers/`:

- **registration** — multi-step sign-up with phone-number capture and password confirmation
- **addproperty** — listing creation by sharing a property link
- **search** — natural-language search over the listings
- **info / oferta** — static info screens, terms of service, contact card
- **payme** — payment kick-off + reconciliation
- **group** — admin-only commands inside the operator group

Templates live in `templates/`, image assets in `images/`, and shared helpers in `bot/utils/`.

### Running locally

```bash
cd telegram_bot
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # see DOCUMENTATION.md if missing
python main.py
```

---

## 3. `payme/` — Payme.uz webhook

A minimal Flask service that implements the Payme JSON-RPC merchant protocol: `CheckPerformTransaction`, `CreateTransaction`, `PerformTransaction`, `CancelTransaction`, `GetStatement`. On a successful payment it forwards a confirmation to the bot via the bot token in `.env`.

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

Each subproject documents its own variables in its `.env.example`:

- [`nothard_website/.env.example`](nothard_website/.env.example)
- [`telegram_bot/.env.example`](telegram_bot/.env.example)
- [`payme/.env.example`](payme/.env.example)

Never commit a real `.env`. The repository's root `.gitignore` already blocks them.

## Production deployment

The services run on a single VPS as four systemd units:

| Unit | Binds to | Purpose |
| --- | --- | --- |
| `nothard.service` | `127.0.0.1:3005` | Next.js frontend |
| `nothard-api.service` | `127.0.0.1:5000` | Flask API (gunicorn, 2 workers) |
| `nothard-payme.service` | `127.0.0.1:5001` | Payme webhook (gunicorn, 2 workers) |
| `nothard-bot.service` | n/a | Long-running Telegram bot process |

A reference Caddy configuration:

```caddy
nothard.uz, www.nothard.uz {
    handle /api/*    { reverse_proxy 127.0.0.1:5000 }
    handle /payme/*  { reverse_proxy 127.0.0.1:5001 }
    handle           { reverse_proxy 127.0.0.1:3005 }
}
```

## License

Released under the [MIT License](LICENSE).
