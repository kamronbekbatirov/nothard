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

import json
import math
from typing import Optional

import requests

# Public demo endpoints — good enough to develop against. For production set
# `osrm_url` / `nominatim_url` in operator settings to your own instances.
DEFAULT_OSRM_URL = "https://router.project-osrm.org"
DEFAULT_NOMINATIM_URL = "https://nominatim.openstreetmap.org"
# TfL's official Journey Planner — free London public-transport routing, no server
# to run. Works keyless at low volume; an app key lifts the rate limit.
DEFAULT_TFL_URL = "https://api.tfl.gov.uk"
# Straight-line fallback assumes this average city driving speed.
DEFAULT_FALLBACK_KMH = 25.0

# Travel modes. Each OSRM instance serves ONE profile, so walk/cycle need their
# own self-hosted server; the public demo only does driving. Transit (rail/bus)
# is not an OSRM concept at all — it needs OpenTripPlanner + GTFS — so for now it
# always uses the straight-line estimate at an average transit speed.
MODE_PROFILE = {"car": "driving", "walk": "walking", "cycle": "cycling"}
MODE_SPEED_KMH = {"car": 25.0, "walk": 4.8, "cycle": 15.0, "transit": 30.0}

_UA = {"User-Agent": "Nothard/1.0 (+https://nothard.uz)"}

# Per-line station coordinates {line_id: {normalized_name: (lat, lng)}}, fetched
# once from the TfL Line Route Sequence API and cached for the process lifetime
# (a line's stations rarely change). Used to redraw rail legs cleanly through the
# real stations, because TfL's raw per-leg `lineString` geometry is often tangled.
_LINE_STATIONS: dict = {}


def _station_key(name: str) -> str:
    n = (name or "").lower()
    for junk in (" underground station", " rail station", " dlr station", " station"):
        n = n.replace(junk, "")
    return n.strip()


def _line_stations(line_id: str, base: Optional[str] = None, app_key: Optional[str] = None,
                   timeout: float = 6.0) -> dict:
    """{normalized station name: (lat, lng)} for a TfL line (cached). Empty on error."""
    if not line_id:
        return {}
    if line_id in _LINE_STATIONS:
        return _LINE_STATIONS[line_id]
    b = (base or DEFAULT_TFL_URL).rstrip("/")
    out: dict = {}
    try:
        params = {"app_key": app_key} if app_key else {}
        seq = requests.get(f"{b}/Line/{line_id}/Route/Sequence/all",
                           params=params, headers=_UA, timeout=timeout).json()
        for sps in seq.get("stopPointSequences", []) or []:
            for sp in sps.get("stopPoint", []) or []:
                if sp.get("lat") and sp.get("lon"):
                    out.setdefault(_station_key(sp.get("name", "")), (sp["lat"], sp["lon"]))
    except (requests.RequestException, ValueError, KeyError, TypeError):
        out = {}
    _LINE_STATIONS[line_id] = out
    return out


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


def tfl_journey(from_lat: float, from_lng: float, to_lat: float, to_lng: float,
                app_key: Optional[str] = None, base: Optional[str] = None,
                timeout: float = 8.0) -> Optional[dict]:
    """Real London public-transport itinerary via the TfL Journey Planner API.

    Returns ``{minutes, km, route, source:'tfl', mode:'transit'}`` for the first
    journey (walk + tube/bus/rail legs stitched into one line), or None on any
    error / no journey (e.g. outside London → caller estimates instead). Distance
    is computed from the geometry (TfL's per-leg `distance` is unreliable for rail).
    """
    js = tfl_journeys(from_lat, from_lng, to_lat, to_lng, app_key=app_key, base=base,
                      timeout=timeout, limit=1)
    return js[0] if js else None


def _poly_len(pts: list) -> float:
    return sum(haversine_km(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
               for i in range(len(pts) - 1))


def _detangle(pts: list) -> list:
    """TfL's rail `lineString` (esp. the Elizabeth line) is often badly broken —
    the geometry zigzags/doubles back so the drawn line looks buggy. When a leg's
    polyline is much longer than the straight distance between its endpoints
    (i.e. tangled), first drop points that backtrack against the overall
    direction; if it's STILL tangled, fall back to a clean straight segment
    between the endpoints (a transit schematic — the exact stops are in the legs)."""
    if len(pts) < 4:
        return pts
    straight = haversine_km(pts[0][0], pts[0][1], pts[-1][0], pts[-1][1])
    if straight < 0.3 or _poly_len(pts) <= straight * 1.4:
        return pts  # already reasonable — leave the real curve alone
    ax, ay = pts[0]
    dx, dy = pts[-1][0] - ax, pts[-1][1] - ay
    norm = dx * dx + dy * dy
    if norm < 1e-12:
        return [pts[0], pts[-1]]
    out = [pts[0]]
    max_proj = 0.0
    for p in pts[1:-1]:
        proj = ((p[0] - ax) * dx + (p[1] - ay) * dy) / norm  # 0..1 along start→end
        if proj >= max_proj:  # strictly forward — drop any backtracking
            out.append(p)
            max_proj = proj
    out.append(pts[-1])
    # Still noticeably longer than straight → the geometry is too broken to trust;
    # use a clean endpoint-to-endpoint segment.
    if _poly_len(out) > straight * 1.35:
        return [pts[0], pts[-1]]
    return out


def _rail_leg_via_stations(leg: dict, line_id: str, base, app_key) -> Optional[list]:
    """Rebuild a rail leg's geometry by drawing through its ordered stations'
    real coordinates (clean, like a transit map) instead of TfL's tangled
    per-leg lineString. Returns the point list, or None if not enough stations
    resolve (caller then falls back to de-tangling the raw geometry)."""
    stops = (leg.get("path") or {}).get("stopPoints") or []
    if len(stops) < 2:
        return None
    coords = _line_stations(line_id, base=base, app_key=app_key)
    if not coords:
        return None
    pts: list = []
    # Start from the actual departure point so the line connects to the walk leg.
    dp = leg.get("departurePoint") or {}
    if dp.get("lat") is not None and dp.get("lon") is not None:
        pts.append([dp["lat"], dp["lon"]])
    resolved = 0
    for sp in stops:
        c = coords.get(_station_key(sp.get("name", "")))
        if c:
            if not pts or (pts[-1][0], pts[-1][1]) != c:
                pts.append([c[0], c[1]])
            resolved += 1
    ap = leg.get("arrivalPoint") or {}
    if ap.get("lat") is not None and ap.get("lon") is not None:
        if not pts or (pts[-1][0], pts[-1][1]) != (ap["lat"], ap["lon"]):
            pts.append([ap["lat"], ap["lon"]])
    # Need most stations resolved and a sensible line.
    if resolved < max(2, len(stops) - 2) or len(pts) < 2:
        return None
    return pts


def _parse_tfl_journey(j: dict, base=None, app_key=None) -> dict:
    """One TfL journey object → {minutes, km, route, legs, source, mode}."""
    route: list = []
    legs: list = []
    for leg in j.get("legs") or []:
        leg_pts = 0
        ls = (leg.get("path") or {}).get("lineString")
        mode_name = (leg.get("mode") or {}).get("name") or ""
        line = ""
        line_id = ""
        opts = leg.get("routeOptions") or []
        if opts:
            line = opts[0].get("name") or ""
            ident = (opts[0].get("lineIdentifier") or {})
            line = ident.get("name") or line
            line_id = ident.get("id") or ""
        is_walk = "walk" in mode_name.lower()
        raw: list = []
        # Rail legs: draw through the real stations (clean); walk legs use their
        # own short lineString; fall back to de-tangling the raw geometry.
        if not is_walk and line_id:
            via = _rail_leg_via_stations(leg, line_id, base, app_key)
            if via:
                raw = via
        if not raw and ls:
            try:
                raw = [[p[0], p[1]] for p in json.loads(ls)]  # TfL is [[lat,lng]...]
                if not is_walk:
                    raw = _detangle(raw)
            except (ValueError, TypeError, IndexError):
                raw = []
        route.extend(raw)
        leg_pts = len(raw)
        to_lat = to_lng = None
        ap = leg.get("arrivalPoint") or {}
        if ap.get("lat") is not None and ap.get("lon") is not None:
            to_lat, to_lng = ap["lat"], ap["lon"]
        elif route:
            to_lat, to_lng = route[-1][0], route[-1][1]
        legs.append({
            "mode": mode_name, "line": line,
            "summary": (leg.get("instruction") or {}).get("summary") or "",
            "from": (leg.get("departurePoint") or {}).get("commonName") or "",
            "to": (leg.get("arrivalPoint") or {}).get("commonName") or "",
            "minutes": int(round(leg.get("duration") or 0)),
            "points": leg_pts, "toLat": to_lat, "toLng": to_lng,
        })
    km = sum(
        haversine_km(route[i][0], route[i][1], route[i + 1][0], route[i + 1][1])
        for i in range(len(route) - 1)
    )
    return {
        "minutes": int(round(j.get("duration") or 0)), "km": round(km, 2),
        "route": route, "legs": legs, "source": "tfl", "mode": "transit",
    }


def tfl_journeys(from_lat: float, from_lng: float, to_lat: float, to_lng: float,
                 app_key: Optional[str] = None, base: Optional[str] = None,
                 timeout: float = 8.0, limit: int = 3) -> list:
    """Up to `limit` alternative London transit journeys (each parsed like
    tfl_journey). Empty list on error / no journey (e.g. outside London)."""
    b = (base or DEFAULT_TFL_URL).rstrip("/")
    url = f"{b}/Journey/JourneyResults/{from_lat},{from_lng}/to/{to_lat},{to_lng}"
    params = {"app_key": app_key} if app_key else {}
    try:
        resp = requests.get(url, params=params, headers=_UA, timeout=timeout)
        data = resp.json()
        out = []
        for j in (data.get("journeys") or [])[:limit]:
            parsed = _parse_tfl_journey(j, base=b, app_key=app_key)
            if parsed["route"]:
                out.append(parsed)
        return out
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return []


def _osrm_routes(base: str, profile: str, from_lat: float, from_lng: float,
                 to_lat: float, to_lng: float, timeout: float = 3.5, alternatives: int = 2) -> list:
    """OSRM `/route` with alternatives → list of {minutes, km, route}."""
    coords = f"{from_lng},{from_lat};{to_lng},{to_lat}"
    url = f"{base.rstrip('/')}/route/v1/{profile}/{coords}"
    try:
        resp = requests.get(
            url,
            params={"overview": "full", "geometries": "geojson", "alternatives": str(alternatives)},
            headers=_UA, timeout=timeout,
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("code") == "Ok" and data.get("routes"):
            return [{
                "minutes": int(round(r["duration"] / 60)),
                "km": round(r["distance"] / 1000, 2),
                "route": [[c[1], c[0]] for c in r["geometry"]["coordinates"]],
            } for r in data["routes"]]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    return []


def route_options(from_lat: float, from_lng: float, to_lat: float, to_lng: float,
                  osrm_url: Optional[str] = None, walk_url: Optional[str] = None,
                  bike_url: Optional[str] = None, tfl_key: Optional[str] = None,
                  fallback_kmh: float = DEFAULT_FALLBACK_KMH) -> list:
    """All the ways to get from A to B, for the operator/runner to pick from —
    instead of auto-choosing the fastest. Returns a list of options, each:
    ``{id, mode, source, minutes, km, route, legs}`` (legs only for transit).
    Sorted fastest-first within/across kinds so the top one is the default hint."""
    osrm = osrm_url or DEFAULT_OSRM_URL
    opts: list = []

    # Real London transit alternatives (TfL) — usually the meaningful choices.
    for i, j in enumerate(tfl_journeys(from_lat, from_lng, to_lat, to_lng, app_key=tfl_key)):
        opts.append({**j, "id": f"transit-{i}"})

    # Car — the driving route + any alternatives OSRM returns.
    for i, r in enumerate(_osrm_routes(osrm, "driving", from_lat, from_lng, to_lat, to_lng)):
        opts.append({**r, "id": f"car-{i}", "mode": "car", "source": "osrm", "legs": []})

    # Walk / cycle — a dedicated server if configured, else a road-following estimate.
    for mode, url in (("walk", walk_url), ("cycle", bike_url)):
        rs = _osrm_routes(url, MODE_PROFILE[mode], from_lat, from_lng, to_lat, to_lng) if url else []
        if rs:
            opts.append({**rs[0], "id": mode, "mode": mode, "source": "osrm", "legs": []})
        else:
            # Estimate from the car road path at the mode's speed (dashed on the map).
            car = _osrm_routes(osrm, "driving", from_lat, from_lng, to_lat, to_lng)
            if car:
                km = car[0]["km"]
                spd = MODE_SPEED_KMH.get(mode, fallback_kmh)
                opts.append({
                    "id": mode, "mode": mode, "source": "approx",
                    "minutes": int(round((km / spd) * 60)) if km else 0,
                    "km": km, "route": car[0]["route"], "legs": [],
                })

    # Nothing from any router → a single straight-line estimate.
    if not opts:
        sl = _straight_line(from_lat, from_lng, to_lat, to_lng, fallback_kmh)
        opts.append({**sl, "id": "line-0", "mode": "car", "legs": []})

    opts.sort(key=lambda o: o.get("minutes") or 9999)
    return opts


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


def _osrm_route(base: str, profile: str, from_lat: float, from_lng: float,
                to_lat: float, to_lng: float, timeout: float = 3.5) -> Optional[dict]:
    """One OSRM `/route` call → ``{minutes, km, route}`` or None. OSRM wants
    lon,lat and returns geometry as [[lon,lat]...] which we flip to [[lat,lng]...]."""
    coords = f"{from_lng},{from_lat};{to_lng},{to_lat}"
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
            return {
                "minutes": int(round(r["duration"] / 60)),
                "km": round(r["distance"] / 1000, 2),
                "route": [[c[1], c[0]] for c in r["geometry"]["coordinates"]],
            }
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    return None


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
    tfl_key: Optional[str] = None,
    fallback_kmh: float = DEFAULT_FALLBACK_KMH,
    timeout: float = 3.5,
) -> dict:
    """Route + ETA from one point to another for the given travel `mode`.

    Returns ``{minutes, km, route: [[lat,lng]...], source, mode}``. ``source``:
      * ``"osrm"`` / ``"otp"`` — a REAL route for this mode (solid line).
      * ``"approx"`` — a road-following line (from the car network) with a
        mode-speed time estimate, used when this mode has no dedicated router yet.
      * ``"line"`` — last-resort straight-line estimate.
    Never raises — every failure degrades to the next-best option.
    """
    if mode not in MODE_SPEED_KMH:
        mode = "car"
    speed = fallback_kmh if (mode == "car" and fallback_kmh) else MODE_SPEED_KMH[mode]
    car_url = osrm_url or DEFAULT_OSRM_URL

    # 1) A real route for this exact mode, when we have the right engine/server.
    if mode == "transit":
        # A self-hosted OTP (if configured) wins; otherwise TfL's free Journey
        # Planner gives real London tube/bus/rail routing with no server to run.
        if otp_url:
            r = otp_route(from_lat, from_lng, to_lat, to_lng, otp_url)
            if r:
                return r
        r = tfl_journey(from_lat, from_lng, to_lat, to_lng, app_key=tfl_key)
        if r:
            return r
    else:
        # One OSRM instance = one profile, so walk/cycle only get a real route
        # from their own server (never the car server, which would mislabel it).
        dedicated = {"car": car_url, "walk": walk_url, "cycle": bike_url}[mode]
        if dedicated:
            real = _osrm_route(dedicated, MODE_PROFILE[mode], from_lat, from_lng, to_lat, to_lng, timeout)
            if real:
                real.update({"source": "osrm", "mode": mode})
                return real

    # 2) No dedicated router → draw the car road path as an approximation and
    #    estimate the time from the mode's average speed over that road distance.
    if mode != "car":
        approx = _osrm_route(car_url, "driving", from_lat, from_lng, to_lat, to_lng, timeout)
        if approx:
            km = approx["km"]
            return {
                "minutes": int(round((km / speed) * 60)) if km > 0 else 0,
                "km": km,
                "route": approx["route"],
                "source": "approx",
                "mode": mode,
            }

    # 3) Last resort — straight line.
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
