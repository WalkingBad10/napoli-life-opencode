#!/usr/bin/env python3
"""Genera edifici in pixel art originale con proiezione obliqua a tre quarti.

La geometria deriva ESCLUSIVAMENTE dal bbox del perimetro OSM salvato in
``data/world/pianura_world.json``: larghezza = (maxx-minx)*16 px, profondità =
(maxy-miny)*8 px (asse di profondità a 45 gradi, scala 0,5). Non si dipinge mai
il footprint piatto come facciata: si costruiscono parete sud rettangolare,
parete est parallelogramma e tetto architettonico.

Regole vincolanti: docs/ART_SPEC.md (1 m = 16 px, finestre 12x16 con passo
38x46 px, porta 22x38 al livello strada, ombra di contatto morbida).
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
WORLD = json.loads((ROOT / "data/world/pianura_world.json").read_text(encoding="utf-8"))

PPM = 16
DEPTH_PX_PER_M = 8          # 16 px/m * 0,5
FLOOR_PX = 46                # un piano
WIN_W, WIN_H = 12, 16        # finestra standard
STEP_X, STEP_Y = 38, 46      # griglia regolare
DOOR_W, DOOR_H = 22, 38
OVERHANG = 2
SHADOW_R = 12                # 0,75 m <= 1 m
BOTTOM_PAD = 10
CANOPY_D = 40                # pensilina lato binari (stazione)

STUCCOS = [
    P["stucco_cream"], P["stucco_ochre"], P["stucco_pink"],
    P["stucco_yellow"], P["stucco_green"], P["stucco_blue"],
]
SHUTTERS = [P["wood"], P["green_dark"], P["stucco_cream"], P["brown"]]
DOORS = [P["wood"], P["brown"], P["eav_blue"], P["green_dark"]]

try:
    FONT = ImageFont.load_default()
except Exception:  # pragma: no cover - sandbox senza font
    FONT = None


class Painter:
    """Helper locale: converte coordinate architettoniche in pixel dell'immagine."""

    def __init__(self, img: Image.Image, ox: float, oy: float):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")
        self.ox = ox
        self.oy = oy

    def pt(self, x: float, y: float) -> tuple[int, int]:
        return (int(round(self.ox + x)), int(round(self.oy + y)))

    def box(self, x0: float, y0: float, x1: float, y1: float,
            fill, outline=None, width: int = 1) -> None:
        rect(self.d, *self.pt(x0, y0), *self.pt(x1, y1), fill, outline, width)

    def poly(self, pts, fill, outline=None) -> None:
        self.d.polygon([self.pt(x, y) for x, y in pts], fill=fill, outline=outline)

    def seg(self, pts, fill, width: int = 1) -> None:
        line(self.d, [self.pt(x, y) for x, y in pts], fill, width)

    def oval(self, x0: float, y0: float, x1: float, y1: float, fill) -> None:
        ellipse(self.d, *self.pt(x0, y0), *self.pt(x1, y1), fill)

    def text(self, xy, txt: str, fill) -> None:
        if FONT is not None:
            self.d.text(self.pt(*xy), txt, fill=fill, font=FONT)


def grid_positions(width_px: int) -> list[int]:
    """Top-left x delle finestre: passo esatto 38 px, griglia centrata."""
    n = max(1, int(width_px // STEP_X))
    while n > 1 and (n - 1) * STEP_X > width_px - 12:
        n -= 1
    start = (width_px - (n - 1) * STEP_X - WIN_W) / 2
    return [int(round(start + i * STEP_X)) for i in range(n)]


def draw_window(p: Painter, x: int, y: int, wall, shutter,
                variant: str = "home", balcony: bool = False) -> None:
    """Finestra 12x16 px, incassata, con persiane e davanzale.

    variant: 'home' (persiane), 'retail' (vetrina), 'station' (vetrata EAV).
    """
    p.box(x - 2, y - 1, x + 13, y + 16, rgba(shade(wall, 0.60), 255))
    p.box(x - 1, y - 1, x + 12, y + 16, rgba(P["concrete_light"], 255))
    p.box(x, y, x + 11, y + 15, rgba(P["glass"], 255))
    p.box(x + 1, y + 1, x + 5, y + 7, rgba(P["glass_light"], 165))
    p.seg([(x + 5, y), (x + 5, y + 15)], rgba(P["ink"], 150))
    p.seg([(x, y + 7), (x + 11, y + 7)], rgba(P["ink"], 150))

    if variant == "station":
        p.box(x - 3, y - 1, x - 1, y + 16, rgba(P["eav_blue"], 255))
        p.box(x + 12, y - 1, x + 14, y + 16, rgba(P["eav_blue"], 255))
        p.seg([(x, y + 15), (x + 11, y + 15)], rgba(P["white"], 150))
    elif variant == "retail":
        p.box(x - 3, y - 2, x + 14, y, rgba(P["eav_blue"], 255))
        p.box(x - 3, y + 13, x + 14, y + 16, rgba(P["metal"], 255))
    else:
        for sx in (x - 4, x + 12):
            p.box(sx, y - 1, sx + 2, y + 16, rgba(shade(shutter, 0.92), 255))
            for yy in range(y + 2, y + 16, 4):
                p.seg([(sx, yy), (sx + 2, yy)], rgba(P["ink"], 55))
        p.box(x - 3, y + 16, x + 14, y + 18, rgba(P["concrete_light"], 255))

    if balcony:
        # Solo ai piani superiori: lastra, ringhiera e montanti verticali.
        p.box(x - 6, y + 18, x + 18, y + 21, rgba(shade(P["concrete"], 0.92), 255))
        p.box(x - 6, y + 9, x + 18, y + 10, rgba(P["metal"], 255))
        for xx in range(x - 5, x + 18, 4):
            p.box(xx, y + 10, xx + 1, y + 18, rgba(P["ink_soft"], 255))


def draw_side_window(p: Painter, x: float, y: float, wall, shutter,
                     variant: str) -> None:
    """Finestra sulla parete est, parallelogrammo coerente con la proiezione."""
    frame = [(x - 1, y + 1), (x + 13, y - 11), (x + 13, y + 5), (x - 1, y + 17)]
    glass = [(x, y), (x + 12, y - 12), (x + 12, y + 4), (x, y + 16)]
    p.poly(frame, rgba(shade(wall, 0.55), 255))
    p.poly(glass, rgba(P["glass"], 255))
    p.seg([(x + 6, y - 6), (x + 6, y + 10)], rgba(P["ink"], 145))
    if variant == "home":
        p.seg([(x - 3, y + 1), (x - 3, y + 17)], rgba(shade(shutter, 0.9), 255))


def draw_door(p: Painter, x: int, wall, rng, style: str) -> None:
    """Porta centrale 22x38 px al livello strada, con gradino."""
    color = P["eav_blue"] if style == "station" else rng.choice(DOORS)
    p.box(x - 2, -DOOR_H - 2, x + DOOR_W + 2, 1, rgba(P["ink"], 215))
    p.box(x - 1, -DOOR_H - 1, x + DOOR_W + 1, 0,
          rgba(shade(P["concrete_light"], 1.02), 255))
    p.box(x, -DOOR_H, x + DOOR_W - 1, -1, rgba(color, 255))
    p.box(x + 2, -DOOR_H + 2, x + DOOR_W - 3, -20, rgba(P["glass"], 255))
    p.box(x + 3, -DOOR_H + 3, x + 7, -27, rgba(P["glass_light"], 150))
    p.seg([(x + DOOR_W // 2, -DOOR_H), (x + DOOR_W // 2, -1)], rgba(P["ink"], 120))
    p.box(x + DOOR_W - 5, -18, x + DOOR_W - 4, -17, rgba(P["yellow"], 255))
    p.box(x - 4, 0, x + DOOR_W + 4, 3, rgba(P["concrete_light"], 255))
    p.seg([(x - 4, 3), (x + DOOR_W + 4, 3)], rgba(shade(wall, 0.7), 255))


def contact_shadow(p: Painter, width_px: int) -> None:
    """Ombra di contatto a bande: raggio <= 1 m, alpha <= 45, senza sfalsamento."""
    for ww, hh, alpha in (
        (width_px + SHADOW_R * 2, 14, 10),
        (width_px + SHADOW_R, 10, 14),
        (width_px, 6, 16),
    ):
        p.oval(width_px / 2 - ww / 2, 2 - hh / 2,
               width_px / 2 + ww / 2, 2 + hh / 2, rgba(P["black"], alpha))


def draw_east_wall(p: Painter, w: int, h: int, depth: int, wall,
                   style: str, levels: int, rng) -> None:
    """Parete est: parallelogramma che arretra di depth px a destra e in alto."""
    p.poly([(w, 0), (w + depth, -depth), (w + depth, -h - depth), (w, -h)],
           rgba(shade(wall, 0.76), 255))
    p.poly([(w, 0), (w + depth, -depth), (w + depth, -depth - 3), (w, -3)],
           rgba(shade(wall, 0.65), 255))
    p.seg([(w, -h), (w + depth, -h - depth)], rgba(P["ink"], 120))

    for t in range(38, depth, 38):
        p.seg([(w + t, -t), (w + t, -h - t)], rgba(shade(wall, 0.70), 85))

    if depth >= 22:
        n = max(1, int(depth // STEP_X))
        shutter = rng.choice(SHUTTERS)
        variant = "station" if style == "station" else ("retail" if style == "retail" else "home")
        for lv in range(levels):
            for i in range(n):
                t = (i + 0.5) * depth / n
                if t + 12 > depth:
                    continue
                # Il piano terra è in basso: y = -34 - t; ogni piano sale di 46 px.
                y = (-34 if lv == 0 else -(lv + 1) * FLOOR_PX + 12) - t
                draw_side_window(p, w + t, y, wall, shutter, variant)


def draw_south_wall(p: Painter, w: int, h: int, wall, style: str,
                    levels: int, rng) -> None:
    p.box(0, -h, w, 0, rgba(wall, 255))
    for lv in range(1, levels):
        p.seg([(0, -lv * FLOOR_PX), (w, -lv * FLOOR_PX)],
              rgba(shade(wall, 0.79), 135))
    p.box(0, -4, w, 0, rgba(shade(wall, 0.82), 255))
    p.box(0, -h, w, -h + 3, rgba(shade(wall, 1.09), 255))
    p.box(0, -h, 2, 0, rgba(shade(wall, 1.05), 255))
    p.box(w - 2, -h, w, 0, rgba(shade(wall, 0.88), 255))
    for _ in range(min(90, w * h // 700)):
        x, y = rng.randrange(w), rng.randrange(-h, 0)
        p.box(x, y, x + 1, y + 1, rgba(shade(wall, 0.93), 35))

    variant = "station" if style == "station" else ("retail" if style == "retail" else "home")
    shutter = rng.choice(SHUTTERS)
    xs = grid_positions(w)

    # Fabbricato viaggiatori: colonne in intonaco tra le vetrate.
    if style == "station":
        for x in xs:
            cx = x - 6
            if abs(cx - w / 2) < 16:
                continue
            p.box(cx, -h + 3, cx + 2, 0, rgba(P["concrete_light"], 255))
            p.box(cx - 1, -h + 3, cx + 3, -h + 6, rgba(P["metal_light"], 255))

    # Piano terra in basso, a livello strada. La porta resta libera.
    ground_y = -28 if style == "station" else -34
    for idx, x in enumerate(xs):
        if abs(x + WIN_W / 2 - w / 2) < 20:
            continue
        draw_window(p, x, ground_y, wall, shutter, variant)

    # Piani superiori: passo verticale esatto 46 px dal piano terra.
    for lv in range(1, levels):
        y = -(lv + 1) * FLOOR_PX + 12
        for idx, x in enumerate(xs):
            if abs(x + WIN_W / 2 - w / 2) < 20:
                continue
            balcony = style != "station" and (idx % 2 == 0 or rng.random() < 0.25)
            draw_window(p, x, y, wall, shutter, "home", balcony)

    draw_door(p, w // 2 - DOOR_W // 2, wall, rng, style)


def draw_gable_end(p: Painter, w: int, h: int, depth: int,
                   rise: int, wall) -> None:
    p.poly([(w, -h), (w + depth, -h - depth),
            (w + depth / 2, -h - depth / 2 - rise)],
           rgba(shade(wall, 0.68), 255))
    p.seg([(w, -h), (w + depth, -h - depth)], rgba(P["ink"], 110))


def draw_gable_roof(p: Painter, w: int, h: int, depth: int, rise: int,
                    roof_color, antenna: bool) -> None:
    sl = (-OVERHANG, -h + OVERHANG)
    sr = (w + OVERHANG, -h + OVERHANG)
    nl = (depth - OVERHANG, -h - depth - OVERHANG)
    nr = (w + depth + OVERHANG, -h - depth - OVERHANG)
    rl = (depth / 2, -h - depth / 2 - rise - OVERHANG)
    rr = (w + depth / 2, -h - depth / 2 - rise - OVERHANG)

    p.poly([nl, nr, rr, rl], rgba(shade(roof_color, 0.86), 255),
           rgba(P["ink"], 150))
    p.poly([sl, sr, rr, rl], rgba(shade(roof_color, 1.04), 255),
           rgba(P["ink"], 150))

    # Tegole in file regolari, parallele al colmo; nessuna riga diagonale casuale.
    for eave, ridge_end, dark in ((sl, rl, 0.78), (nl, rl, 0.70)):
        steps = max(2, int((depth / 2 + rise) / 5))
        for k in range(1, steps):
            f = k / steps
            x0 = eave[0] + (ridge_end[0] - eave[0]) * f
            y0 = eave[1] + (ridge_end[1] - eave[1]) * f
            p.seg([(x0, y0), (x0 + w + 4, y0)], rgba(shade(roof_color, dark), 115))
            for xx in range(int(x0) + 5, int(x0 + w), 8):
                p.seg([(xx, y0), (xx + 2, y0 + 1)],
                      rgba(shade(roof_color, 1.17), 80))

    p.seg([rl, rr], rgba(P["ink"], 190), 3)
    p.seg([(rl[0], rl[1] - 1), (rr[0], rr[1] - 1)],
          rgba(shade(roof_color, 1.22), 255), 2)

    # Comignoli allineati al colmo.
    chimneys = [0.24, 0.72] if w > 150 else [0.66]
    for frac in chimneys:
        cx = int(w * frac + depth / 2)
        cy = int(-h - depth / 2 - rise - OVERHANG)
        p.box(cx - 4, cy - 14, cx + 4, cy + 2,
              rgba(shade(P["terra_dark"], 1.0), 255))
        p.box(cx - 5, cy - 16, cx + 5, cy - 13, rgba(P["terra_light"], 255))
        p.box(cx - 2, cy - 15, cx + 2, cy - 14, rgba(P["ink"], 180))

    if antenna:
        ax = int(w * 0.38 + depth / 2)
        ay = int(-h - depth / 2 - rise - OVERHANG)
        p.seg([(ax, ay), (ax, ay - 24)], rgba(P["metal_light"], 255))
        p.seg([(ax - 6, ay - 8), (ax + 6, ay - 11)], rgba(P["metal_light"], 255))
        p.seg([(ax - 6, ay - 13), (ax + 6, ay - 16)], rgba(P["metal_light"], 255))


def draw_flat_roof(p: Painter, w: int, h: int, depth: int,
                   roof_color, station: bool) -> None:
    p.poly([(-OVERHANG, -h + OVERHANG), (w + OVERHANG, -h + OVERHANG),
            (w + depth + OVERHANG, -h - depth - OVERHANG),
            (depth - OVERHANG, -h - depth - OVERHANG)],
           rgba(shade(roof_color, 1.10), 255), rgba(P["ink"], 155))
    for x in range(0, w, 16):
        p.seg([(x, -h + OVERHANG), (x + depth, -h - depth - OVERHANG)],
              rgba(P["ink"], 45))
    for t in range(16, depth, 16):
        p.seg([(t, -h - t), (w + t, -h - t)], rgba(P["ink"], 35))
    p.poly([(-OVERHANG, -h + OVERHANG), (w + OVERHANG, -h + OVERHANG),
            (w + OVERHANG, -h + OVERHANG + 3), (-OVERHANG, -h + OVERHANG + 3)],
           rgba(shade(roof_color, 0.72), 255))
    if not station:
        for frac in (0.20, 0.76):
            x = int(w * frac)
            p.box(x, -h - 10, x + 12, -h - 2, rgba(P["metal"], 255))
            p.box(x + 1, -h - 9, x + 11, -h - 4, rgba(P["metal_light"], 255))


def draw_canopy(p: Painter, w: int, h: int, depth: int) -> None:
    """Pensilina metallica lato binari (a nord), dietro il fabbricato."""
    attach = -h - depth + 6
    far = attach - CANOPY_D
    p.poly([(depth, attach), (w + depth, attach),
            (w + depth + CANOPY_D, far), (depth + CANOPY_D, far)],
           rgba(P["metal_light"], 255), rgba(P["ink"], 170))
    for x in range(depth + 16, w + depth, 24):
        p.seg([(x, attach), (x + CANOPY_D, far)], rgba(P["metal"], 110))
    p.poly([(depth + CANOPY_D, far), (w + depth + CANOPY_D, far),
            (w + depth + CANOPY_D, far + 3), (depth + CANOPY_D, far + 3)],
           rgba(P["metal"], 255))
    for x in range(depth + 20, w + depth + CANOPY_D, 64):
        p.box(x, far + 3, x + 3, far + 17, rgba(P["metal"], 255))
        p.box(x - 2, far + 16, x + 5, far + 18, rgba(P["concrete"], 255))


def draw_station_sign(p: Painter, w: int, h: int) -> None:
    sx = w // 2 - 60
    sy = -h + 2
    p.box(sx - 3, sy - 1, sx + 123, sy + 14, rgba(P["ink"], 235))
    p.box(sx - 1, sy + 1, sx + 121, sy + 12, rgba(P["eav_blue"], 255))
    p.box(sx + 2, sy + 3, sx + 12, sy + 10, rgba(P["white"], 255))
    p.text((sx + 15, sy + 2), "EAV  PIANURA", rgba(P["white"], 255))


def pick_style(kind: str, rng) -> str:
    if kind == "train_station":
        return "station"
    if kind in ("retail", "commercial", "shops"):
        return "retail"
    if kind in ("industrial", "warehouse", "shed"):
        return "industrial"
    if kind == "mausoleum":
        return "mausoleum"
    return "residential"


def pick_levels(style: str, rng) -> int:
    if style in ("station", "industrial", "mausoleum"):
        return 1
    if style == "retail":
        return rng.choice([2, 2, 3])
    return rng.choice([2, 2, 3, 3, 4])


def make_building(b: dict) -> dict:
    bid = b["id"]
    rng = seeded("building:" + bid)
    minx, miny, maxx, maxy = b["bbox"]
    width_m, depth_m = maxx - minx, maxy - miny

    width_px = max(16, int(round(width_m * PPM)))
    depth_px = max(2, int(round(depth_m * DEPTH_PX_PER_M)))
    style = pick_style(b["kind"], rng)
    levels = pick_levels(style, rng)
    wall_h_px = levels * FLOOR_PX
    height_m = round(wall_h_px / PPM, 2)

    wall = P["stucco_cream"] if style == "station" else rng.choice(STUCCOS)
    roof_color = P["roof_grey"] if style in ("station", "industrial") else (
        P["terra"] if rng.random() < 0.72 else P["roof_grey"])
    is_station = style == "station"
    gable = not is_station and style not in ("industrial", "mausoleum") and depth_px <= 175
    rise = min(22, max(10, width_px // 100 + 9))
    antenna = gable and style == "residential" and width_px > 90 and rng.random() < 0.55

    # Estremi in coordinate locali: sud-ovest della parete sud è (0, 0).
    x_min = -OVERHANG - SHADOW_R
    x_max = width_px + depth_px + OVERHANG + (CANOPY_D if is_station else 0)
    y_top = -wall_h_px - depth_px - OVERHANG
    if gable:
        y_top = min(y_top, -wall_h_px - depth_px / 2 - rise - OVERHANG - 16)
        if antenna:
            y_top = min(y_top, -wall_h_px - depth_px / 2 - rise - OVERHANG - 25)
    if is_station:
        y_top = min(y_top, -wall_h_px - depth_px + 4 - CANOPY_D)

    ox = -x_min + 1
    oy = -y_top + 1
    img_w = int(math.ceil(x_max - x_min)) + 2
    img_h = int(math.ceil(-y_top + BOTTOM_PAD)) + 2
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    p = Painter(img, ox, oy)

    # Dal fondo verso l'alto: ombra, pensilina, parete est, parete sud, tetto.
    contact_shadow(p, width_px)
    if is_station:
        draw_canopy(p, width_px, wall_h_px, depth_px)
    draw_east_wall(p, width_px, wall_h_px, depth_px, wall, style, levels, rng)
    if gable:
        draw_gable_end(p, width_px, wall_h_px, depth_px, rise, wall)
    draw_south_wall(p, width_px, wall_h_px, wall, style, levels, rng)
    if is_station:
        draw_station_sign(p, width_px, wall_h_px)
    if gable:
        draw_gable_roof(p, width_px, wall_h_px, depth_px, rise, roof_color, antenna)
    else:
        draw_flat_roof(p, width_px, wall_h_px, depth_px, roof_color, is_station)

    anchor_x = (minx + maxx) / 2
    anchor_y = maxy
    fname = "b_" + re.sub(r"[^a-zA-Z0-9_]", "_", bid.replace("/", "_")) + ".png"
    save_png(img, OUT / fname)

    return {
        "id": bid,
        "name": b.get("name", ""),
        "kind": b["kind"],
        "sprite": f"assets/buildings/{fname}",
        "anchor_x": round(anchor_x, 3),
        "anchor_y": round(anchor_y, 3),
        "w": img.width,
        "h": img.height,
        "height_m": height_m,
        "style": style,
        "origin_x": round((ox + width_px / 2) / img_w, 5),
        "origin_y": round(oy / img_h, 5),
        "wall_h_px": wall_h_px,
        "width_px": width_px,
        "depth_px": depth_px,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = [make_building(b) for b in WORLD["buildings"]]
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.glob("*.png"))
    print(f"OK {len(manifest)} edifici, {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
