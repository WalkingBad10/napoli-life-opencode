#!/usr/bin/env python3
"""Scarica i dati OpenStreetMap grezzi dell'area della stazione di Pianura.

Uso: python tools/fetch_osm.py
I dati vengono salvati in data/osm/ con metadata di provenienza e licenza.
Nessuna richiesta alle API avviene durante il gameplay: questo script è solo offline/build-time.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "osm"
OUT.mkdir(parents=True, exist_ok=True)

# 600 x 550 m circa, centrati sul fabbricato viaggiatori di Pianura (OSM node 4936292644).
BBOX = (40.8530, 14.1590, 40.8590, 14.1660)  # south, west, north, east
SOUTH, WEST, NORTH, EAST = BBOX
QUERY = f"""[out:json][timeout:180];
(
  nwr({SOUTH},{WEST},{NORTH},{EAST});
);
out ids tags geom;"""

ENDPOINTS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
HEADERS = {"User-Agent": "NapoliLife-OpenCode/0.1 (building OSM-derived game map; github.com/WalkingBad10)"}


def main() -> None:
    last_error: Exception | None = None
    payload: dict | None = None
    used = ""
    for endpoint in ENDPOINTS:
        try:
            print(f"Interrogazione {endpoint} ...", flush=True)
            response = requests.post(endpoint, data={"data": QUERY}, headers=HEADERS, timeout=240)
            response.raise_for_status()
            candidate = response.json()
            if not candidate.get("elements"):
                raise RuntimeError("risposta vuota")
            payload = candidate
            used = endpoint
            break
        except Exception as exc:  # noqa: BLE001 - prova il mirror successivo
            last_error = exc
            print(f"  fallito: {exc}", flush=True)
    if payload is None:
        raise RuntimeError(f"Nessun endpoint Overpass disponibile: {last_error}")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    outfile = OUT / f"pianura_{stamp}.json"
    outfile.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    meta = {
        "captured_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "endpoint": used,
        "bbox_latlon": list(BBOX),
        "query": QUERY,
        "file": outfile.name,
        "elements": len(payload.get("elements", [])),
        "station_node": 4936292644,
        "station_latlon": [40.8560001, 14.1624307],
        "license": "© OpenStreetMap contributors, ODbL 1.0 — https://www.openstreetmap.org/copyright",
    }
    (OUT / "latest.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK: {outfile.name} — {meta['elements']} elementi — fonte {used}")


if __name__ == "__main__":
    main()
