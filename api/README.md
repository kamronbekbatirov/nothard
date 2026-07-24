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

## Live runner tracking (Traccar Client → OSRM ETA)

The runner shares their location during a journey (e.g. airport → the client's
home); the client and their family watch a live map with a road-following ETA.

**On the runner's phone** — the free, open-source **Traccar Client** app (iOS &
Android). In the runner panel (`/runner`) each runner sees their **Server URL**
(`https://nothard.uz/api/track`) and **Device identifier** (their `track_token`).
Configure Traccar Client with protocol **OsmAnd**, ~30 s interval, 50 m distance.
No login on the phone — pings authenticate by the device id == `track_token`.

**Flow:** runner taps *Start trip* (picks a client + destination address, which
is geocoded) → Traccar Client streams pings to `POST /track` → the backend caches
a route/ETA (recomputed every `tracking_refresh_sec`) → client `/me/trip` and
family `/share/<token>/live` render it on a Leaflet + OpenStreetMap map.

**Routing/geocoding are pluggable** (operator settings, Admin → Tracking):
- `osrm_url` — OSRM for the road route + duration. Defaults to the public demo
  `router.project-osrm.org`, which is **non-commercial / 1 req-s only** — for
  production **self-host OSRM** (Docker, England extract):
  ```
  wget http://download.geofabrik.de/europe/great-britain/england-latest.osm.pbf
  docker run -t -v "$PWD:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/england-latest.osm.pbf
  docker run -t -v "$PWD:/data" osrm/osrm-backend osrm-partition /data/england-latest.osrm
  docker run -t -v "$PWD:/data" osrm/osrm-backend osrm-customize /data/england-latest.osrm
  docker run -d -p 5000:5000 -v "$PWD:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/england-latest.osrm
  ```
  then set `osrm_url` to `http://127.0.0.1:5000`.
- `nominatim_url` — geocoder for the destination address (self-host for volume).
- `tracking_fallback_kmh` — if the router is unreachable, ETA degrades to a
  straight-line estimate at this average speed (never fails).

Everything is open-source and free; the demo servers are fine for testing.

### Travel modes (car / walk / cycle / transit)

The runner picks a travel mode; the ETA/route adapt:
- **car** — OSRM driving (`osrm_url`); works now.
- **walk / cycle** — need a *separate* OSRM instance built with the foot/bike
  profile (one OSRM = one profile). Set `osrm_walk_url` / `osrm_bike_url` in
  Admin → Tracking. Blank → that mode uses a straight-line estimate at an average
  speed (walk 4.8, cycle 15 km/h). Never route walk/cycle at the car server — it
  would return a car route mislabelled.
- **transit** (train/bus) — not an OSRM concept; needs **OpenTripPlanner + GTFS**
  (TfL publishes GTFS for London). Until that's wired, transit is a straight-line
  estimate at ~30 km/h, clearly shown as approximate (dashed line). `routing.py`
  already branches on mode, so adding an OTP call there is the only change needed.

  **Deploy OTP (real transit):** OTP2 is a Java service. Roughly:
  ```
  # 1. Data: an OSM extract for the walking legs + GTFS feeds for London.
  #    TfL publishes GTFS (tube/bus/rail) via its open-data portal / data.gov.uk.
  mkdir otp && cd otp
  wget -O england.osm.pbf http://download.geofabrik.de/europe/great-britain/england-latest.osm.pbf
  #    drop one or more GTFS zip files (e.g. tfl-gtfs.zip) into this folder
  # 2. Build the graph (needs Java 17+ and several GB of RAM):
  java -Xmx6G -jar otp-2.x-shaded.jar --build --save .
  # 3. Serve it:
  java -Xmx6G -jar otp-2.x-shaded.jar --load . --port 8080
  ```
  Then set **Admin → Tracking → OpenTripPlanner** to the GraphQL endpoint
  `http://127.0.0.1:8080/otp/routers/default/index/graphql`. `routing.otp_route()`
  posts a WALK+TRANSIT `plan` query and stitches the leg geometries into the map
  line; on any failure it silently falls back to the straight-line estimate.
