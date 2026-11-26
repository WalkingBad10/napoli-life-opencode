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
# Area giocabile v0.6: rettangolo metrico, non piu' il cerchio da 150 m.
# x = est, y = sud, origine sempre al nodo stazione OSM 4936292644.
PLAY_BOUNDS = (-256.0, -320.0, 704.0, 704.0)  # minx, miny, maxx, maxy
SECTOR_M = 64
CONTEXT_MARGIN_M = 48.0  # contesto visivo attorno all'area giocabile
MARGIN_M = CONTEXT_MARGIN_M  # compatibilita' con i vecchi script
PLAY_RADIUS_M = 480.0   # solo per compatibilita' con i consumer 0.5
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)
OX, OY = TO_UTM.transform(STATION_LON, STATION_LAT)

# Due centri scommesse fittizi: nomi e orari simulati, ancorati a edifici OSM
# reali. I POI reali GoldBet/Eurobet restano invariati in `pois`.
FICTIONAL_BOOKMAKERS = (
    {"id": "fictional/scommesse_doro_west", "name": "Scommesse d'oro",
     "anchor": "way/655446563", "expected_center": (-231.5, 78.2)},
    {"id": "fictional/scommesse_doro_east", "name": "Scommesse d'oro",
     "anchor": "way/623181901", "expected_center": (525.2, 416.5)},
)

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


def is_circumflegrea(tags: dict) -> bool:
    """Solo way Ferrovia Circumflegrea documentate nei tag, senza collegamenti inventati."""
    if tags.get("railway") not in ("rail", "construction"):
        return False
    if tags.get("name") == "Ferrovia Circumflegrea":
        return True
    return "Circumflegrea" in str(tags.get("description", ""))


def building_center(elements: list[dict], osm_id: int) -> list[float] | None:
    """Baricentro dei vertici proiettati di un edificio OSM già presente nel dump."""
    for e in elements:
        if e["type"] == "way" and e["id"] == osm_id and "building" in e.get("tags", {}):
            pts = points_of(e)
            if len(pts) >= 4:
                return centroid(pts)
    return None


def main() -> None:
    meta = json.loads((OSM_DIR / "latest.json").read_text(encoding="utf-8"))
    raw = json.loads((OSM_DIR / meta["file"]).read_text(encoding="utf-8"))
    elements = raw["elements"]
    minx, miny, maxx, maxy = PLAY_BOUNDS
    playable = box(minx, miny, maxx, maxy)
    context = box(minx - CONTEXT_MARGIN_M, miny - CONTEXT_MARGIN_M,
                  maxx + CONTEXT_MARGIN_M, maxy + CONTEXT_MARGIN_M)
    context_bounds = [minx - CONTEXT_MARGIN_M, miny - CONTEXT_MARGIN_M,
                      maxx + CONTEXT_MARGIN_M, maxy + CONTEXT_MARGIN_M]

    world: dict = {
        "meta": {
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source_file": meta["file"],
            "osm_captured_utc": meta["captured_utc"],
            "osm_endpoint": meta["endpoint"],
            "license": meta["license"],
            "crs": "EPSG:32633 local tangent origin at OSM node 4936292644",
            "origin_latlon": [STATION_LAT, STATION_LON],
            "play_bounds": list(PLAY_BOUNDS),
            "context_bounds": context_bounds,
            "sector_m": SECTOR_M,
            "expanded": True,
            "play_radius_m": PLAY_RADIUS_M,
            "pixels_per_meter": 16,
            "units": "metres, x=east, y=south",
        },
        "roads": [], "rails": [], "platforms": [], "buildings": [],
        "landcover": [], "parking": [], "barriers": [], "pois": [],
        "fictional_pois": [], "rail_route": [], "colliders": [],
    }

    rail_lines: list[LineString] = []
    for e in elements:
        t = e.get("tags", {})
        p = points_of(e)
        if len(p) < 2 and e["type"] != "node":
            continue
        geom_line = LineString(p) if len(p) >= 2 else None
        bbox = bbox_of(p)

        # Percorso reale completo della Circumflegrea: way già presenti nel dump,
        # con tutti i loro vertici, anche fuori dal contesto. Nessun segmento
        # viene ricostruito fra way che non sono collegate nei dati OSM.
        if e["type"] == "way" and is_circumflegrea(t) and len(p) >= 2:
            world["rail_route"].append({
                "id": f"way/{e['id']}",
                "name": t.get("name", "Ferrovia Circumflegrea"),
                "kind": t.get("railway", "rail"),
                "operator": t.get("operator", ""),
                "description": t.get("description", ""),
                "points": p,
            })

        # POI nominati derivati da way/relation (es. ristoranti mappati come
        # perimetro): si usa il baricentro dei vertici proiettati, con lo stesso
        # limite playable + margin dei POI nodo. Nessun edificio/strada nuovo.
        if (e["type"] in ("way", "relation") and p and t.get("name")
                and (t.get("amenity") or t.get("shop"))):
            cx, cy = centroid(p)
            if box(bbox[0], bbox[1], bbox[2], bbox[3]).intersects(context):
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
            if context.contains(Point(x, y)):
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
            # Le fermate e i segnali OSM sono elementi viari puntuali reali:
            # li si conserva come record stradali (un solo vertice), senza
            # ricostruire alcun tracciato. I crossing restano solo nei POI.
            elif (e["type"] == "node"
                  and t["highway"] in ("bus_stop", "traffic_signals", "stop")
                  and context.contains(Point(p[0]))):
                world["roads"].append({
                    "id": f"node/{e['id']}",
                    "name": t.get("name", ""),
                    "kind": t["highway"],
                    "width_m": 0,
                    "surface": "",
                    "foot": "",
                    "point_feature": True,
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

    world["meta"]["road_way_count"] = sum(
        1 for r in world["roads"] if not r.get("point_feature"))
    world["meta"]["road_node_count"] = sum(
        1 for r in world["roads"] if r.get("point_feature"))

    world["rail_route"].sort(key=lambda r: r["id"])

    # Due centri scommesse fittizi: coordinate prese dal baricentro reale
    # dell'edificio OSM di ancoraggio. Non sostituiscono GoldBet/Eurobet reali.
    for spec in FICTIONAL_BOOKMAKERS:
        osm_id = int(spec["anchor"].split("/")[1])
        center = building_center(elements, osm_id)
        if not center:
            raise RuntimeError(f"edificio di ancoraggio mancante: {spec['anchor']}")
        if (abs(center[0] - spec["expected_center"][0]) > 1.0
                or abs(center[1] - spec["expected_center"][1]) > 1.0):
            raise RuntimeError(f"baricentro inatteso per {spec['anchor']}: {center}")
        world["fictional_pois"].append({
            "id": spec["id"],
            "name": spec["name"],
            "shop": "bookmaker",
            "amenity": "",
            "railway": "",
            "public_transport": "",
            "highway": "",
            "place": "",
            "cuisine": "",
            "opening_hours": "10:00-22:00",
            "fictional": True,
            "style": "yellow",
            "anchor": spec["anchor"],
            "x": center[0],
            "y": center[1],
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
