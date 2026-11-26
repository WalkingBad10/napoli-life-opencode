#!/usr/bin/env python3
"""Scarica l'area estesa di Pianura per la v0.6.0, senza toccare il dump v0.5.

Il dump e' usato solo a build-time: il gameplay non chiama API esterne.
Vengono richiesti solo gli elementi necessari alla ricostruzione (strade, edifici,
binari, POI, landuse e barriere), non l'intera bbox. Una seconda interrogazione
limitata ai binari copre il corridoio Circumflegrea verso Montesanto.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "osm"
OUT.mkdir(parents=True, exist_ok=True)

# Area giocabile estesa: circa 1,8 x 1,8 km attorno alla stazione di Pianura.
BBOX = (40.8480, 14.1520, 40.8640, 14.1720)  # south, west, north, east
# Corridoio ferroviario reale verso Montesanto, piu' esteso a sud-ovest.
RAIL_BBOX = (40.8380, 14.1340, 40.8580, 14.1640)

HEADERS = {"User-Agent": "NapoliLife-OpenCode/0.6 (OSM-derived game map; github.com/WalkingBad10)"}
ENDPOINTS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def feature_query(bbox: tuple[float, float, float, float], rail_only: bool = False) -> str:
    s, w, n, e = bbox
    if rail_only:
        clauses = [
            f'way["railway"]({s},{w},{n},{e});',
            f'node["railway"]({s},{w},{n},{e});',
            f'relation["railway"]({s},{w},{n},{e});',
        ]
    else:
        clauses = [
            f'way["highway"]({s},{w},{n},{e});',
            f'way["building"]({s},{w},{n},{e});',
            f'way["railway"]({s},{w},{n},{e});',
            f'way["landuse"]({s},{w},{n},{e});',
            f'way["leisure"]({s},{w},{n},{e});',
            f'way["natural"]({s},{w},{n},{e});',
            f'way["barrier"]({s},{w},{n},{e});',
            f'node["highway"]({s},{w},{n},{e});',
            f'node["building"]({s},{w},{n},{e});',
            f'node["railway"]({s},{w},{n},{e});',
            f'node["public_transport"]({s},{w},{n},{e});',
            f'node["shop"]({s},{w},{n},{e});',
            f'node["amenity"]({s},{w},{n},{e});',
            f'node["place"]({s},{w},{n},{e});',
            f'node["barrier"]({s},{w},{n},{e});',
            f'relation["railway"]({s},{w},{n},{e});',
        ]
    return "[out:json][timeout:240];\n(\n" + "\n".join(clauses) + "\n);\nout ids tags geom;"


def fetch(query: str) -> tuple[list[dict], str]:
    error: Exception | None = None
    for endpoint in ENDPOINTS:
        try:
            print(f"Interrogazione {endpoint} ...", flush=True)
            response = requests.post(endpoint, data={"data": query}, headers=HEADERS, timeout=300)
            response.raise_for_status()
            elements = response.json().get("elements", [])
            if not elements:
                raise RuntimeError("risposta vuota")
            return elements, endpoint
        except Exception as exc:  # prova il mirror successivo
            error = exc
            print(f"  fallito: {exc}", flush=True)
    raise RuntimeError(f"Nessun endpoint Overpass disponibile: {error}")


def main() -> None:
    old_meta = OUT / "latest.json"
    if old_meta.exists() and not (OUT / "latest_v05.json").exists():
        (OUT / "latest_v05.json").write_text(old_meta.read_text(encoding="utf-8"), encoding="utf-8")

    main_elements, endpoint = fetch(feature_query(BBOX))
    rail_elements, rail_endpoint = fetch(feature_query(RAIL_BBOX, rail_only=True), )

    merged: dict[tuple[str, int], dict] = {}
    for element in main_elements + rail_elements:
        key = (element["type"], element["id"])
        if key not in merged:
            merged[key] = element

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    outfile = OUT / f"pianura_expanded_{stamp}.json"
    payload = {"elements": list(merged.values())}
    outfile.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    meta = {
        "captured_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "endpoint": endpoint,
        "rail_endpoint": rail_endpoint,
        "bbox_latlon": list(BBOX),
        "rail_bbox_latlon": list(RAIL_BBOX),
        "query": feature_query(BBOX),
        "rail_query": feature_query(RAIL_BBOX, rail_only=True),
        "file": outfile.name,
        "elements": len(merged),
        "station_node": 4936292644,
        "station_latlon": [40.8560001, 14.1624307],
        "license": "© OpenStreetMap contributors, ODbL 1.0 — https://www.openstreetmap.org/copyright",
        "version": "0.6.0",
    }
    old_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK: {outfile.name} — {len(merged)} elementi — fonte {endpoint}")


if __name__ == "__main__":
    main()
