#!/usr/bin/env python3
"""Genera edifici in pixel art originale con proiezione obliqua a tre quarti.

La geometria deriva ESCLUSIVAMENTE dal bbox del perimetro OSM salvato in
``data/world/pianura_world.json``: larghezza = (maxx-minx)*16 px, profondità =
(maxy-miny)*8 px (asse di profondità a 45 gradi, scala 0,5). Non si dipinge mai
il footprint piatto come facciata: si costruiscono parete sud rettangolare,
parete est parallelogramma e tetto architettonico.

La 0.4.0 aggiunge dettagli architettonici deliberati: cornici di piano, plinti,
gronde, persiane a listelli, balconi in ferro battuto, insegne commerciali,
terrazze con bucato e tetti in tegole regolari. Ogni dettaglio resta ancorato
alla griglia di 38 x 46 px e non viene sparso a caso.

Regole vincolanti: docs/ART_SPEC.md (1 m = 16 px, finestre 12x16 con passo
38x46 px, porta 22x38 al livello strada, ombra di contatto morbida).
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw
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

STUCCOS = [
    P["stucco_cream"], P["stucco_ochre"], P["stucco_pink"],
    P["stucco_yellow"], P["stucco_green"], P["stucco_blue"],
]
SHUTTERS = [P["wood"], P["green_dark"], P["stucco_cream"], P["brown"]]
DOORS = [P["wood"], P["brown"], P["eav_blue"], P["green_dark"]]

# Insegne plausibili per attività reali presenti nei tag OSM. Se il nome non è
# disponibile si usa una categoria generica: nessuna attività inventata sul bbox.
RETAIL_LABELS = (
    ("BAR", "terra"), ("ALIMENTARI", "green_dark"), ("TABACCHI", "eav_blue"),
    ("NEGOZIO", "brown"), ("CAFFE", "terra"), ("PIZZERIA", "red"),
)
RETAIL_COLORS = {
    "terra": P["terra"], "green_dark": P["green_dark"],
    "eav_blue": P["eav_blue"], "brown": P["brown"], "red": P["red"],
}

# Font bitmap 3x5: nessuna dipendenza da font di sistema, pixel art nitida.
FONT3 = {
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "Z": ("111", "001", "010", "100", "111"),
    " ": ("000", "000", "000", "000", "000"),
}


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


def draw_text3(p: Painter, x: float, y: float, text: str, fill,
               scale: int = 1) -> None:
    """Scrive testo con il font bitmap 3x5, senza anti-aliasing."""
    cx = int(x)
    for ch in text.upper():
        glyph = FONT3.get(ch, FONT3[" "])
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    p.box(cx + col * scale, y + row * scale,
                          cx + (col + 1) * scale - 1, y + (row + 1) * scale - 1, fill)
        cx += 4 * scale


def grid_positions(width_px: int) -> list[int]:
    """Top-left x delle finestre: passo esatto 38 px, griglia centrata."""
    n = max(1, int(width_px // STEP_X))
    while n > 1 and (n - 1) * STEP_X > width_px - 12:
        n -= 1
    start = (width_px - (n - 1) * STEP_X - WIN_W) / 2
    return [int(round(start + i * STEP_X)) for i in range(n)]


def draw_window(p: Painter, x: int, y: int, wall, shutter,
                variant: str = "home", balcony: bool = False) -> None:
    """Finestra 12x16 px costruita pixel per pixel, incassata nella muratura.

    Ogni variante ha una struttura precisa: persiane con listelli nelle case,
    vetrina con serranda avvolgibile nei negozi, vetrata blu EAV alla stazione.
    """
    # Cornice in pietra e ombra dell'incavo: due toni, nessun antialiasing.
    p.box(x - 3, y - 3, x + 14, y + 17, rgba(shade(wall, 0.50), 255))
    p.box(x - 2, y - 2, x + 13, y + 16, rgba(P["concrete_light"], 255))
    p.box(x - 1, y - 1, x + 12, y + 15, rgba(P["ink_soft"], 255))
    p.box(x, y, x + 11, y + 14, rgba(P["glass"], 255))

    # Riflessi obliqui deterministici e telai incrociati.
    p.seg([(x + 1, y + 13), (x + 5, y + 1)], rgba(P["glass_light"], 170), 2)
    p.seg([(x + 7, y + 13), (x + 10, y + 5)], rgba(P["glass_light"], 95), 1)
    p.seg([(x + 5, y), (x + 5, y + 14)], rgba(P["ink"], 155))
    p.seg([(x, y + 7), (x + 11, y + 7)], rgba(P["ink"], 155))
    p.seg([(x, y + 14), (x + 11, y + 14)], rgba(P["white"], 70))

    # Cassonetto e davanzale: la griglia resta allineata a 38 x 46 px.
    p.box(x - 3, y - 5, x + 14, y - 3, rgba(shade(wall, 0.78), 255))
    p.box(x - 3, y - 5, x + 14, y - 5, rgba(P["concrete_light"], 255))
    p.box(x - 3, y + 16, x + 14, y + 18, rgba(P["concrete_light"], 255))
    p.seg([(x - 3, y + 18), (x + 14, y + 18)], rgba(shade(wall, 0.65), 255))

    if variant == "station":
        p.box(x - 3, y - 2, x - 1, y + 16, rgba(P["eav_blue"], 255))
        p.box(x + 12, y - 2, x + 14, y + 16, rgba(P["eav_blue"], 255))
        p.seg([(x, y + 15), (x + 11, y + 15)], rgba(P["white"], 170))
    elif variant == "retail":
        # Vetrina con serranda a listelli nella parte alta e fascia insegna.
        p.box(x - 3, y - 2, x + 14, y + 16, rgba(P["metal"], 255))
        for yy in range(y, y + 16, 3):
            p.seg([(x - 2, yy), (x + 13, yy)], rgba(P["ink_soft"], 100))
        p.box(x - 3, y - 4, x + 14, y - 2, rgba(P["eav_blue"], 255))
    else:
        for sx in (x - 5, x + 12):
            p.box(sx, y - 2, sx + 2, y + 17, rgba(shade(shutter, 0.90), 255))
            p.box(sx, y - 2, sx + 2, y - 2, rgba(P["ink"], 150))
            for yy in range(y + 1, y + 17, 3):
                p.seg([(sx, yy), (sx + 2, yy)], rgba(P["ink"], 95))
            p.seg([(sx + 3, y + 2), (sx + 3, y + 13)], rgba(P["metal"], 255))

    if balcony:
        # Solo ai piani superiori: lastra con ombra, ringhiera in ferro e fiori.
        p.box(x - 6, y + 19, x + 18, y + 21, rgba(shade(P["concrete"], 0.92), 255))
        p.box(x - 6, y + 21, x + 18, y + 22, rgba(P["ink_soft"], 150))
        p.box(x - 6, y + 9, x + 18, y + 10, rgba(P["metal"], 255))
        p.box(x - 6, y + 18, x + 18, y + 19, rgba(P["metal"], 255))
        for xx in range(x - 5, x + 18, 4):
            p.box(xx, y + 10, xx + 1, y + 18, rgba(P["ink_soft"], 255))
        for xx in (x - 2, x + 13):
            p.seg([(xx, y + 11), (xx + 3, y + 16)], rgba(P["metal_light"], 140))
        p.box(x - 3, y + 14, x, y + 18, rgba(P["terra_dark"], 255))
        p.box(x - 3, y + 12, x - 2, y + 13, rgba(P["red"], 255))
        p.box(x + 13, y + 14, x + 16, y + 18, rgba(P["terra_dark"], 255))
        p.box(x + 14, y + 12, x + 15, y + 13, rgba(P["yellow"], 255))


def draw_side_window(p: Painter, x: float, y: float, wall, shutter,
                     variant: str) -> None:
    """Finestra sulla parete est, parallelogrammo coerente con la proiezione."""
    frame = [(x - 2, y + 1), (x + 14, y - 13), (x + 14, y + 5), (x - 2, y + 19)]
    glass = [(x, y), (x + 12, y - 12), (x + 12, y + 4), (x, y + 16)]
    p.poly(frame, rgba(P["concrete_light"], 255))
    p.poly([(x - 1, y), (x + 13, y - 12), (x + 13, y + 5), (x - 1, y + 17)],
           rgba(P["ink_soft"], 255))
    p.poly(glass, rgba(P["glass"], 255))
    p.seg([(x + 3, y + 11), (x + 8, y - 8)], rgba(P["glass_light"], 150), 2)
    p.seg([(x + 6, y - 6), (x + 6, y + 10)], rgba(P["ink"], 145))
    p.seg([(x, y + 4), (x + 12, y - 8)], rgba(P["ink"], 120))
    p.seg([(x - 2, y + 19), (x + 14, y + 5)], rgba(shade(wall, 0.65), 255))
    if variant == "home":
        p.seg([(x - 4, y + 1), (x - 4, y + 17)], rgba(shade(shutter, 0.88), 255), 2)
        for yy in (4, 8, 12):
            p.seg([(x - 4, y + yy), (x - 4, y + yy + 1)], rgba(P["ink"], 90))


def draw_door(p: Painter, x: int, wall, rng, style: str) -> None:
    """Portale napoletano: cornice in pietra, transom, ante e gradino."""
    color = P["eav_blue"] if style == "station" else rng.choice(DOORS)
    # Cornice a gradoni: il portone resta centrato e a livello strada.
    p.box(x - 5, -DOOR_H - 8, x + DOOR_W + 5, 2, rgba(P["ink"], 215))
    p.box(x - 4, -DOOR_H - 7, x + DOOR_W + 4, 1, rgba(P["concrete_light"], 255))
    p.box(x - 3, -DOOR_H - 6, x + DOOR_W + 3, 0, rgba(shade(wall, 0.78), 255))
    # Transom superiore a vetro, diviso in tre riquadri.
    p.box(x - 1, -DOOR_H - 4, x + DOOR_W + 1, -DOOR_H + 6, rgba(P["ink_soft"], 255))
    p.box(x, -DOOR_H - 3, x + DOOR_W, -DOOR_H + 5, rgba(P["glass"], 255))
    p.seg([(x + 7, -DOOR_H - 3), (x + 7, -DOOR_H + 5)], rgba(P["ink"], 140))
    p.seg([(x + 14, -DOOR_H - 3), (x + 14, -DOOR_H + 5)], rgba(P["ink"], 140))
    p.seg([(x + 1, -DOOR_H + 3), (x + 5, -DOOR_H - 1)], rgba(P["glass_light"], 150))
    # Ante con pannelli incassati e maniglie ottonate.
    p.box(x - 1, -DOOR_H + 7, x + DOOR_W + 1, 0, rgba(P["ink"], 255))
    p.box(x, -DOOR_H + 7, x + DOOR_W - 1, -1, rgba(color, 255))
    p.box(x + 2, -DOOR_H + 9, x + 9, -21, rgba(shade(color, 0.72), 255))
    p.box(x + 12, -DOOR_H + 9, x + DOOR_W - 3, -21, rgba(shade(color, 0.72), 255))
    p.box(x + 3, -DOOR_H + 10, x + 8, -22, rgba(shade(color, 1.12), 255))
    p.box(x + 13, -DOOR_H + 10, x + DOOR_W - 4, -22, rgba(shade(color, 1.12), 255))
    p.box(x + 9, -17, x + 11, -16, rgba(P["yellow"], 255))
    p.box(x + DOOR_W - 12, -17, x + DOOR_W - 10, -16, rgba(P["yellow"], 255))
    # Targhetta civico e gradino in pietra.
    p.box(x + DOOR_W - 7, -DOOR_H - 6, x + DOOR_W + 1, -DOOR_H, rgba(P["white"], 255))
    draw_text3(p, x + DOOR_W - 6, -DOOR_H - 5, "N", rgba(P["ink"], 255))
    p.box(x - 6, 0, x + DOOR_W + 6, 3, rgba(P["concrete_light"], 255))
    p.box(x - 6, 3, x + DOOR_W + 6, 5, rgba(shade(wall, 0.68), 255))
    p.seg([(x - 6, 0), (x + DOOR_W + 6, 0)], rgba(P["ink"], 100))


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
    p.poly([(w, -h), (w + depth, -h - depth), (w + depth, -h - depth + 3), (w, -h + 3)],
           rgba(shade(wall, 1.10), 255))
    p.seg([(w, -h), (w + depth, -h - depth)], rgba(P["ink"], 120))

    # Linee di piano e giunti verticali nella proiezione cabinet.
    for lv in range(1, levels):
        p.seg([(w, -lv * FLOOR_PX), (w + depth, -lv * FLOOR_PX - depth)],
              rgba(shade(wall, 0.66), 140))
    for t in range(38, depth, 38):
        p.seg([(w + t, -t), (w + t, -h - t)], rgba(shade(wall, 0.70), 85))

    # Grondaia e pluviale: elementi architettonici, non decorazione casuale.
    p.seg([(w + depth - 4, -depth - 2), (w + depth - 4, -h - depth + 2)],
          rgba(P["metal"], 190))
    p.box(w + depth - 5, -h - depth + 2, w + depth - 3, -h - depth + 5,
          rgba(P["metal_light"], 255))

    if depth >= 22:
        n = max(1, int(depth // STEP_X))
        shutter = rng.choice(SHUTTERS)
        variant = "station" if style == "station" else ("retail" if style == "retail" else "home")
        for lv in range(levels):
            for i in range(n):
                t = (i + 0.5) * depth / n
                if t + 12 > depth:
                    continue
                # Stessa griglia della parete sud: piano terra in basso a -34.
                y = -34 - lv * FLOOR_PX - t
                draw_side_window(p, w + t, y, wall, shutter, variant)


def draw_south_wall(p: Painter, w: int, h: int, wall, style: str,
                    levels: int, rng, name: str = "") -> list[tuple[int, int]]:
    """Costruisce la facciata sud e restituisce le finestre dei piani superiori.

    Ogni coppia è (centro-x locale, top-y locale) nel sistema di coordinate del
    generatore. Il manifest la passa al motore, che disegna le luci notturne
    esattamente dentro i vetri invece di usare una griglia approssimata.
    """
    p.box(0, -h, w, 0, rgba(wall, 255))

    # Zoccolo, marcapiano e cornice: la facciata è un volume, non un rettangolo.
    p.box(0, -8, w, 0, rgba(shade(wall, 0.80), 255))
    p.box(0, -10, w, -8, rgba(shade(wall, 0.93), 255))
    p.box(0, -h, w, -h + 4, rgba(shade(wall, 1.12), 255))
    p.seg([(0, -h + 4), (w, -h + 4)], rgba(P["ink"], 90))
    for lv in range(1, levels):
        y = -lv * FLOOR_PX
        p.box(0, y, w, y + 2, rgba(shade(wall, 0.74), 170))
        p.seg([(0, y + 3), (w, y + 3)], rgba(shade(wall, 1.10), 190))
    p.box(0, -h, 2, 0, rgba(shade(wall, 1.05), 255))
    p.box(w - 2, -h, w, 0, rgba(shade(wall, 0.86), 255))

    xs = grid_positions(w)
    # Pilastri solo in corrispondenza di ogni terza finestra: ritmo regolare.
    for px in xs[::3]:
        p.box(px - 6, -h + 4, px - 4, 0, rgba(shade(wall, 0.90), 100))

    # Texture minima e deterministica: due pixel per modulo, non rumore sparso.
    for _ in range(min(36, w // 5)):
        x, y = rng.randrange(w), rng.randrange(-h + 4, -12)
        p.box(x, y, x + 1, y, rgba(shade(wall, 0.92), 55))

    variant = "station" if style == "station" else ("retail" if style == "retail" else "home")
    shutter = rng.choice(SHUTTERS)
    # Solo i piani superiori vengono restituiti: il piano terra resta buio di notte.
    upper_windows: list[tuple[int, int]] = []

    # Fabbricato viaggiatori: colonne in intonaco tra le vetrate.
    if style == "station":
        for x in xs:
            cx = x - 6
            if abs(cx - w / 2) < 16:
                continue
            p.box(cx, -h + 3, cx + 2, 0, rgba(P["concrete_light"], 255))
            p.box(cx - 1, -h + 3, cx + 3, -h + 6, rgba(P["metal_light"], 255))

    # Insegna commerciale: dal nome OSM quando presente, altrimenti categoria.
    if style == "retail" and h >= 92 and xs:
        label = name.strip().upper()[:10] or rng.choice(RETAIL_LABELS)[0]
        color_name = rng.choice(RETAIL_LABELS)[1]
        p.box(4, -44, w - 4, -36, rgba(RETAIL_COLORS[color_name], 255))
        p.box(4, -44, w - 4, -44, rgba(P["white"], 110))
        draw_text3(p, 8, -42, label, rgba(P["white"], 255))

    # Piano terra in basso, a livello strada. La porta resta libera.
    # Alla stazione si libera anche la fascia centrale per insegna e targa.
    clear = 100 if style == "station" else 20
    ground_y = -28 if style == "station" else -34
    for idx, x in enumerate(xs):
        if abs(x + WIN_W / 2 - w / 2) < clear:
            continue
        draw_window(p, x, ground_y, wall, shutter, variant)

    # Piani superiori: la stessa griglia di 46 px del marcapiano, senza offset.
    for lv in range(1, levels):
        y = -34 - lv * FLOOR_PX
        for idx, x in enumerate(xs):
            if abs(x + WIN_W / 2 - w / 2) < clear:
                continue
            balcony = style != "station" and (idx % 2 == 0 or rng.random() < 0.22)
            draw_window(p, x, y, wall, shutter, "home", balcony)
            upper_windows.append((x + WIN_W // 2, y))

    draw_door(p, w // 2 - DOOR_W // 2, wall, rng, style)

    # Pluviali alle estremità: coerenti con la gronda della parete est.
    for px in (5, w - 7):
        p.box(px, -h + 4, px + 2, -2, rgba(P["metal"], 170))
        p.box(px - 1, -10, px + 3, -8, rgba(P["metal_light"], 255))

    return upper_windows


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
                   roof_color, station: bool, rng) -> None:
    """Terrazza napoletana: parapetto, lastrico a quote, scarichi e bucato.

    La stazione resta sobria (solo gronda e cornice); le abitazioni hanno
    elementi quotidiani deliberati, non oggetti sparsi a caso.
    """
    p.poly([(-OVERHANG, -h + OVERHANG), (w + OVERHANG, -h + OVERHANG),
            (w + depth + OVERHANG, -h - depth - OVERHANG),
            (depth - OVERHANG, -h - depth - OVERHANG)],
           rgba(shade(roof_color, 1.10), 255), rgba(P["ink"], 155))
    for x in range(0, w, 16):
        p.seg([(x, -h + OVERHANG), (x + depth, -h - depth - OVERHANG)],
              rgba(P["ink"], 45))
    for t in range(16, depth, 16):
        p.seg([(t, -h - t), (w + t, -h - t)], rgba(P["ink"], 35))
    # Parapetto sul bordo sud, con ombra proiettata sul lastrico.
    p.poly([(-OVERHANG, -h + OVERHANG), (w + OVERHANG, -h + OVERHANG),
            (w + OVERHANG + 4, -h - 4), (depth - OVERHANG + 4, -h - depth - OVERHANG)],
           rgba(shade(roof_color, 0.80), 255), rgba(P["ink"], 140))
    p.poly([(-OVERHANG, -h + OVERHANG), (w + OVERHANG, -h + OVERHANG),
            (w + OVERHANG, -h + OVERHANG + 3), (-OVERHANG, -h + OVERHANG + 3)],
           rgba(shade(roof_color, 0.72), 255))

    if station:
        return

    # Botole e comignoli tecnici: posizioni fisse in frazioni della larghezza.
    for frac in (0.20, 0.76):
        x = int(w * frac)
        p.box(x, -h - 10, x + 12, -h - 2, rgba(P["metal"], 255))
        p.box(x + 1, -h - 9, x + 11, -h - 4, rgba(P["metal_light"], 255))
        p.box(x + 2, -h - 8, x + 10, -h - 6, rgba(P["ink_soft"], 255))

    # Serbatoio dell'acqua: tipico dei tetti napoletani, con sostegni in ferro.
    if w > 120:
        tx = int(w * 0.52)
        ty = int(-h - depth * 0.42)
        p.box(tx - 16, ty - 18, tx + 16, ty + 6, rgba(P["metal"], 255))
        p.box(tx - 15, ty - 17, tx + 15, ty + 4, rgba(P["metal_light"], 255))
        p.box(tx - 15, ty - 10, tx + 15, ty - 9, rgba(P["ink"], 130))
        p.seg([(tx - 12, ty + 6), (tx - 10, ty + 14)], rgba(P["ink_soft"], 255), 2)
        p.seg([(tx + 12, ty + 6), (tx + 10, ty + 14)], rgba(P["ink_soft"], 255), 2)

    # Filo del bucato teso tra due pali, con tre capi deterministici.
    if w > 150 and depth > 40:
        lx, rx = int(w * 0.12), int(w * 0.42)
        ly = int(-h - depth * 0.70)
        ry = ly - 20
        p.seg([(lx, ly + 12), (lx, ly - 8)], rgba(P["metal_light"], 255))
        p.seg([(rx, ry + 12), (rx, ry - 8)], rgba(P["metal_light"], 255))
        p.seg([(lx, ly - 7), (rx, ry - 7)], rgba(P["ink_soft"], 255))
        cloth = [P["white"], P["eav_light"], P["terra_light"]]
        for i, color in enumerate(cloth):
            cx = lx + (rx - lx) * (i + 1) // 4
            cy = ly - 7 + (ry - ly) * (i + 1) // 4
            p.box(cx - 6, cy, cx + 6, cy + 12, rgba(color, 255))
            p.seg([(cx - 5, cy + 2), (cx + 5, cy + 2)], rgba(shade(color, 0.85), 255))


def draw_station_sign(p: Painter, w: int, h: int) -> None:
    """Insegna e targhe dell'ingresso, senza inventare un logo EAV.

    La foto 2018 mostra una scritta "Pianura"; le fonti 2020 documentano le
    targhe dell'intitolazione a Don Giustino Russolillo. Non inventa un logo
    EAV: usa solo il nome della fermata documentato dalle fonti.
    """
    sx = w // 2 - 95
    sy = -h + 2
    p.box(sx - 3, sy - 1, sx + 135, sy + 20, rgba(P["ink"], 235))
    p.box(sx - 1, sy + 1, sx + 133, sy + 18, rgba(P["eav_blue"], 255))
    draw_text3(p, sx + 27, sy + 2, "PIANURA", rgba(P["white"], 255), 3)
    # Targa dell'intitolazione, più piccola e separata dall'insegna.
    p.box(sx - 2, sy + 22, sx + 190, sy + 36, rgba(P["concrete_light"], 255))
    p.box(sx - 2, sy + 22, sx + 190, sy + 22, rgba(P["ink"], 150))
    draw_text3(p, sx + 4, sy + 25, "DON GIUSTINO RUSSOLILLO", rgba(P["ink"], 255))


def draw_station_murals(p: Painter, w: int, h: int, depth: int) -> None:
    """Due pannelli originali sulla parete est, ispirati ai soggetti documentati.

    Sono disegni generati dal codice: figure e cantiere astratti, non una copia
    dei murales di Luca Danza. La proiezione segue la parete est a 45 gradi.
    """
    if depth < 100:
        return
    for mi, t in enumerate((16, 70)):
        x0, y0 = w + t, -h * 0.62 - t
        mw, mh = 44, 24
        quad = [(x0, y0), (x0 + mw, y0 - mw),
                (x0 + mw, y0 - mw - mh), (x0, y0 - mh)]
        p.poly([(x0 - 2, y0 + 2), (x0 + mw + 2, y0 - mw + 2),
                (x0 + mw + 2, y0 - mw - mh - 2), (x0 - 2, y0 - mh - 2)],
               rgba(P["ink"], 205))
        p.poly(quad, rgba(P["stucco_cream"], 255))
        if mi == 0:
            # Tre figure stilizzate, con colori della palette del progetto.
            for i, fx in enumerate((x0 + 10, x0 + 22, x0 + 34)):
                fy = y0 - 12 - (fx - x0)
                p.oval(fx - 2, fy - 2, fx + 2, fy + 2, rgba(P["skin2"], 255))
                p.box(fx - 3, fy + 3, fx + 3, fy + 10,
                      rgba((P["eav_light"], P["terra"], P["green"])[i], 255))
        else:
            # Cantiere del Vocazionario: impalcatura e tetto in costruzione.
            for xx in range(x0 + 6, x0 + mw - 2, 8):
                p.seg([(xx, y0 - 8 - (xx - x0)), (xx, y0 - 20 - (xx - x0))],
                      rgba(P["wood"], 255))
            p.seg([(x0 + 4, y0 - 10 - 4), (x0 + mw - 4, y0 - 10 - (mw - 4))],
                  rgba(P["wood"], 255))
            p.poly([(x0 + 8, y0 - 12 - 8), (x0 + mw - 6, y0 - 12 - (mw - 6)),
                    (x0 + mw - 12, y0 - 20 - (mw - 12))],
                   rgba(P["terra"], 255))


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
    # La foto 2018 analizzata localmente mostra due piani; OSM non riporta piani.
    if style == "station":
        return 2
    if style in ("industrial", "mausoleum"):
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
    x_max = width_px + depth_px + OVERHANG
    y_top = -wall_h_px - depth_px - OVERHANG
    if gable:
        y_top = min(y_top, -wall_h_px - depth_px / 2 - rise - OVERHANG - 16)
        if antenna:
            y_top = min(y_top, -wall_h_px - depth_px / 2 - rise - OVERHANG - 25)

    ox = -x_min + 1
    oy = -y_top + 1
    img_w = int(math.ceil(x_max - x_min)) + 2
    img_h = int(math.ceil(-y_top + BOTTOM_PAD)) + 2
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    p = Painter(img, ox, oy)

    # Dal fondo verso l'alto: ombra, parete est, parete sud, tetto.
    # Nessuna pensilina: OSM riporta shelter=no su entrambe le banchine.
    contact_shadow(p, width_px)
    draw_east_wall(p, width_px, wall_h_px, depth_px, wall, style, levels, rng)
    if is_station:
        draw_station_murals(p, width_px, wall_h_px, depth_px)
    if gable:
        draw_gable_end(p, width_px, wall_h_px, depth_px, rise, wall)
    upper_windows = draw_south_wall(p, width_px, wall_h_px, wall, style, levels, rng, b.get("name", ""))
    if is_station:
        draw_station_sign(p, width_px, wall_h_px)
    if gable:
        draw_gable_roof(p, width_px, wall_h_px, depth_px, rise, roof_color, antenna)
    else:
        draw_flat_roof(p, width_px, wall_h_px, depth_px, roof_color, is_station, rng)

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
        # Finestre reali dei piani superiori in coordinate locali (centro-x, top-y).
        "windows": [[cx, wy] for cx, wy in upper_windows],
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
