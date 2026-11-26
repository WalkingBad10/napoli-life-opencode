#!/usr/bin/env python3
"""Genera i settori del suolo in pixel art dal mondo OSM convertito.

Ogni settore copre 64 x 64 metri e viene disegnato a 8 px/m (512 x 512 px);
il motore lo scala 2x con filtro nearest-neighbor mantenendo 16 px/m globali.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw
from artlib import P, noise, rgba, save_png, seeded

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/assets/tiles"
W = json.loads((ROOT / "data/world/pianura_world.json").read_text(encoding="utf-8"))
PPM = 8
SECTOR_M = 64
SECTOR_PX = SECTOR_M * PPM
ORIGINS = range(-192, 192, SECTOR_M)


def to_local(pt, ox, oy):
    return ((pt[0] - ox) * PPM, (pt[1] - oy) * PPM)


def bbox_of(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def affected(points, pad_m=3):
    x0, y0, x1, y1 = bbox_of(points)
    out = []
    for ox in ORIGINS:
        for oy in ORIGINS:
            if ox <= x1 + pad_m and ox + SECTOR_M >= x0 - pad_m and oy <= y1 + pad_m and oy + SECTOR_M >= y0 - pad_m:
                out.append((ox, oy))
    return out


def seg_points(a, b, step_m):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 0.001:
        return []
    n = max(1, int(length / step_m))
    return [(a[0] + dx * i / n, a[1] + dy * i / n) for i in range(n + 1)]


def draw_sector(ox, oy):
    rng = seeded(f"ground:{ox}:{oy}")
    img = Image.new("RGB", (SECTOR_PX, SECTOR_PX), "#c8bfab")
    noise(img, rng, amount=9, step=2)
    d = ImageDraw.Draw(img, "RGBA")

    # Superfici verdi / cortili
    for lc in W["landcover"]:
        pts = lc["footprint"]
        if len(pts) < 3:
            continue
        color = {"grass": "#7c995f", "meadow": "#7c995f", "forest": "#5c7b49",
                 "recreation_ground": "#88a36a", "cemetery": "#93a178"}.get(lc["kind"], "#b9b5a6")
        for sx, sy in affected(pts):
            d.polygon([to_local(p, sx, sy) for p in pts], fill=color)
            dd = ImageDraw.Draw(img, "RGBA")
            target = tuple(bytes.fromhex(color[1:]))
            for _ in range(120):
                px = rng.randrange(SECTOR_PX)
                py = rng.randrange(SECTOR_PX)
                if img.getpixel((px, py))[:3] == target:
                    dd.point((px, py), fill=rgba(P["green_light"], 150))

    # Parcheggi (dati OSM reali)
    for park in W["parking"]:
        pts = park["footprint"]
        if len(pts) < 3:
            continue
        for sx, sy in affected(pts):
            d.polygon([to_local(p, sx, sy) for p in pts], fill=P["asphalt"])
            x0, y0, x1, y1 = bbox_of([to_local(p, sx, sy) for p in pts])
            for yy in range(int(y0) + 8, int(y1) - 4, 14):
                for xx in range(int(x0) + 6, int(x1) - 6, 20):
                    d.line((xx, yy, xx + 15, yy), fill=rgba(P["white"], 120), width=1)

    # Strade: marciapiedi, cordoli, asfalto
    for road in W["roads"]:
        pts = road["points"]
        if len(pts) < 2:
            continue
        kind = road["kind"]
        width_px = max(5, road["width_m"] * PPM)
        if kind in ("footway", "path", "steps", "crossing", "cycleway", "track"):
            base = None
            color = "#cabfa9" if kind != "steps" else "#9b9485"
            for sx, sy in affected(pts, pad_m=2):
                local = [to_local(p, sx, sy) for p in pts]
                d.line(local, fill=rgba(color, 235), width=int(width_px), joint="curve")
                if kind == "steps":
                    for i in range(0, len(local) - 1):
                        a, b = local[i], local[i + 1]
                        dx, dy = b[0] - a[0], b[1] - a[1]
                        n = max(1, int(math.hypot(dx, dy) / 4))
                        for j in range(n):
                            t = j / n
                            x, y = a[0] + dx * t, a[1] + dy * t
                            d.line((x - 4, y - 4, x + 4, y + 4), fill=rgba(P["ink"], 90), width=1)
            continue
        for sx, sy in affected(pts, pad_m=5):
            local = [to_local(p, sx, sy) for p in pts]
            d.line(local, fill=rgba(P["curb"], 255), width=int(width_px + 16), joint="curve")
            d.line(local, fill=rgba(P["concrete"], 255), width=int(width_px + 10), joint="curve")
            d.line(local, fill=rgba(P["asphalt"], 255), width=int(width_px), joint="curve")
            d.line(local, fill=rgba(P["asphalt_light"], 45), width=max(2, int(width_px * 0.32)), joint="curve")
            # giunti del marciapiede
            for i in range(len(local) - 1):
                a, b = local[i], local[i + 1]
                dx, dy = b[0] - a[0], b[1] - a[1]
                n = max(1, int(math.hypot(dx, dy) / 12))
                for j in range(1, n):
                    t = j / n
                    x, y = a[0] + dx * t, a[1] + dy * t
                    nx, ny = -dy, dx
                    ln = math.hypot(nx, ny) or 1
                    nx, ny = nx / ln, ny / ln
                    r = width_px / 2 + 5
                    d.line((x - nx * r, y - ny * r, x + nx * r, y + ny * r),
                           fill=rgba(P["ink"], 35), width=1)
            # strisce pedonali reali (highway=crossing)
            if kind == "crossing":
                for i in range(len(local) - 1):
                    a, b = local[i], local[i + 1]
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    ln = math.hypot(dx, dy) or 1
                    tx, ty = dx / ln, dy / ln
                    nx, ny = -ty, tx
                    for k in range(4):
                        cx = a[0] + dx * (0.2 + k * 0.2)
                        cy = a[1] + dy * (0.2 + k * 0.2)
                        d.line((cx - nx * 8, cy - ny * 8, cx + nx * 8, cy + ny * 8),
                               fill=rgba(P["white"], 220), width=3)

    # Sedime ferroviario, traverse, rotaie
    for rail in W["rails"]:
        pts = rail["points"]
        if len(pts) < 2:
            continue
        for sx, sy in affected(pts, pad_m=6):
            local = [to_local(p, sx, sy) for p in pts]
            d.line(local, fill=rgba("#8b8577", 255), width=int(7.2 * PPM), joint="curve")
            d.line(local, fill=rgba("#9d9687", 120), width=int(6 * PPM), joint="curve")
            for i in range(len(local) - 1):
                a, b = local[i], local[i + 1]
                dx, dy = b[0] - a[0], b[1] - a[1]
                ln = math.hypot(dx, dy) or 1
                nx, ny = -dy / ln, dx / ln
                tx, ty = dx / ln, dy / ln
                for t in seg_points((0, 0), (ln, 0), 0.75):
                    dist = t[0]
                    cx, cy = a[0] + tx * dist, a[1] + ty * dist
                    d.line((cx - nx * 24, cy - ny * 24, cx + nx * 24, cy + ny * 24),
                           fill=rgba(P["brown"], 210), width=3)
                for offset in (-9, 9):
                    d.line((a[0] + nx * offset, a[1] + ny * offset,
                            b[0] + nx * offset, b[1] + ny * offset),
                           fill=rgba("#404444", 255), width=3)
                    d.line((a[0] + nx * (offset - 1), a[1] + ny * (offset - 1),
                            b[0] + nx * (offset - 1), b[1] + ny * (offset - 1)),
                           fill=rgba(P["metal_light"], 180), width=1)

    # Banchine reali (OSM railway=platform)
    for platform in W["platforms"]:
        pts = platform["footprint"]
        for sx, sy in affected(pts, pad_m=2):
            local = [to_local(p, sx, sy) for p in pts]
            d.polygon(local, fill=rgba(P["concrete_light"], 255), outline=rgba(P["ink"], 120))
            for i in range(len(local)):
                a, b = local[i], local[(i + 1) % len(local)]
                d.line((a, b), fill=rgba(P["yellow"], 230), width=2)

    # Ombre degli edifici: ancoraggio visivo al suolo
    for b in W["buildings"]:
        pts = b["footprint"]
        for sx, sy in affected(pts, pad_m=4):
            local = [to_local(p, sx, sy) for p in pts]
            d.polygon([(x + 5, y + 5) for x, y in local], fill=rgba(P["shadow"], 150))
            d.polygon(local, outline=rgba(P["ink"], 90))

    # Recinzioni ferroviarie reali
    for barrier in W["barriers"]:
        pts = barrier["points"]
        for sx, sy in affected(pts, pad_m=2):
            local = [to_local(p, sx, sy) for p in pts]
            d.line(local, fill=rgba(P["metal"], 200), width=2)
            for i in range(len(local) - 1):
                a, b = local[i], local[i + 1]
                for t in seg_points(a, b, 1.5):
                    d.rectangle((t[0] - 1, t[1] - 1, t[0] + 1, t[1] + 1), fill=rgba(P["ink"], 180))

    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for ox in ORIGINS:
        for oy in ORIGINS:
            img = draw_sector(ox, oy)
            save_png(img, OUT / f"sector_{ox}_{oy}.png")
            count += 1
    manifest = {
        "sector_m": SECTOR_M, "source_ppm": PPM, "engine_ppm": 16,
        "engine_scale": 2, "origins": list(ORIGINS), "count": count,
        "naming": "sector_{x}_{y}.png where x,y are metres (origin top-left of sector)",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"OK {count} settori suolo")


if __name__ == "__main__":
    main()
