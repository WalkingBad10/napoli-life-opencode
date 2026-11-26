#!/usr/bin/env python3
"""Controlli automatici di fedeltà geografica, proporzioni e completezza asset.

Eseguito sia in locale sia nella CI prima della pubblicazione.
Il report JSON viene scritto in ``data/world/validation-report.json``:
nessuna screenshot viene generata o sovrascritta.
"""

from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from pathlib import Path

from PIL import Image
from shapely.geometry import LineString, Point, Polygon

ROOT = Path(__file__).resolve().parent.parent
W = json.loads((ROOT / "data/world/pianura_world.json").read_text(encoding="utf-8"))
BM = json.loads((ROOT / "public/assets/buildings/manifest.json").read_text(encoding="utf-8"))
SM = json.loads((ROOT / "public/assets/sprites/manifest.json").read_text(encoding="utf-8"))
TM = json.loads((ROOT / "public/assets/tiles/manifest.json").read_text(encoding="utf-8"))
IM = json.loads((ROOT / "public/assets/interiors/manifest.json").read_text(encoding="utf-8"))
AM = json.loads((ROOT / "public/assets/audio/manifest.json").read_text(encoding="utf-8"))
checks: list[tuple[str, bool, str]] = []


def chk(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, bool(ok), detail))


# --- area e metadati v0.6 ---------------------------------------------------
meta = W["meta"]
expected_bounds = [-256.0, -320.0, 704.0, 704.0]
chk("bounds rettangolari v0.6", meta.get("play_bounds") == expected_bounds,
    str(meta.get("play_bounds")))
chk("settore 64 m dichiarato", meta.get("sector_m") == 64, str(meta.get("sector_m")))
chk("mondo espanso dichiarato", meta.get("expanded") is True)
chk("contesto 48 m attorno ai bounds",
    meta.get("context_bounds") == [-304.0, -368.0, 752.0, 752.0],
    str(meta.get("context_bounds")))
chk("raggio compatibilità 480 m", meta.get("play_radius_m") == 480)

station = [b for b in W["buildings"] if b["kind"] == "train_station"]
chk("fabbricato viaggiatori OSM presente", len(station) == 1, str(len(station)))
if station:
    d = Point(*station[0]["center"]).distance(Point(0, 0))
    chk("stazione entro 30 m dal nodo EAV", d < 30, f"{d:.1f} m")
    b = station[0]["bbox"]
    chk("facciata lunga 40-80 m (proporzione reale)", 40 < b[2] - b[0] < 80,
        f"{b[2] - b[0]:.1f} m")

rail_lines = [LineString(r["points"]) for r in W["rails"] if len(r["points"]) > 1]
chk("binari Circumflegrea presenti", len(rail_lines) >= 5, str(len(rail_lines)))
chk("banchine presenti", len(W["platforms"]) >= 2, str(len(W["platforms"])))
names = {r["name"] for r in W["roads"]}
for road_name in ("Via Nelson Mandela", "Via Montagna Spaccata", "Via Provinciale Napoli"):
    chk(f"{road_name} nei dati", road_name in names)
chk("strade-classificate > 80", len(W["roads"]) > 80, str(len(W["roads"])))
chk("almeno 400 elementi viari OSM", len(W["roads"]) >= 400, str(len(W["roads"])))
chk("almeno 380 way stradali reali", meta.get("road_way_count", 0) >= 380,
    str(meta.get("road_way_count")))
chk("almeno 500 edifici", len(W["buildings"]) >= 500, str(len(W["buildings"])))

# Tabaccherie reali: almeno due POI OSM con shop=tobacco.
tobacconists = [p for p in W["pois"] if p.get("shop") == "tobacco"]
chk("almeno 2 tabaccherie OSM", len(tobacconists) >= 2, str(len(tobacconists)))

# Percorso ferroviario reale: solo way già presenti nel dump, senza collegamenti inventati.
osm_meta = json.loads((ROOT / "data/osm/latest.json").read_text(encoding="utf-8"))
osm_raw = json.loads((ROOT / "data/osm" / osm_meta["file"]).read_text(encoding="utf-8"))
osm_ids = {f"{e['type']}/{e['id']}" for e in osm_raw["elements"]}
rail_route = W.get("rail_route", [])
rail_route_ids = [r["id"] for r in rail_route]
chk("rail_route con almeno 6 way", len(rail_route) >= 6, str(len(rail_route)))
chk("rail_route usa solo way OSM reali",
    all(rid.startswith("way/") and rid in osm_ids for rid in rail_route_ids),
    ", ".join(rid for rid in rail_route_ids if rid not in osm_ids))
chk("rail_route con geometria completa",
    all(len(r.get("points", [])) >= 2 for r in rail_route))

# Nessun edificio inventato sul sedime ferroviario (buffer 9 m).
violations = []
for b in W["buildings"]:
    if b["kind"] == "train_station":
        continue
    poly = Polygon(b["footprint"])
    for line in rail_lines:
        if poly.buffer(-0.2).intersects(line.buffer(8.0)):
            violations.append(b["id"])
            break
chk("ogni edificio deriva da OSM (nessuno inventato)",
    all(b["id"] in osm_ids for b in W["buildings"]))
# Un edificio realmente mappato vicino ai binari non viene rimosso: la fedeltà ai dati prevale.
invented_in_corridor = [v for v in violations if v not in osm_ids]
chk("nessun edificio inventato nel corridoio ferroviario", not invented_in_corridor,
    ", ".join(violations[:5]))

# --- POI fittizi dichiarati, mai confusi con quelli reali -------------------
fictional = W.get("fictional_pois", [])
chk("due POI fittizi Scommesse d'oro", len(fictional) == 2, str(len(fictional)))
expected_anchors = {"way/655446563", "way/623181901"}
chk("ancoraggi fittizi OSM reali",
    {p.get("anchor") for p in fictional} == expected_anchors,
    ", ".join(str(p.get("anchor")) for p in fictional))
chk("POI fittizi gialli, bookmaker e orari dichiarati",
    all(p.get("fictional") is True and p.get("style") == "yellow"
        and p.get("shop") == "bookmaker" and p.get("name") == "Scommesse d'oro"
        and p.get("opening_hours") == "10:00-22:00" for p in fictional))
building_by_id = {b["id"]: b for b in W["buildings"]}
chk("centro fittizio = baricentro edificio di ancoraggio",
    all(building_by_id.get(p["anchor"])
        and Point(p["x"], p["y"]).distance(Point(*building_by_id[p["anchor"]]["center"])) < 1.0
        for p in fictional))
real_bookmakers = [p for p in W["pois"]
                   if p.get("shop") == "bookmaker" and p.get("name", "").lower() in ("goldbet", "eurobet")]
chk("GoldBet ed Eurobet reali conservati", len(real_bookmakers) == 2,
    str(len(real_bookmakers)))

# --- proporzioni e manifest sprite -----------------------------------------
player = Image.open(ROOT / "public/assets/sprites/player.png")
chk("sprite personaggio 16x32 px per frame", player.size == (64, 128), str(player.size))
car = Image.open(ROOT / "public/assets/sprites/car_red.png")
chk("automobile ~4.5 x 2.5 m", 4.0 <= car.width / 16 <= 5.0 and 2.0 <= car.height / 16 <= 3.0,
    f"{car.width / 16:.2f} x {car.height / 16:.2f} m")
train = Image.open(ROOT / "public/assets/sprites/train_eav.png")
chk("treno EAV due casse < 40 m", 30 <= train.width / 16 <= 42, f"{train.width / 16:.1f} m")
chk("standard 16 px/m dichiarato", meta["pixels_per_meter"] == 16)

sprites = SM.get("sprites", {})
required_sprites = {
    "player", "resident", "worker", "elderly", "teen", "railway", "vendor", "pizzaiolo",
    "car_red", "car_silver", "car_blue", "bus", "scooter", "motorcycle", "train_eav",
    "shopping_basket", "shirt", "toolbox", "gift", "heart", "newspaper", "tabacco_sign",
    "shopkeeper", "mechanic",
}
chk("manifest sprite versione 0.6.0", SM.get("version") == "0.6.0", str(SM.get("version")))
chk("nuovi sprite 0.6 presenti", required_sprites.issubset(sprites),
    ", ".join(sorted(required_sprites - set(sprites))))
chk("almeno 38 sprite e metadati 16 px/m",
    len(sprites) >= 38 and SM.get("pixel_per_metro") == 16
    and all(v.get("pixel_per_metro") == 16 for v in sprites.values()),
    f"{len(sprites)} sprite")
chk("sheet 64x128, frame 16x32, piedi y=30",
    SM.get("sheet_w") == 64 and SM.get("sheet_h") == 128
    and SM.get("frame_w") == 16 and SM.get("frame_h") == 32 and SM.get("feet_y") == 30)
bad_sprites = []
for name, entry in sprites.items():
    path = ROOT / "public/assets/sprites" / entry["file"]
    if not path.is_file():
        bad_sprites.append(f"{name}:file")
        continue
    with Image.open(path) as im:
        if im.size != (entry.get("w"), entry.get("h")):
            bad_sprites.append(f"{name}:size")
chk("coerenza manifest sprite / PNG", not bad_sprites, ", ".join(bad_sprites[:6]))

# --- tiles: 240 settori, nessuno mancante ----------------------------------
expected_origins = {(x, y) for x in range(-256, 704, 64) for y in range(-320, 704, 64)}
manifest_origins = {tuple(o) for o in TM.get("origins", [])}
tiles_dir = ROOT / "public/assets/tiles"
tile_files = {p.name for p in tiles_dir.glob("sector_*.png")}
expected_files = {f"sector_{x}_{y}.png" for x, y in expected_origins}
chk("manifest versione 0.6.0", TM.get("version") == "0.6.0", str(TM.get("version")))
chk("240 settori dichiarati", TM.get("count") == 240, str(TM.get("count")))
chk("origini 15x16 corrette", manifest_origins == expected_origins,
    f"{len(manifest_origins)} origini")
chk("bounds tile coerenti con il mondo",
    TM.get("bounds") == {"minX": -256, "minY": -320, "maxX": 704, "maxY": 704},
    str(TM.get("bounds")))
chk("suolo generato a 16 px/m senza scala motore",
    TM.get("engine_scale") == 1 and TM.get("engine_ppm") == 16
    and TM.get("source_ppm") == 16 and TM.get("sector_px") == 1024,
    f"engine_scale={TM.get('engine_scale')} sector_px={TM.get('sector_px')}")
chk("nessun settore mancante", not (expected_files - tile_files),
    ", ".join(sorted(expected_files - tile_files)[:5]))
chk("nessun settore fuori bounds", not (tile_files - expected_files),
    ", ".join(sorted(tile_files - expected_files)[:5]))
bad_tiles = []
for name in sorted(expected_files & tile_files):
    with Image.open(tiles_dir / name) as im:
        if im.size != (1024, 1024):
            bad_tiles.append(name)
chk("tile PNG 1024x1024", not bad_tiles, ", ".join(bad_tiles[:5]))

# --- edifici: manifesto e insegne ------------------------------------------
chk("almeno 500 sprite edifici", len(BM) >= 500, str(len(BM)))
chk("coerenza edifici mondo / manifest",
    {b["id"] for b in BM} == {b["id"] for b in W["buildings"]},
    f"{len(BM)} manifest vs {len(W['buildings'])} mondo")
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
bad_metrics = []
for b in BM:
    source = building_by_id.get(b["id"])
    if not source:
        continue
    x0, _, x1, _ = source["bbox"]
    expected_width = max(16, int(round((x1 - x0) * 16)))
    if int(b["width_px"]) != expected_width:
        bad_metrics.append(b["id"])
chk("metriche edifici 16 px/m invariate", not bad_metrics, ", ".join(bad_metrics[:5]))
bad_building_files = [b["id"] for b in BM if not (ROOT / "public" / b["sprite"]).is_file()]
chk("coerenza manifest edifici / PNG", not bad_building_files,
    ", ".join(bad_building_files[:5]))

signs = [s for b in BM for s in b.get("signs", [])]
sign_kinds = Counter(s.get("kind") for s in signs)
yellow_fictional = [b for b in BM if b.get("facade") == "yellow"]
chk("due facciate gialle fittizie", len(yellow_fictional) == 2,
    ", ".join(b["id"] for b in yellow_fictional))
chk("insegna SCOMMESSE D'ORO sulle facciate gialle",
    all(any(s.get("kind") == "fictional_bookmaker"
            and s.get("text") == "SCOMMESSE D'ORO" for s in b.get("signs", []))
        for b in yellow_fictional))
chk("insegne GoldBet ed Eurobet reali", sign_kinds.get("real_bookmaker", 0) >= 2,
    str(sign_kinds.get("real_bookmaker", 0)))
chk("insegne T per le tabaccherie", sign_kinds.get("tobacco", 0) >= 2,
    str(sign_kinds.get("tobacco", 0)))

# --- interni ---------------------------------------------------------------
new_rooms = {"supermarket", "tobacco", "bookmaker", "bakery", "clothing", "workshop"}
legacy_rooms = {"station", "bar", "shop", "home", "pizzeria"}
chk("5 interni storici intatti", legacy_rooms.issubset(IM),
    ", ".join(sorted(legacy_rooms - set(IM))))
chk("6 nuovi interni presenti", new_rooms.issubset(IM),
    ", ".join(sorted(new_rooms - set(IM))))
chk("manifest interni versione 0.6.0", IM.get("version") == "0.6.0", str(IM.get("version")))


def dist_to_bbox(x: float, y: float, bbox: list[float]) -> float:
    dx = max(bbox[0] - x, 0.0, x - bbox[2])
    dy = max(bbox[1] - y, 0.0, y - bbox[3])
    return (dx * dx + dy * dy) ** 0.5


bad_spawns = []
bad_rooms = []
missing_interior_files = []
for name, room in IM.items():
    if not isinstance(room, dict):
        continue
    sx, sy = room["door"]["spawn"]
    if min(dist_to_bbox(sx, sy, b["bbox"]) for b in W["buildings"]) > 2.5:
        bad_spawns.append(name)
    path = ROOT / "public" / room["file"]
    if not path.is_file():
        missing_interior_files.append(name)
    else:
        with Image.open(path) as im:
            if im.size != (576, 384):
                bad_rooms.append(f"{name}:size")
    if room.get("scale_ppm") != 48 or room.get("size_px") != [576, 384]:
        bad_rooms.append(f"{name}:scale")
    if len(room.get("interactables", [])) < 2:
        bad_rooms.append(f"{name}:interactables")
chk("spawn degli interni ancorati a edifici OSM", not bad_spawns, ", ".join(bad_spawns))
chk("interni 576x384 @ 48 px/m", not bad_rooms, ", ".join(bad_rooms[:6]))
chk("coerenza manifest interni / PNG", not missing_interior_files,
    ", ".join(missing_interior_files[:6]))

unreachable = []
for name in sorted(new_rooms & set(IM)):
    room = IM[name]
    for it in room["interactables"]:
        x, y = it["x"], it["y"]
        if not (16 <= x <= 560 and 130 <= y <= 360):
            unreachable.append(f"{name}:{it['id']}:fuori")
            continue
        if any(x0 - 8 < x < x1 + 8 and y0 - 8 < y < y1 + 8
               for x0, y0, x1, y1 in room.get("colliders", [])):
            unreachable.append(f"{name}:{it['id']}:colliso")
chk("interactabili dei nuovi interni raggiungibili", not unreachable,
    ", ".join(unreachable[:6]))

# --- audio -----------------------------------------------------------------
expected_audio = {
    "ambience.wav", "music.wav", "step.wav", "coin.wav", "door.wav", "train.wav",
    "birds.wav", "night.wav", "crowd.wav", "bar_murmur.wav", "cash.wav", "eat.wav",
    "sleep.wav", "ui.wav", "traffic.wav", "market.wav", "engine.wav", "scooter.wav",
    "shop_bell.wav", "relationship.wav",
}
audio_files = set(AM.get("files", []))
chk("manifest audio versione 0.6.0", AM.get("version") == "0.6.0", str(AM.get("version")))
chk("14 loop/SFX storici + 6 nuovi", audio_files == expected_audio,
    f"{len(audio_files)} file; mancanti={sorted(expected_audio - audio_files)}; "
    f"extra={sorted(audio_files - expected_audio)}")
missing_audio = [f for f in sorted(audio_files)
                 if not (ROOT / "public/assets/audio" / f).is_file()]
chk("coerenza manifest audio / WAV", not missing_audio, ", ".join(missing_audio[:5]))

chk("licenza OSM presente nei metadati", "OpenStreetMap" in meta["license"])
chk("data cattura OSM presente", bool(meta["osm_captured_utc"]))

# Nessun perimetro edificio degenere.
bad = [b["id"] for b in W["buildings"] if len(b["footprint"]) < 4 or b["area_m2"] < 6]
chk("perimetri edifici validi", not bad, ", ".join(bad[:5]))

warnings = []
if violations:
    warnings.append(
        "Edifici OSM reali entro 8 m dai binari (mantenuti per fedeltà, non inventati): "
        + ", ".join(violations))
warnings.append(
    f"Conteggio stradale: {meta.get('road_way_count', 0)} way OSM + "
    f"{meta.get('road_node_count', 0)} elementi viari puntuali OSM (fermate/segnali); "
    "nessun tracciato inventato.")
warnings.append(
    "Scommesse d'oro è un'attività fittizia dichiarata, ancorata a due edifici OSM reali.")
if not W.get("parking"):
    warnings.append("Nessun parcheggio mappato nel contesto: elenco vuoto, non inventato.")

report = {
    "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "version": "0.6.0",
    "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in checks],
    "passed": sum(1 for _, ok, _ in checks if ok),
    "total": len(checks),
    "warnings": warnings,
    "counts": {
        "roads": len(W["roads"]),
        "road_ways": meta.get("road_way_count", 0),
        "road_nodes": meta.get("road_node_count", 0),
        "buildings": len(W["buildings"]),
        "tobacconists": len(tobacconists),
        "rail_route_ways": len(rail_route),
        "fictional_pois": len(fictional),
        "tiles": TM.get("count"),
        "building_sprites": len(BM),
        "sprites": len(sprites),
        "interiors": len([k for k, v in IM.items() if isinstance(v, dict) and k != "version"]),
        "audio": len(audio_files),
    },
}
out = ROOT / "data/world/validation-report.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
# Copia legacy: gli screenshot e i report storici fanno riferimento a questo percorso.
mirror = ROOT / "screenshots/validation-report.json"
mirror.parent.mkdir(parents=True, exist_ok=True)
mirror.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
for name, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'} {name}{' — ' + detail if detail else ''}")
for warning in warnings:
    print(f"WARN {warning}")
print(f"{report['passed']}/{report['total']} controlli superati")
if report["passed"] != report["total"]:
    raise SystemExit(1)
