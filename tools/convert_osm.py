#!/usr/bin/env python3
"""Converte i dati OSM grezzi in un mondo metrico locale, pronto per il motore.

Proiezione: UTM 33N (EPSG:32633), origine nel nodo stazione OSM 4936292644.
Coordinate emesse: x = est in metri, y = sud in metri (asse Y schermo).
1 metro = 16 pixel nel motore (vedi src/config.ts).

Mai chiamato a runtime: i dati convertiti sono committed nel repository.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
OSM_DIR = ROOT / "data" / "osm"
OUT_DIR = ROOT / "data" / "world"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATION_LAT, STATION_LON = 40.8560001, 14.1624307
PLAY_RADIUS_M = 150.0  # area giocabile ~300 x 300 m
MARGIN_M = 45.0        # contesto visivo attorno all'area giocabile
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)
OX, OY = TO_UTM.transform(STATION_LON, STATION_LAT)

ROAD_WIDTHS = {
    "motorway": 16, "trunk": 14, "primary": 12, "secondary": 10,
    "secondary_link": 7, "tertiary": 8, "unclassified": 6,
    "residential": 6.5, "living_street": 5, "service": 4,
    "footway": 1.8, "path": 1.5, "pedestrian": 4, "steps": 2.2,
    "crossing": 3.2, "track": 2.5, "cycleway": 1.8,
}


def project(lat: float, lon: float) -> tuple[float, float]:
    """Restituisce (x=est, y=sud) in metri rispetto alla stazione."""
    east, north = TO_UTM.transform(lon, lat)
    return round(east - OX, 3), round(-(north - OY), 3)


def points_of(element: dict) -> list[list[float]]:
    if element["type"] == "node":
        return [list(project(element["lat"], element["lon"]))]
    return [list(project(p["lat"], p["lon"])) for p in element.get("geometry", [])]


def centroid(pts: list[list[float]]) -> list[float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [round(sum(xs) / len(xs), 3), round(sum(ys) / len(ys), 3)]


def bbox_of(pts: list[list[float]]) -> list[float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3)]


def main() -> None:
    meta = json.loads((OSM_DIR / "latest.json").read_text(encoding="utf-8"))
    raw = json.loads((OSM_DIR / meta["file"]).read_text(encoding="utf-8"))
    elements = raw["elements"]
    playable = box(-PLAY_RADIUS_M, -PLAY_RADIUS_M, PLAY_RADIUS_M, PLAY_RADIUS_M)
    context = box(-PLAY_RADIUS_M - MARGIN_M, -PLAY_RADIUS_M - MARGIN_M,
                  PLAY_RADIUS_M + MARGIN_M, PLAY_RADIUS_M + MARGIN_M)

    world: dict = {
        "meta": {
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source_file": meta["file"],
            "osm_captured_utc": meta["captured_utc"],
            "osm_endpoint": meta["endpoint"],
            "license": meta["license"],
            "crs": "EPSG:32633 local tangent origin at OSM node 4936292644",
            "origin_latlon": [STATION_LAT, STATION_LON],
            "play_radius_m": PLAY_RADIUS_M,
            "pixels_per_meter": 16,
            "units": "metres, x=east, y=south",
        },
        "roads": [], "rails": [], "platforms": [], "buildings": [],
        "landcover": [], "parking": [], "barriers": [], "pois": [],
        "colliders": [],
    }

    rail_lines: list[LineString] = []
    for e in elements:
        t = e.get("tags", {})
        p = points_of(e)
        if len(p) < 2 and e["type"] != "node":
            continue
        geom_line = LineString(p) if len(p) >= 2 else None
        bbox = bbox_of(p)

        # POI nominati derivati da way/relation (es. ristoranti mappati come
        # perimetro): si usa il baricentro dei vertici proiettati, con lo stesso
        # limite playable + margin dei POI nodo. Nessun edificio/strada nuovo.
        if (e["type"] in ("way", "relation") and p and t.get("name")
                and (t.get("amenity") or t.get("shop"))):
            cx, cy = centroid(p)
            if playable.buffer(MARGIN_M).contains(Point(cx, cy)):
                world["pois"].append({
                    "id": f"{e['type']}/{e['id']}", "name": t["name"],
                    "shop": t.get("shop", ""), "amenity": t.get("amenity", ""),
                    "railway": "", "public_transport": "", "highway": "",
                    "place": "", "cuisine": t.get("cuisine", ""),
                    "opening_hours": t.get("opening_hours", ""),
                    "x": cx, "y": cy,
                })

        # I POI nodo vanno raccolti prima dello smistamento per highway/railway,
        # altrimenti le fermate e i passaggi pedonali verrebbero scartati dal
        # `continue` delle rispettive categorie.
        if e["type"] == "node" and (t.get("shop") or t.get("amenity") or t.get("railway")
                                    or t.get("public_transport")
                                    or t.get("highway") in ("bus_stop", "crossing")
                                    or t.get("place")):
            x, y = project(e["lat"], e["lon"])
            if playable.buffer(MARGIN_M).contains(Point(x, y)):
                world["pois"].append({
                    "id": f"node/{e['id']}", "name": t.get("name", ""),
                    "shop": t.get("shop", ""), "amenity": t.get("amenity", ""),
                    "railway": t.get("railway", ""), "public_transport": t.get("public_transport", ""),
                    "highway": t.get("highway", ""), "place": t.get("place", ""),
                    "cuisine": t.get("cuisine", ""),
                    "opening_hours": t.get("opening_hours", ""),
                    "x": x, "y": y,
                })

        def intersects(b: list[float], poly=context) -> bool:
            return box(b[0], b[1], b[2], b[3]).intersects(poly)

        if "railway" in t and t["railway"] in ("rail", "tram", "light_rail", "subway", "construction"):
            if intersects(bbox):
                if geom_line:
                    rail_lines.append(geom_line)
                world["rails"].append({
                    "id": f"{e['type']}/{e['id']}", "kind": t["railway"],
                    "name": t.get("name", ""), "points": p,
                })
            continue

        if t.get("railway") == "platform":
            if intersects(bbox) and len(p) >= 3:
                world["platforms"].append({
                    "id": f"{e['type']}/{e['id']}", "footprint": p,
                    "name": t.get("name", ""),
                })
            continue

        if "highway" in t:
            if intersects(bbox) and geom_line:
                world["roads"].append({
                    "id": f"{e['type']}/{e['id']}",
                    "name": t.get("name", ""),
                    "kind": t["highway"],
                    "width_m": ROAD_WIDTHS.get(t["highway"], 5),
                    "surface": t.get("surface", ""),
                    "foot": t.get("foot", ""),
                    "points": p,
                })
            continue

        if "building" in t:
            if intersects(bbox) and len(p) >= 4:
                try:
                    area = abs(Polygon(p).area)
                except Exception:
                    area = 0
                if area < 6 or area > 12000:
                    continue
                world["buildings"].append({
                    "id": f"{e['type']}/{e['id']}",
                    "name": t.get("name", ""),
                    "kind": t.get("building", "yes"),
                    "levels": int(t["building:levels"]) if str(t.get("building:levels", "")).isdigit() else None,
                    "addr": t.get("addr:street", ""),
                    "footprint": p, "center": centroid(p), "bbox": bbox,
                    "area_m2": round(area, 1),
                })
            continue

        if "barrier" in t and geom_line and intersects(bbox):
            world["barriers"].append({
                "id": f"{e['type']}/{e['id']}", "kind": t["barrier"], "points": p,
            })

        if any(k in t for k in ("landuse", "leisure", "natural")) and len(p) >= 3 and intersects(bbox):
            world["landcover"].append({
                "id": f"{e['type']}/{e['id']}",
                "kind": t.get("landuse") or t.get("leisure") or t.get("natural"),
                "name": t.get("name", ""), "footprint": p,
            })

        if t.get("amenity") in ("parking", "bus_station") and len(p) >= 3 and intersects(bbox):
            world["parking"].append({
                "id": f"{e['type']}/{e['id']}", "kind": t["amenity"],
                "name": t.get("name", ""), "footprint": p,
            })

    # Corridoio ferroviario: nessun edificio o albero inventato nei 9 m attorno ai binari.
    if rail_lines:
        corridor = unary_union([line.buffer(9.0) for line in rail_lines])
        world["rail_corridor"] = [
            [list(coord) for coord in ring.coords]
            for poly in (corridor.geoms if hasattr(corridor, "geoms") else [corridor])
            for ring in [poly.exterior]
        ]
    else:
        world["rail_corridor"] = []

    # Collider: edifici (leggermente espansi) + recinzioni + corsia ferroviaria.
    for b in world["buildings"]:
        try:
            poly = Polygon(b["footprint"]).buffer(0.25)
            world["colliders"].append({"kind": "building", "id": b["id"],
                                       "polygon": [[round(x, 3), round(y, 3)] for x, y in poly.exterior.coords]})
        except Exception:
            pass
    for barrier in world["barriers"]:
        if barrier["kind"] in ("fence", "wall", "rail"):
            world["colliders"].append({"kind": "barrier", "id": barrier["id"],
                                       "line": barrier["points"], "width_m": 0.4})
    world["stats"] = {k: len(v) for k, v in world.items() if isinstance(v, list)}

    out = OUT_DIR / "pianura_world.json"
    text = json.dumps(world, ensure_ascii=False, separators=(",", ":"))
    out.write_text(text, encoding="utf-8")
    runtime = ROOT / "public" / "data" / "world"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "pianura_world.json").write_text(text, encoding="utf-8")
    print(f"OK {out.name}: {world['stats']}")


if __name__ == "__main__":
    main()
