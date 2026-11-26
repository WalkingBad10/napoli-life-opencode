#!/usr/bin/env python3
"""Controllo visivo automatico della v0.5.0 su asset generati e screenshot reali.

Non sostituisce la visione umana, ma intercetta i difetti che hanno reso inaccettabile
la 0.2.0: immagini vuote, ombre nere dominanti, perdita di palette, linee troppo
spesse e asset fuori dalla metrica 1 m = 16 px. La 0.5.0 verifica anche i nuovi
asset di vita quotidiana (pizzeria, pizza, caffè, arredi, audio e bisogni nell'HUD).
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "screenshots"
checks: list[dict] = []


def chk(name: str, ok: bool, detail: str = "") -> None:
    checks.append({"name": name, "ok": bool(ok), "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'} {name}{' — ' + detail if detail else ''}")


def sample_stats(path: Path, stride: int = 12) -> dict:
    with Image.open(path) as im:
        img = im.convert("RGB")
        w, h = img.size
        px = img.load()
        colors: set[int] = set()
        black = 0
        dark = 0
        luma = 0.0
        n = 0
        for y in range(0, h, stride):
            for x in range(0, w, stride):
                r, g, b = px[x, y]
                colors.add((r << 16) | (g << 8) | b)
                if r < 8 and g < 8 and b < 8:
                    black += 1
                if 0.2126 * r + 0.7152 * g + 0.0722 * b < 36:
                    dark += 1
                luma += 0.2126 * r + 0.7152 * g + 0.0722 * b
                n += 1
        edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
        ep = edges.load()
        edge_hits = sum(1 for y in range(0, h, stride) for x in range(0, w, stride) if ep[x, y] > 42)
        return {
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "w": w, "h": h,
            "colors": len(colors),
            "black_ratio": round(black / max(1, n), 5),
            "dark_ratio": round(dark / max(1, n), 5),
            "luma": round(luma / max(1, n), 1),
            "edge_ratio": round(edge_hits / max(1, n), 4),
        }


# --- Screenshot reali della build (il link pubblico viene aggiunto dopo la pubblicazione) ---
shots = sorted(p for p in SHOTS.glob("v0.5_*.png") if not p.name.endswith("_public_link.png"))
chk("screenshot v0.5 presenti", len(shots) >= 8, f"{len(shots)} file")
shot_stats = []
for path in shots:
    s = sample_stats(path)
    shot_stats.append(s)
    chk(f"screenshot non vuoto: {s['file']}", s["colors"] > 100, f"{s['colors']} colori")
    chk(f"ombre nere controllate: {s['file']}", s["black_ratio"] < 0.03,
        f"{s['black_ratio'] * 100:.2f}%")
    chk(f"dettaglio pixel presente: {s['file']}", s["edge_ratio"] > 0.008,
        f"{s['edge_ratio'] * 100:.1f}% bordi")

# --- Manifest e asset generati ---
bm = json.loads((ROOT / "public/assets/buildings/manifest.json").read_text(encoding="utf-8"))
tm = json.loads((ROOT / "public/assets/tiles/manifest.json").read_text(encoding="utf-8"))
sm = json.loads((ROOT / "public/assets/sprites/manifest.json").read_text(encoding="utf-8"))
im = json.loads((ROOT / "public/assets/interiors/manifest.json").read_text(encoding="utf-8"))
am = json.loads((ROOT / "public/assets/audio/manifest.json").read_text(encoding="utf-8"))

chk("suolo engine_scale=1", tm.get("engine_scale") == 1, str(tm.get("engine_scale")))
chk("origini edifici valide", all(0 <= b["origin_x"] <= 1 and 0 <= b["origin_y"] <= 1 for b in bm))
station = next((b for b in bm if b["id"] == "way/503291719"), None)
chk("stazione ampia e ricostruita", bool(station) and station["width_px"] >= 900,
    str(station["width_px"]) if station else "assente")
chk("personaggi 16x32 px", sm.get("frame_w") == 16 and sm.get("frame_h") == 32)
chk("manifest sprite versione 0.5.0", sm.get("version") == "0.5.0", str(sm.get("version")))
required_building_fields = {"origin_x", "origin_y", "wall_h_px", "width_px", "depth_px", "windows"}
missing_fields = [b.get("id", "?") for b in bm if not required_building_fields <= set(b)]
chk("metadati architettonici in tutti gli edifici", not missing_fields, ",".join(missing_fields[:5]))
window_count = sum(len(b.get("windows", [])) for b in bm)
chk("finestre reali per luci notturne", window_count > 500, f"{window_count} finestre")
chk("stazione a due piani senza pensilina", bool(station) and station.get("wall_h_px") == 92,
    str(station.get("wall_h_px")) if station else "assente")

# Nuovi sprite v0.5: dimensioni e presenza file.
expected_sprites = {
    "pizzaiolo": (64, 128), "pizza": (24, 20), "coffee_cup": (12, 14),
    "bookshelf": (48, 64), "plant": (24, 48),
}
sprite_dir = ROOT / "public/assets/sprites"
for name, (w, h) in expected_sprites.items():
    path = sprite_dir / f"{name}.png"
    exists = path.exists() and name in sm.get("sprites", {})
    size_ok = exists and Image.open(path).size == (w, h)
    chk(f"sprite v0.5 {name} {w}x{h}", size_ok,
        str(Image.open(path).size) if path.exists() else "file assente")
chk("26 sprite storici preservati", all(k in sm.get("sprites", {}) for k in [
    "player", "resident", "worker", "elderly", "teen", "railway", "vendor",
    "car_red", "car_silver", "bus", "scooter", "train_eav", "lamp", "bin", "bench",
    "tree", "planter", "sign", "traffic_light", "ticket_machine", "dog", "cat",
    "parcel", "keys", "coffee", "ticket"]))

# Interni: quattro stanze storiche invariate più la pizzeria OSM.
chk("cinque interni presenti", all((ROOT / f"public/assets/interiors/{n}.png").exists()
    for n in ["station", "bar", "shop", "home", "pizzeria"]))
chk("porte storiche invariate", all(k in im for k in ["station", "bar", "shop", "home"]))
pizzeria = im.get("pizzeria", {})
chk("pizzeria Carpe Diem ancorata a OSM", pizzeria.get("door", {}).get("spawn") == [-126.3, 123.9],
    str(pizzeria.get("door", {}).get("spawn")))
piz_kinds = {it.get("kind") for it in pizzeria.get("interactables", [])}
chk("pizzeria interattiva", {"exit", "pizzaiolo", "buy_pizza", "read"} <= piz_kinds,
    ", ".join(sorted(piz_kinds)))
chk("armadio in casa", any(it.get("kind") == "furnish" for it in im.get("home", {}).get("interactables", [])))

# Audio ambientale: loop e SFX originali.
audio_dir = ROOT / "public/assets/audio"
expected_audio = ["ambience", "music", "step", "coin", "door", "train",
                  "birds", "night", "crowd", "bar_murmur", "cash", "eat", "sleep", "ui"]
missing_audio = [n for n in expected_audio if not (audio_dir / f"{n}.wav").exists()]
chk("14 file audio originali", not missing_audio, ",".join(missing_audio))
chk("manifest audio versione 0.5.0", str(am.get("version")) == "0.5.0", str(am.get("version")))

# Dati OSM convertiti: nessuna API a runtime, POI reali e campo opening_hours esportato.
world = json.loads((ROOT / "data/world/pianura_world.json").read_text(encoding="utf-8"))
chk("metrica mondo 16 px/m", world.get("meta", {}).get("pixels_per_meter") == 16)
carpe = next((p for p in world.get("pois", []) if p.get("id") == "way/655446533"), None)
chk("Carpe Diem nei POI OSM", bool(carpe) and carpe.get("name") == "Carpe Diem")
chk("opening_hours campo presente", all("opening_hours" in p for p in world.get("pois", [])))

tile_dir = ROOT / "public/assets/tiles"
black_tiles = []
for path in tile_dir.glob("sector_*.png"):
    with Image.open(path) as im_file:
        if im_file.size != (1024, 1024):
            black_tiles.append(path.name)
        # Campione grosso: una ombra dura coprirebbe migliaia di pixel neri.
        px = im_file.convert("RGB").load()
        hits = sum(1 for y in range(0, 1024, 32) for x in range(0, 1024, 32)
                   if px[x, y][0] < 8 and px[x, y][1] < 8 and px[x, y][2] < 8)
        if hits > 0:
            black_tiles.append(path.name)
chk("36 settori senza ombre nere dure", not black_tiles and len(list(tile_dir.glob("sector_*.png"))) == 36,
    ", ".join(black_tiles[:5]))

report = {
    "generated_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    "method": "analisi programmatica di screenshot reali e asset generati (non sostituisce revisione umana)",
    "checks": checks,
    "screenshots": shot_stats,
    "passed": sum(1 for c in checks if c["ok"]),
    "total": len(checks),
}
out = SHOTS / "visual-qa-report.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{report['passed']}/{report['total']} controlli visivi superati — report: {out}")
if report["passed"] != report["total"]:
    raise SystemExit(1)
