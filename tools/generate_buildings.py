#!/usr/bin/env python3
"""Genera sprite architettonici originali, uno per ogni perimetro edificio OSM.

Lo stile è pixel art 2D a tre quarti: facciate proporzionate ai livelli,
tetti in tegole, balconi, persiane, condizionatori, antenne e panni stesi.
Il fabbricato viaggiatori riceve un trattamento dedicato (insegne EAV, vetrate,
colonne e pensilina).
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from artlib import P, ellipse, line, rect, rgba, save_png, seeded, shade

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/assets/buildings"
W = json.loads((ROOT / "data/world/pianura_world.json").read_text(encoding="utf-8"))
PPM = 16

STUCCOS = [P["stucco_cream"], P["stucco_ochre"], P["stucco_pink"],
           P["stucco_yellow"], P["stucco_green"], P["stucco_blue"]]
try:
    FONT = ImageFont.load_default()
except Exception:  # pragma: no cover
    FONT = None


def pedina(poly):
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    return cx, cy


def draw_window(d, x, y, rng, level, balcony=False, shutter_color=None):
    """Finestra 12x18 px con persiane, vetro e davanzale."""
    sc = shutter_color or P["wood"]
    rect(d, x - 2, y - 1, x + 14, y + 19, shade(sc, 0.75))
    rect(d, x - 1, y, x + 13, y + 18, shade(sc, 1.06))
    rect(d, x + 1, y + 2, x + 11, y + 16, P["glass"])
    rect(d, x + 1, y + 2, x + 6, y + 8, rgba(P["glass_light"], 190))
    rect(d, x + 5, y + 2, x + 6, y + 16, shade(P["ink"], 1.4))
    rect(d, x - 3, y + 19, x + 15, y + 21, P["concrete_light"])
    if balcony:
        rect(d, x - 7, y + 21, x + 19, y + 24, shade(P["concrete"], 0.9))
        for xx in range(x - 6, x + 19, 4):
            rect(d, xx, y + 12, xx + 1, y + 22, P["ink_soft"])
        rect(d, x - 7, y + 11, x + 19, y + 13, P["ink_soft"])
        if rng.random() < 0.42:  # panni stesi
            cloth = rng.choice([P["white"], P["red"], P["eav_light"], P["yellow"]])
            rect(d, x - 5, y + 13, x - 1, y + 18, cloth)
            rect(d, x + 3, y + 14, x + 8, y + 19, cloth)


def draw_facade_details(d, a, b, height_px, height_m, rng, style, levels, name):
    """Dettagli su un lato rivolto a sud: porte, finestre, balconi, negozi."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy)
    if ln < 28:
        return
    tx, ty = dx / ln, dy / ln
    nx, ny = -ty, tx

    def along(t, depth):
        return (a[0] + tx * t + nx * depth, a[1] + ty * t + ny * depth)

    step = 2.45 * PPM
    count = max(1, int(ln / step))
    for level in range(levels):
        base_y = -(height_px - level * 2.85 * PPM)
        for i in range(count):
            t = (i + 0.5) * ln / count
            cx, cy = along(t, 0)
            x, y = int(cx - 6), int(cy + base_y)
            if style == "station":
                if level == 0:
                    rect(d, x - 8, y - 2, x + 20, y + 24, P["white"])
                    rect(d, x - 7, y - 1, x + 19, y + 23, P["glass"])
                    rect(d, x, y - 1, x + 2, y + 23, P["eav_blue"])
                    rect(d, x + 11, y - 1, x + 13, y + 23, P["eav_blue"])
                    rect(d, x + 2, y + 8, x + 11, y + 10, P["glass_light"])
            elif style == "retail" and level == 0:
                rect(d, x - 10, y + 2, x + 22, y + 24, P["metal"])
                for k in range(-8, 22, 4):
                    rect(d, x + k, y + 3, x + k + 1, y + 23, rgba(P["ink"], 120))
                rect(d, x - 10, y - 4, x + 22, y + 2, rng.choice([P["eav_blue"], P["red"], P["green_dark"]]))
            else:
                draw_window(d, x, y, rng, level,
                            balcony=(level > 0 and rng.random() < 0.62),
                            shutter_color=rng.choice([P["wood"], P["stucco_cream"], P["stucco_green"]]))

    # Porta d'ingresso / androne
    if style != "station" and ln > 40:
        t = ln * 0.5
        cx, cy = along(t, 0)
        x, y = int(cx - 8), int(cy - height_px + (levels - 1) * 2.85 * PPM)
        rect(d, x - 2, y + 2, x + 18, y + 44, shade(P["ink"], 1.5))
        rect(d, x, y + 4, x + 16, y + 42, rng.choice([P["brown"], P["ink_soft"], P["eav_blue"]]))
        rect(d, x + 1, y + 5, x + 7, y + 24, rgba(P["glass_light"], 130))
        rect(d, x + 12, y + 25, x + 13, y + 27, P["yellow"])  # citofono
        rect(d, x + 6, y + 44, x + 10, y + 45, P["concrete_light"])

    # Condizionatori e antenne tv
    if style not in ("station",) and rng.random() < 0.8:
        for _ in range(min(3, levels)):
            t = rng.uniform(0.15, 0.85) * ln
            cx, cy = along(t, 0)
            lvl = rng.randrange(levels)
            yy = int(cy - height_px + lvl * 2.85 * PPM + 30)
            rect(d, int(cx) - 5, yy, int(cx) + 6, yy + 8, P["concrete_light"])
            rect(d, int(cx) - 3, yy + 2, int(cx) + 4, yy + 6, P["metal"])
    if style == "residential" and rng.random() < 0.55:
        t = rng.uniform(0.2, 0.8) * ln
        cx, cy = along(t, 0)
        top = int(cy - height_px - 22)
        line(d, [(cx, int(cy - height_px)), (cx, top)], P["metal_light"], 1)
        line(d, [(cx - 6, top + 6), (cx + 6, top + 3)], P["metal_light"], 1)
        line(d, [(cx - 6, top + 3), (cx + 6, top + 6)], P["metal_light"], 1)


def make_building(b):
    bid = b["id"].replace("/", "_")
    rng = seeded("building:" + b["id"])
    fp = b["footprint"]
    xs = [p[0] for p in fp]
    ys = [p[1] for p in fp]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    kind = b["kind"]
    if kind == "train_station":
        style, height_m = "station", 3.6
    elif kind in ("retail", "commercial", "shops"):
        style, height_m = "retail", 3.0 * (b["levels"] or 2)
    elif kind in ("industrial", "warehouse", "shed"):
        style, height_m = "industrial", 4.2
    elif kind in ("roof", "yes"):
        style, height_m = "residential", 2.85 * (b["levels"] or 3)
    else:
        style, height_m = "residential", 2.85 * (b["levels"] or 3)
    height_m = min(height_m, 18)
    hpx = int(height_m * PPM)
    pad_x = 48
    pad_top = hpx + 40
    pad_bottom = 22
    w = int((maxx - minx) * PPM) + pad_x * 2
    h = int((maxy - miny) * PPM) + pad_top + pad_bottom
    img = Image.new("RGBA", (max(w, 32), max(h, 48)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    local = [(int((p[0] - minx) * PPM + pad_x), int((p[1] - miny) * PPM + pad_top)) for p in fp]
    cx, cy = pedina(local)

    wall = P["stucco_cream"] if style == "station" else rng.choice(STUCCOS)
    roof_color = P["roof_grey"] if style == "station" else (P["terra"] if rng.random() < 0.7 else P["roof_grey"])

    # Facciate: lati con normale verso sud (il gioco è visto da sud-est)
    for i in range(len(local)):
        a, bpt = local[i], local[(i + 1) % len(local)]
        mx, my = (a[0] + bpt[0]) / 2, (a[1] + bpt[1]) / 2
        nx, ny = mx - cx, my - cy
        nlen = math.hypot(nx, ny) or 1
        nx, ny = nx / nlen, ny / nlen
        if ny > -0.12:
            shade_f = 0.92 + 0.16 * nx
            poly = [a, bpt, (bpt[0], bpt[1] - hpx), (a[0], a[1] - hpx)]
            d.polygon(poly, fill=rgba(shade(wall, shade_f), 255))
            d.line(poly + [poly[0]], fill=rgba(P["ink"], 130), width=1)
            if ny > 0.25:
                draw_facade_details(d, a, bpt, hpx, height_m, rng, style,
                                    max(1, round(height_m / 2.85)) if style != "station" else 1,
                                    b.get("name", ""))

    # Tetto con tegole e merlatura
    roof = [(x, y - hpx) for x, y in local]
    d.polygon(roof, fill=rgba(shade(roof_color, 1.05), 255))
    d.polygon(roof, outline=rgba(P["ink"], 170))
    x0, y0 = min(p[0] for p in roof), min(p[1] for p in roof)
    x1, y1 = max(p[0] for p in roof), max(p[1] for p in roof)
    if style != "station":
        for yy in range(int(y0) + 4, int(y1), 6):
            d.line((x0, yy, x1, yy - 2), fill=rgba(P["ink"], 40), width=1)
        for xx in range(int(x0) + 4, int(x1), 8):
            d.line((xx, y0, xx + 3, y1), fill=rgba(P["white"], 25), width=1)
    else:
        rect(d, x0 + 8, y0 + 8, x1 - 8, y1 - 8, rgba(P["metal"], 90))
        for k in range(4):
            xx = x0 + 30 + k * (x1 - x0) / 5
            rect(d, int(xx), int(y0 + 12), int(xx + 20), int(y0 + 30), P["metal_light"])

    # Insegna EAV sul fabbricato viaggiatori
    if style == "station":
        sx = int((x0 + x1) / 2 - 62)
        sy = int(y0 + (y1 - y0) * 0.55)
        rect(d, sx - 6, sy - 4, sx + 130, sy + 30, P["ink"])
        rect(d, sx - 4, sy - 2, sx + 128, sy + 28, P["eav_blue"])
        if FONT:
            d.text((sx + 6, sy + 2), "EAV", fill=P["white"], font=FONT)
            d.text((sx + 48, sy + 2), "Pianura", fill=P["white"], font=FONT)
        # pensilina lato binari
        rect(d, x0 + 10, int(y1 + 4), x1 - 10, int(y1 + 10), rgba(P["metal_light"], 230))
        for xx in range(int(x0 + 20), int(x1 - 10), 55):
            rect(d, xx, int(y1 + 10), xx + 3, int(y1 + 26), P["metal"])

    # Fioriere / cassonetti presso gli ingressi
    if style in ("residential", "retail") and rng.random() < 0.6:
        fx = int(cx + rng.uniform(-40, 40))
        fy = int(maxy * PPM + pad_top + 4)
        rect(d, fx - 7, fy, fx + 7, fy + 9, P["brown"])
        for k in range(-5, 6, 3):
            ellipse(d, fx + k - 1, fy - 5, fx + k + 3, fy, P["green"])

    anchor_x = minx + (maxx - minx) / 2
    anchor_y = maxy
    fname = f"b_{re.sub(r'[^a-zA-Z0-9_]', '_', bid)}.png"
    save_png(img, OUT / fname)
    return {
        "id": b["id"], "name": b.get("name", ""), "kind": b["kind"],
        "sprite": f"assets/buildings/{fname}", "anchor_x": round(anchor_x, 3),
        "anchor_y": round(anchor_y, 3), "w": img.width, "h": img.height,
        "height_m": round(height_m, 2), "style": style,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = [make_building(b) for b in W["buildings"]]
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.glob("*.png"))
    print(f"OK {len(manifest)} edifici, {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
