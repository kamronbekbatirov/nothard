"""Routing / ETA helpers for live runner tracking.

Everything here is open-source & self-hostable:
  * road route + duration  -> OSRM   (Open Source Routing Machine)
  * address -> coordinates -> Nominatim (OpenStreetMap geocoder)

Both are reached over plain HTTP so the URLs are swappable via operator settings
(default to the public demo servers, which are fine for development but should be
self-hosted for production — see api/README). Every network call has a short
timeout and a graceful fallback, so tracking keeps working even if the routing
server is down: the ETA then falls back to a straight-line estimate.
"""

from __future__ import annotations

import math
from typing import Optional

import requests

# Public demo endpoints — good enough to develop against. For production set
# `osrm_url` / `nominatim_url` in operator settings to your own instances.
DEFAULT_OSRM_URL = "https://router.project-osrm.org"
DEFAULT_NOMINATIM_URL = "https://nominatim.openstreetmap.org"
# Straight-line fallback assumes this average city driving speed.
DEFAULT_FALLBACK_KMH = 25.0

# Travel modes. Each OSRM instance serves ONE profile, so walk/cycle need their
# own self-hosted server; the public demo only does driving. Transit (rail/bus)
# is not an OSRM concept at all — it needs OpenTripPlanner + GTFS — so for now it
# always uses the straight-line estimate at an average transit speed.
MODE_PROFILE = {"car": "driving", "walk": "walking", "cycle": "cycling"}
MODE_SPEED_KMH = {"car": 25.0, "walk": 4.8, "cycle": 15.0, "transit": 30.0}

_UA = {"User-Agent": "Nothard/1.0 (+https://nothard.uz)"}


def _decode_polyline(s: str, precision: int = 5) -> list:
    """Decode a Google-encoded polyline (OTP leg geometry) → [[lat, lng], ...]."""
    index, lat, lng, out = 0, 0, 0, []
    factor = float(10 ** precision)
    while index < len(s):
        for is_lng in range(2):
            shift, result = 0, 0
            while True:
                b = ord(s[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if is_lng == 0:
                lat += delta
            else:
                lng += delta
        out.append([lat / factor, lng / factor])
    return out


def otp_route(from_lat: float, from_lng: float, to_lat: float, to_lng: float,
              otp_url: str, timeout: float = 6.0) -> Optional[dict]:
    """Real public-transport itinerary via OpenTripPlanner (OTP2 GraphQL).

    `otp_url` is the full GraphQL endpoint (e.g.
    ``https://otp.host/otp/routers/default/index/graphql``). Returns
    ``{minutes, km, route, source:'otp', mode:'transit'}`` for the first
    WALK+TRANSIT itinerary, or None on any error (caller then estimates).
    """
    query = (
        "query($from: InputCoordinates!, $to: InputCoordinates!) {"
        "  plan(from: $from, to: $to,"
        "       transportModes: [{mode: WALK}, {mode: TRANSIT}],"
        "       numItineraries: 1) {"
        "    itineraries { duration legs { distance legGeometry { points } } }"
        "  }"
        "}"
    )
    variables = {
        "from": {"lat": from_lat, "lon": from_lng},
        "to": {"lat": to_lat, "lon": to_lng},
    }
    try:
        resp = requests.post(
            otp_url,
            json={"query": query, "variables": variables},
            headers={**_UA, "Content-Type": "application/json"},
            timeout=timeout,
        )
        data = resp.json()
        its = ((data.get("data") or {}).get("plan") or {}).get("itineraries") or []
        if its:
            it = its[0]
            route: list = []
            dist = 0.0
            for leg in it.get("legs") or []:
                dist += leg.get("distance") or 0
                pts = (leg.get("legGeometry") or {}).get("points")
                if pts:
                    route.extend(_decode_polyline(pts))
            return {
                "minutes": int(round((it.get("duration") or 0) / 60)),
                "km": round(dist / 1000, 2),
                "route": route,
                "source": "otp",
                "mode": "transit",
            }
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    return None


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _straight_line(lat1: float, lng1: float, lat2: float, lng2: float,
                   fallback_kmh: float) -> dict:
    km = haversine_km(lat1, lng1, lat2, lng2)
    speed = fallback_kmh if fallback_kmh > 0 else DEFAULT_FALLBACK_KMH
    minutes = int(round((km / speed) * 60)) if km > 0 else 0
    return {
        "minutes": minutes,
        "km": round(km, 2),
        # A plain two-point line — the UI renders it dashed to signal "estimate".
        "route": [[lat1, lng1], [lat2, lng2]],
        "source": "line",
    }


def route_eta(
    from_lat: float,
    from_lng: float,
    to_lat: float,
    to_lng: float,
    mode: str = "car",
    osrm_url: Optional[str] = None,
    walk_url: Optional[str] = None,
    bike_url: Optional[str] = None,
    otp_url: Optional[str] = None,
    fallback_kmh: float = DEFAULT_FALLBACK_KMH,
    timeout: float = 3.5,
) -> dict:
    """Route + ETA from one point to another for the given travel `mode`.

    Returns ``{minutes, km, route: [[lat,lng]...], source, mode}`` where ``source``
    is ``"osrm"`` for a real route or ``"line"`` for the straight-line estimate.
    Never raises — any routing failure degrades to the estimate.

    Each mode uses its own routing server (one OSRM instance = one profile), so
    walk/cycle only follow roads when `walk_url`/`bike_url` are configured; transit
    has no OSRM profile and is always the straight-line estimate for now.
    """
    if mode not in MODE_SPEED_KMH:
        mode = "car"
    speed = fallback_kmh if (mode == "car" and fallback_kmh) else MODE_SPEED_KMH[mode]

    # Transit is a different engine (OpenTripPlanner + GTFS), not OSRM.
    if mode == "transit":
        if otp_url:
            r = otp_route(from_lat, from_lng, to_lat, to_lng, otp_url)
            if r:
                return r
        out = _straight_line(from_lat, from_lng, to_lat, to_lng, speed)
        out["mode"] = "transit"
        return out

    # Pick the routing server for this mode. Never route walk/cycle against the
    # car server — it would return a car route mislabelled as walking.
    base = None
    if mode == "car":
        base = osrm_url or DEFAULT_OSRM_URL
    elif mode == "walk":
        base = walk_url
    elif mode == "cycle":
        base = bike_url

    if base:
        coords = f"{from_lng},{from_lat};{to_lng},{to_lat}"
        profile = MODE_PROFILE.get(mode, "driving")
        url = f"{base.rstrip('/')}/route/v1/{profile}/{coords}"
        try:
            resp = requests.get(
                url,
                params={"overview": "full", "geometries": "geojson", "alternatives": "false"},
                headers=_UA,
                timeout=timeout,
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("code") == "Ok" and data.get("routes"):
                r = data["routes"][0]
                # geometry.coordinates is [[lon,lat], ...] → flip to [[lat,lng], ...]
                line = [[c[1], c[0]] for c in r["geometry"]["coordinates"]]
                return {
                    "minutes": int(round(r["duration"] / 60)),
                    "km": round(r["distance"] / 1000, 2),
                    "route": line,
                    "source": "osrm",
                    "mode": mode,
                }
        except (requests.RequestException, ValueError, KeyError, TypeError):
            pass

    out = _straight_line(from_lat, from_lng, to_lat, to_lng, speed)
    out["mode"] = mode
    return out


def geocode_search(query: str, nominatim_url: Optional[str] = None,
                   limit: int = 6, timeout: float = 4.0) -> list[dict]:
    """Address autocomplete: up to ``limit`` UK matches as ``[{label, lat, lng}]``.

    Backs the runner's "type an address, pick from a list" field so they never
    start a trip against a mistyped/ambiguous address. Returns [] on any error.
    """
    q = (query or "").strip()
    if len(q) < 3:
        return []
    base = (nominatim_url or DEFAULT_NOMINATIM_URL).rstrip("/")
    try:
        resp = requests.get(
            f"{base}/search",
            params={"q": q, "format": "json", "limit": limit, "countrycodes": "gb"},
            headers=_UA,
            timeout=timeout,
        )
        rows = resp.json()
        if resp.status_code == 200 and isinstance(rows, list):
            out = []
            for r in rows:
                try:
                    out.append({
                        "label": r.get("display_name", ""),
                        "lat": float(r["lat"]),
                        "lng": float(r["lon"]),
                    })
                except (KeyError, ValueError, TypeError):
                    continue
            return out
    except (requests.RequestException, ValueError, TypeError):
        pass
    return []


def geocode(query: str, nominatim_url: Optional[str] = None,
            timeout: float = 4.0) -> Optional[dict]:
    """Address string → ``{lat, lng, label}`` via Nominatim, or None.

    Biased to the UK (this is a London relocation service). Nominatim's usage
    policy asks for a real User-Agent and ≤1 req/s — we only geocode once when a
    trip starts, so that's comfortably within limits.
    """
    q = (query or "").strip()
    if not q:
        return None
    base = (nominatim_url or DEFAULT_NOMINATIM_URL).rstrip("/")
    try:
        resp = requests.get(
            f"{base}/search",
            params={"q": q, "format": "json", "limit": 1, "countrycodes": "gb"},
            headers=_UA,
            timeout=timeout,
        )
        rows = resp.json()
        if resp.status_code == 200 and rows:
            row = rows[0]
            return {
                "lat": float(row["lat"]),
                "lng": float(row["lon"]),
                "label": row.get("display_name", q),
            }
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
        pass
    return None
