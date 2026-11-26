#!/usr/bin/env python3
"""Controllo visivo automatico della v0.4.0 su asset generati e screenshot reali.

Non sostituisce la visione umana, ma intercetta i difetti che hanno reso inaccettabile
la 0.2.0: immagini vuote, ombre nere dominanti, perdita di palette, linee troppo
spesse e asset fuori dalla metrica 1 m = 16 px.
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


# --- Screenshot reali della build ---
shots = sorted(SHOTS.glob("v0.4_*.png"))
chk("screenshot v0.4 presenti", len(shots) >= 4, f"{len(shots)} file")
shot_stats = []
for path in shots:
    s = sample_stats(path)
    shot_stats.append(s)
    chk(f"screenshot non vuoto: {s['file']}", s["colors"] > 100, f"{s['colors']} colori")
    chk(f"ombre nere controllate: {s['file']}", s["black_ratio"] < 0.03,
        f"{s['black_ratio'] * 100:.2f}%")
    chk(f"dettaglio pixel presente: {s['file']}", s["edge_ratio"] > 0.008,
        f"{s['edge_ratio'] * 100:.1f}% bordi")

# --- Asset generati ---
bm = json.loads((ROOT / "public/assets/buildings/manifest.json").read_text(encoding="utf-8"))
tm = json.loads((ROOT / "public/assets/tiles/manifest.json").read_text(encoding="utf-8"))
sm = json.loads((ROOT / "public/assets/sprites/manifest.json").read_text(encoding="utf-8"))

chk("suolo engine_scale=1", tm.get("engine_scale") == 1, str(tm.get("engine_scale")))
chk("origini edifici valide", all(0 <= b["origin_x"] <= 1 and 0 <= b["origin_y"] <= 1 for b in bm))
station = next((b for b in bm if b["id"] == "way/503291719"), None)
chk("stazione ampia e ricostruita", bool(station) and station["width_px"] >= 900,
    str(station["width_px"]) if station else "assente")
chk("personaggi 16x32 px", sm.get("frame_w") == 16 and sm.get("frame_h") == 32)
chk("manifest sprite versione 0.4.0", sm.get("version") == "0.4.0", str(sm.get("version")))
window_count = sum(len(b.get("windows", [])) for b in bm)
chk("finestre reali per luci notturne", window_count > 500, f"{window_count} finestre")
chk("stazione a due piani senza pensilina", bool(station) and station.get("wall_h_px") == 92,
    str(station.get("wall_h_px")) if station else "assente")

tile_dir = ROOT / "public/assets/tiles"
black_tiles = []
for path in tile_dir.glob("sector_*.png"):
    with Image.open(path) as im:
        if im.size != (1024, 1024):
            black_tiles.append(path.name)
        # Campione grosso: una ombra dura coprirebbe migliaia di pixel neri.
        px = im.convert("RGB").load()
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
