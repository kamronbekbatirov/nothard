# Nothard API (v2) — PostgreSQL

Auth + Telegram + client-cabinet API for the redesigned Nothard platform.
Flask + SQLAlchemy + PostgreSQL. Replaces the old SQLite `nothard_website/app.py`.

## Services (systemd)

| Service                 | Port | What it is                                    |
|-------------------------|------|-----------------------------------------------|
| `nothard.service`       | 3005 | Next.js frontend (redesigned)                 |
| `nothard-api2.service`  | 5010 | **this API** (gunicorn, 1 worker + threads)   |
| `nothard-bot.service`   | —    | `notharduzbot` Telegram bot (long polling)    |
| `nothard-payme.service` | 5001 | Payme webhook (unchanged)                     |

Caddy routes `nothard.uz/api/*` → `strip_prefix /api` → `127.0.0.1:5010`.
The old `nothard-api.service` (SQLite, :5000) has been stopped and disabled.

```bash
sudo systemctl status  nothard-api2 nothard-bot
sudo systemctl restart nothard-api2         # after code changes
sudo journalctl -u nothard-bot -f           # bot logs
```

## Configuration — `api/.env`

See `.env.example`. Already set on this server:

- `DATABASE_URL` — `postgresql+psycopg2://nothard_user:***@127.0.0.1/nothard`
- `JWT_SECRET` — random, keep private
- `TELEGRAM_BOT_TOKEN` — the `notharduzbot` token
- `TELEGRAM_BOT_USERNAME=notharduzbot`
- `MINIAPP_URL` — defaults to `https://nothard.uz/ru/profile`

## Endpoints

```
GET  /                          health
POST /auth/register             {email,password,name,phone?}  -> {access_token, user}
POST /auth/login                {email,password}              -> {access_token, user}
GET  /auth/me                   (Bearer)                       -> user
POST /auth/telegram/miniapp     {init_data}                    -> {access_token, user}   ← Mini App
GET  /auth/telegram/start       -> 302 Telegram OIDC (or ?tg_error=unconfigured)
GET  /auth/telegram/link-start  (Bearer) -> {url}   OIDC url, or bot deep-link
GET  /auth/telegram/callback    -> redirects to frontend with a one-time ticket
POST /auth/telegram/exchange    {ticket} -> {access_token, user}
POST /auth/telegram/unlink      (Bearer)
GET  /me/profile                (Bearer) -> cabinet data
```

## Telegram sign-in — three working paths

1. **Mini App login** (works now, needs only the bot token).
   Opening the bot's Mini App button loads `MINIAPP_URL`; the page validates the
   signed `initData` (HMAC-SHA256) via `/auth/telegram/miniapp` and logs the user
   in, matching on `telegram_id`.

2. **Account linking from the cabinet** (works now).
   In `/profile`, "Привязать Telegram" calls `/auth/telegram/link-start`. Without
   OIDC configured it returns a `t.me/notharduzbot?start=link_<code>` deep link;
   the bot attaches this Telegram account to the web account.

3. **"Continue with Telegram" web sign-in** (needs BotFather Web Login).
   Uses OpenID Connect (Authorization Code + PKCE), mirroring `/var/www/assista`.
   To enable:
   - Open **@BotFather → Mini App → Web Login** for `notharduzbot`.
   - Register allowed URLs: `https://nothard.uz` and redirect
     `https://nothard.uz/api/auth/telegram/callback`.
   - Copy the Client ID / Secret into `api/.env`:
     `TELEGRAM_OIDC_CLIENT_ID=...`, `TELEGRAM_OIDC_CLIENT_SECRET=...`
   - `sudo systemctl restart nothard-api2`

   Until then, `/auth/telegram/start` redirects back with `?tg_error=unconfigured`
   and the two paths above still work.

## BotFather — Mini App

- The chat **menu button** is already set to open the Mini App (`setChatMenuButton`).
- For a richer setup (Launch button on the bot profile, direct
  `t.me/notharduzbot/app` link), create the Mini App in **@BotFather → Mini App →
  New / Edit** and set its URL to `https://nothard.uz/ru/profile`.

## Demo accounts (password `nothard123`)

`operator@nothard.uz` · `agency@nothard.uz` · `runner@nothard.uz` · `client@nothard.uz`

## Schema / migrations

Tables are created on boot via `Base.metadata.create_all` (`db.init_db()`).
For real migrations later, add Alembic. The `users` table holds email/password
(bcrypt), role, and `telegram_id` / `telegram_username` / `tg_link_code`.
