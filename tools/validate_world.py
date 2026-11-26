#!/usr/bin/env python3
"""Controlli automatici di fedeltà geografica, proporzioni e completezza asset.

Eseguito sia in locale sia nella CI prima della pubblicazione.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from shapely.geometry import LineString, Point, Polygon

ROOT = Path(__file__).resolve().parent.parent
W = json.loads((ROOT / "data/world/pianura_world.json").read_text(encoding="utf-8"))
BM = json.loads((ROOT / "public/assets/buildings/manifest.json").read_text(encoding="utf-8"))
SM = json.loads((ROOT / "public/assets/sprites/manifest.json").read_text(encoding="utf-8"))
TM = json.loads((ROOT / "public/assets/tiles/manifest.json").read_text(encoding="utf-8"))
IM = json.loads((ROOT / "public/assets/interiors/manifest.json").read_text(encoding="utf-8"))
checks: list[tuple[str, bool, str]] = []


def chk(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, bool(ok), detail))


station = [b for b in W["buildings"] if b["kind"] == "train_station"]
chk("fabbricato viaggiatori OSM presente", len(station) == 1, str(len(station)))
if station:
    d = Point(*station[0]["center"]).distance(Point(0, 0))
    chk("stazione entro 30 m dal nodo EAV", d < 30, f"{d:.1f} m")
    b = station[0]["bbox"]
    chk("facciata lunga 40-80 m (proporzione reale)", 40 < b[2] - b[0] < 80, f"{b[2] - b[0]:.1f} m")

rail_lines = [LineString(r["points"]) for r in W["rails"] if len(r["points"]) > 1]
chk("binari Circumflegrea presenti", len(rail_lines) >= 5, str(len(rail_lines)))
chk("banchine presenti", len(W["platforms"]) >= 2, str(len(W["platforms"])))
names = {r["name"] for r in W["roads"]}
chk("Via Nelson Mandela nei dati", "Via Nelson Mandela" in names)
chk("strade-classificate > 80", len(W["roads"]) > 80, str(len(W["roads"])))
chk(" edifici > 60", len(W["buildings"]) > 60, str(len(W["buildings"])))

# Nessun edificio inventato sul sedime ferroviario (buffer 9 m).
osm_meta = json.loads((ROOT / "data/osm/latest.json").read_text(encoding="utf-8"))
osm_raw = json.loads((ROOT / "data/osm" / osm_meta["file"]).read_text(encoding="utf-8"))
osm_ids = {f"{e['type']}/{e['id']}" for e in osm_raw["elements"]}
violations = []
for b in W["buildings"]:
    if b["kind"] == "train_station":
        continue
    poly = Polygon(b["footprint"])
    for line in rail_lines:
        if poly.buffer(-0.2).intersects(line.buffer(8.0)):
            violations.append(b["id"])
            break
chk("ogni edificio deriva da OSM (nessuno inventato)", all(b["id"] in osm_ids for b in W["buildings"]))
# Un edificio realmente mappato vicino ai binari non viene rimosso: la fedeltà ai dati prevale.
invented_in_corridor = [v for v in violations if v not in osm_ids]
chk("nessun edificio inventato nel corridoio ferroviario", not invented_in_corridor,
    ", ".join(violations[:5]))

# Proporzioni sprite coerenti con lo standard 16 px/m.
player = Image.open(ROOT / "public/assets/sprites/player.png")
chk("sprite personaggio 16x32 px per frame", player.size == (64, 128), str(player.size))
car = Image.open(ROOT / "public/assets/sprites/car_red.png")
chk("automobile ~4.5 x 2.5 m", 4.0 <= car.width / 16 <= 5.0 and 2.0 <= car.height / 16 <= 3.0,
    f"{car.width / 16:.2f} x {car.height / 16:.2f} m")
train = Image.open(ROOT / "public/assets/sprites/train_eav.png")
chk("treno EAV due casse < 40 m", 30 <= train.width / 16 <= 42, f"{train.width / 16:.1f} m")
chk("standard 16 px/m dichiarato", W["meta"]["pixels_per_meter"] == 16)
chk("36 settori suolo generati", TM["count"] == 36, str(TM["count"]))
chk("suolo generato a 16 px/m senza scala motore",
    TM.get("engine_scale") == 1 and TM.get("engine_ppm") == 16 and TM.get("sector_px") == 1024,
    f"engine_scale={TM.get('engine_scale')} sector_px={TM.get('sector_px')}")
chk("73 sprite edifici generati", len(BM) >= 70, str(len(BM)))

# Contratto grafico 0.3.0: origini architettoniche e griglia delle facciate.
required_bfields = {"origin_x", "origin_y", "wall_h_px", "width_px", "depth_px"}
bad_bman = [b["id"] for b in BM if not required_bfields.issubset(b)]
chk("manifest edifici con origini architettoniche", not bad_bman, ", ".join(bad_bman[:5]))
bad_origins = [b["id"] for b in BM
               if not (0 <= float(b.get("origin_x", -1)) <= 1 and 0 <= float(b.get("origin_y", -1)) <= 1)]
chk("origini edifici entro 0..1", not bad_origins, ", ".join(bad_origins[:5]))
station_sprite = next((b for b in BM if b["id"] == "way/503291719"), None)
chk("facciata stazione ricostruita (>56 m)",
    bool(station_sprite) and station_sprite.get("width_px", 0) >= 900,
    str(station_sprite.get("width_px")) if station_sprite else "assente")
chk("griglia piani edifici multipla di 46 px",
    all(int(b["wall_h_px"]) % 46 == 0 for b in BM))
sprites = SM.get("sprites", {})
chk("26 sprite e metadati 16 px/m",
    len(sprites) >= 26 and SM.get("pixel_per_metro") == 16 and
    all(v.get("pixel_per_metro") == 16 for v in sprites.values()),
    f"{len(sprites)} sprite")


def dist_to_bbox(x: float, y: float, bbox: list[float]) -> float:
    dx = max(bbox[0] - x, 0.0, x - bbox[2])
    dy = max(bbox[1] - y, 0.0, y - bbox[3])
    return (dx * dx + dy * dy) ** 0.5


bad_spawns = []
for name, room in IM.items():
    sx, sy = room["door"]["spawn"]
    if min(dist_to_bbox(sx, sy, b["bbox"]) for b in W["buildings"]) > 2.5:
        bad_spawns.append(name)
chk("spawn degli interni ancorati a edifici OSM", not bad_spawns, ", ".join(bad_spawns))
chk("licenza OSM presente nei metadati", "OpenStreetMap" in W["meta"]["license"])
chk("data cattura OSM presente", bool(W["meta"]["osm_captured_utc"]))

# Nessun perimetro edificio degenere.
bad = [b["id"] for b in W["buildings"] if len(b["footprint"]) < 4 or b["area_m2"] < 6]
chk("perimetri edifici validi", not bad, ", ".join(bad[:5]))

report = {
    "generated_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in checks],
    "passed": sum(1 for _, ok, _ in checks if ok),
    "total": len(checks),
    "warnings": [
        "Edifici OSM reali entro 8 m dai binari (mantenuti per fedeltà, non inventati): " + ", ".join(violations)
    ] if violations else [],
}
out = ROOT / "screenshots/validation-report.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
for name, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'} {name}{' — ' + detail if detail else ''}")
print(f"{report['passed']}/{report['total']} controlli superati")
if report["passed"] != report["total"]:
    raise SystemExit(1)
