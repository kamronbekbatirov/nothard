"""Exact rail-track geometry from OpenStreetMap (via Overpass), so a transit line
is drawn along the real tracks — like a maps app — instead of straight hops
between stations.

TfL's own geometry is tangled and its line-sequence lineStrings are coarse, so we
pull each line's route relations from OSM, chain their track ways into ordered
polylines (one per branch/direction), and slice the portion between a leg's
departure and arrival stations. Everything is cached to disk (OSM changes rarely)
and best-effort: if Overpass is slow/down we return None and the caller falls back
to the smoothed-stations line.
"""

from __future__ import annotations

import json
import math
import os
import time
from typing import Optional

import requests

_UA = {"User-Agent": "Nothard/1.0 (relocation concierge; contact@nothard.uz)"}
_MIRRORS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "osm_cache")
_MEM: dict = {}          # line_id -> [branch_polyline, ...] (in-process cache)
_FAILED_AT: dict = {}    # line_id -> ts of last failed fetch (avoid hammering)
_RETRY_AFTER = 600       # seconds before retrying a failed line

# TfL line id -> (OSM route type, name regex). Covers the tube, Elizabeth line,
# DLR and Overground; anything unmapped just falls back to smoothed stations.
LINE_OSM = {
    "elizabeth": ("train", "^Elizabeth line"),
    "bakerloo": ("subway", "^Bakerloo line"),
    "central": ("subway", "^Central line"),
    "circle": ("subway", "^Circle line"),
    "district": ("subway", "^District line"),
    "hammersmith-city": ("subway", "^Hammersmith"),
    "jubilee": ("subway", "^Jubilee line"),
    "metropolitan": ("subway", "^Metropolitan line"),
    "northern": ("subway", "^Northern line"),
    "piccadilly": ("subway", "^Piccadilly line"),
    "victoria": ("subway", "^Victoria line"),
    "waterloo-city": ("subway", "^Waterloo"),
    "dlr": ("light_rail", "Docklands"),
    "london-overground": ("train", "Overground"),
}


def _hav(a, b, c, d):
    r = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp = math.radians(c - a)
    dl = math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def _chain_ways(rel: dict) -> list:
    """Chain a route relation's track ways (role='') into one ordered polyline,
    flipping each way to keep continuity. PTv2 relations list ways in order."""
    segs = [
        [(g["lat"], g["lon"]) for g in m["geometry"]]
        for m in rel.get("members", [])
        if m.get("type") == "way" and m.get("role", "") == "" and m.get("geometry")
    ]
    if not segs:
        return []
    out = list(segs[0])
    for seg in segs[1:]:
        de = _hav(out[-1][0], out[-1][1], seg[0][0], seg[0][1])
        dr = _hav(out[-1][0], out[-1][1], seg[-1][0], seg[-1][1])
        s = seg if de <= dr else list(reversed(seg))
        gap = _hav(out[-1][0], out[-1][1], s[0][0], s[0][1])
        out.extend(s if gap > 0.02 else s[1:])
    return [[p[0], p[1]] for p in out]


def _overpass(query: str, timeout: float = 8.0) -> Optional[dict]:
    # Try mirrors in order; the first that answers wins. Short per-mirror timeout
    # so an uncached line fails fast to the caller's fallback (it retries later).
    for m in _MIRRORS:
        try:
            r = requests.post(m, data={"data": query}, headers=_UA, timeout=timeout)
            if r.status_code == 200 and r.text.strip().startswith("{"):
                return r.json()
        except (requests.RequestException, ValueError):
            continue
    return None


def _load_disk(line_id: str) -> Optional[list]:
    p = os.path.join(_CACHE_DIR, f"{line_id}.json")
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except (ValueError, OSError):
            return None
    return None


def _save_disk(line_id: str, branches: list) -> None:
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        json.dump(branches, open(os.path.join(_CACHE_DIR, f"{line_id}.json"), "w"))
    except OSError:
        pass


def _line_branches(line_id: str, timeout: float = 8.0) -> list:
    """All chained track polylines for a line (cached: memory → disk → Overpass).
    Empty list if unavailable (caller falls back)."""
    if line_id in _MEM:
        return _MEM[line_id]
    disk = _load_disk(line_id)
    if disk is not None:
        _MEM[line_id] = disk
        return disk
    if line_id not in LINE_OSM:
        _MEM[line_id] = []
        return []
    # Don't hammer a failing line on every request.
    if time.time() - _FAILED_AT.get(line_id, 0) < _RETRY_AFTER:
        return []
    route, name_re = LINE_OSM[line_id]
    q = (f'[out:json][timeout:60];relation["type"="route"]["route"="{route}"]'
         f'["name"~"{name_re}",i];out geom;')
    data = _overpass(q, timeout=timeout)
    if not data:
        _FAILED_AT[line_id] = time.time()
        return []
    branches = []
    for e in data.get("elements", []):
        poly = _chain_ways(e)
        if len(poly) >= 2:
            branches.append(poly)
    if not branches:
        _FAILED_AT[line_id] = time.time()
        return []
    _MEM[line_id] = branches
    _save_disk(line_id, branches)
    return branches


def _nearest(poly: list, pt) -> tuple:
    best_i, best_d = 0, float("inf")
    for i, p in enumerate(poly):
        d = _hav(p[0], p[1], pt[0], pt[1])
        if d < best_d:
            best_i, best_d = i, d
    return best_i, best_d


def rail_segment(line_id: str, from_pt, to_pt, timeout: float = 8.0) -> Optional[list]:
    """Exact track polyline from `from_pt` to `to_pt` along the OSM geometry of the
    given line, or None if OSM isn't available / the points don't snap onto any
    branch. `from_pt`/`to_pt` are (lat, lng)."""
    branches = _line_branches(line_id, timeout=timeout)
    if not branches:
        return None
    best = None
    for poly in branches:
        i1, d1 = _nearest(poly, from_pt)
        i2, d2 = _nearest(poly, to_pt)
        if d1 > 0.6 or d2 > 0.6 or i1 == i2:
            continue
        seg = poly[i1:i2 + 1] if i1 < i2 else list(reversed(poly[i2:i1 + 1]))
        if len(seg) < 2:
            continue
        span = _hav(seg[0][0], seg[0][1], seg[-1][0], seg[-1][1])
        length = sum(_hav(seg[k][0], seg[k][1], seg[k + 1][0], seg[k + 1][1])
                     for k in range(len(seg) - 1))
        # Reject implausible slices (wrong branch → huge detour).
        if span < 0.2 or length > span * 2.2:
            continue
        score = d1 + d2
        if best is None or score < best[0]:
            best = (score, seg)
    return best[1] if best else None
