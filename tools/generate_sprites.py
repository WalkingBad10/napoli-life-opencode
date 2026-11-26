#!/usr/bin/env python3
"""Sprite originali in pixel art per NAPOLI LIFE 0.3.0.

Proiezione obliqua a tre quarti, scala uniforme 1 m = 16 px, zero anti-aliasing.
Tutto e' disegnato con primitive intere (artlib + helper locali) e reso
deterministico da seed stabili. Ogni sprite riceve un contorno scuro di 1 px
calcolato dalla silhouette opaca, piu' un'ombra di contatto a bassa alpha.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from artlib import P, ellipse, line, rect, rgba, save_png, seeded, shade

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/assets/sprites"

PPM = 16                  # pixel per metro (contratto ART_SPEC.md)
FW, FH = 16, 32           # frame personaggio: 1,0 x 2,0 m
FEET_Y = 30               # piedi a y=30, origine ai piedi
SHEET_COLUMNS, SHEET_ROWS = 4, 4
SHEET_W, SHEET_H = FW * SHEET_COLUMNS, FH * SHEET_ROWS  # 64 x 128
DIRECTIONS = ("down", "left", "right", "up")

INK = P["ink"]
SHADOW = rgba(P["shadow"], 44)   # ombra di contatto, alpha <= 45


# ---------------------------------------------------------------------------
# Helper locali
# ---------------------------------------------------------------------------

def dim(color, factor: float):
    """Come shade(), ma accetta anche colori gia' derivati (tuple RGB)."""
    if isinstance(color, str):
        return shade(color, factor)
    r, g, b = color[:3]
    return (min(255, int(r * factor)), min(255, int(g * factor)), min(255, int(b * factor)))


def start(w: int, h: int):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img, "RGBA")


def poly(d: ImageDraw.ImageDraw, pts, fill) -> None:
    d.polygon([(int(x), int(y)) for x, y in pts], fill=fill)


def contact(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int) -> None:
    ellipse(d, x0, y0, x1, y1, SHADOW)


def outlined(img: Image.Image, bounds: tuple[int, int, int, int] | None = None) -> Image.Image:
    """Contorno scuro coerente: 1 px tutt'intorno ai pixel opachi.

    I pixel semitrasparenti (ombra di contatto) non generano contorno.
    `bounds` (xmin, xmax, ymin, ymax) limita il contorno: per i personaggi
    lascia 1 px di margine laterale e nessun pixel sotto i piedi (y=30).
    Nessuna interpolazione: solo pixel pieni, quindi zero anti-aliasing.
    """
    w, h = img.size
    xlo, xhi, ylo, yhi = bounds if bounds else (0, w - 1, 0, h - 1)
    src = img.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    opaque = [[src[x, y][3] == 255 for x in range(w)] for y in range(h)]
    edge = rgba(INK)
    for y in range(h):
        for x in range(w):
            if opaque[y][x]:
                dst[x, y] = src[x, y]
    for y in range(h):
        for x in range(w):
            if not opaque[y][x]:
                continue
            for dy in (-1, 0, 1):
                ny = y + dy
                if ny < ylo or ny > yhi:
                    continue
                for dx in (-1, 0, 1):
                    nx = x + dx
                    if nx < xlo or nx > xhi:
                        continue
                    if not opaque[ny][nx]:
                        dst[nx, ny] = edge
    return out


def finish(img: Image.Image, name: str) -> None:
    save_png(outlined(img), OUT / f"{name}.png")


# Font bitmap 3x5: solo lettere maiuscole essenziali, senza anti-aliasing.
FONT3 = {
    "A": ("010", "101", "111", "101", "101"),
    "E": ("111", "100", "110", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "V": ("101", "101", "101", "101", "010"),
}

def tiny_text(d: ImageDraw.ImageDraw, x: int, y: int, text: str, color, scale: int = 1) -> None:
    for i, ch in enumerate(text.upper()):
        glyph = FONT3.get(ch)
        if not glyph:
            continue
        gx = x + i * 4 * scale
        for ry, row in enumerate(glyph):
            for rx, bit in enumerate(row):
                if bit == "1":
                    rect(d, gx + rx * scale, y + ry * scale,
                         gx + (rx + 1) * scale - 1, y + (ry + 1) * scale - 1, color)


# ---------------------------------------------------------------------------
# Personaggi: 7 varianti, 4 direzioni x 4 frame, cella 16x32, piedi a y=30
# ---------------------------------------------------------------------------

CHARS = {
    "player":   {"skin": P["skin1"], "hair": P["hair2"], "shirt": shade(P["eav_light"], 0.85),
                 "pants": shade(P["ink_soft"], 0.90), "shoes": dim(P["ink"], 0.90), "acc": "satchel"},
    "resident": {"skin": P["skin2"], "hair": P["hair1"], "shirt": P["terra"],
                 "pants": shade(P["green_dark"], 0.95), "shoes": dim(P["ink"], 0.85), "acc": "none"},
    "worker":   {"skin": P["skin3"], "hair": P["hair3"], "shirt": P["yellow"],
                 "pants": shade(P["metal"], 0.75), "shoes": P["ink"], "acc": "hardhat"},
    "elderly":  {"skin": P["skin1"], "hair": P["concrete_light"], "shirt": shade(P["green"], 0.90),
                 "pants": shade(P["brown"], 0.75), "shoes": dim(P["ink"], 0.90), "acc": "cane"},
    "teen":     {"skin": P["skin2"], "hair": P["hair1"], "shirt": P["stucco_pink"],
                 "pants": dim(P["ink_soft"], 0.80), "shoes": dim(P["ink"], 0.80), "acc": "cap"},
    "railway":  {"skin": P["skin1"], "hair": P["hair1"], "shirt": P["eav_blue"],
                 "pants": shade(P["eav_blue"], 0.60), "shoes": dim(P["ink"], 0.90), "acc": "uniform"},
    "vendor":   {"skin": P["skin2"], "hair": P["hair3"], "shirt": P["white"],
                 "pants": P["brown"], "shoes": dim(P["ink"], 0.90), "acc": "apron"},
}

SWING = (0, 1, 0, -1)   # passo: gamba avanti / indietro
BOUNCE = (0, -1, 0, -1) # leggero rimbalzo del busto


def draw_character_accessory(d, pal: dict, direction: int, bob: int) -> None:
    acc = pal["acc"]
    hy = 3 + bob
    face = direction == 0
    back = direction == 3

    if acc == "satchel":
        if face or back:
            rect(d, 2, 18 + bob, 4, 22 + bob, P["brown"])
            line(d, [(4, 15 + bob), (6, 18 + bob)], P["brown"], 1)
        else:
            x = 11 if direction == 1 else 1
            rect(d, x, 18 + bob, x + 2, 22 + bob, P["brown"])
            line(d, [(x + 2, 15 + bob), (x + 3, 18 + bob)], P["brown"], 1)
    elif acc == "hardhat":
        rect(d, 5, hy - 2, 10, hy + 2, shade(P["yellow"], 0.95))
        rect(d, 3, hy + 3, 12, hy + 4, shade(P["yellow"], 0.80))
        rect(d, 7, hy - 2, 8, hy + 2, shade(P["yellow"], 1.15))
    elif acc == "cane":
        rect(d, 12, 19 + bob, 13, 20 + bob, P["wood"])
        rect(d, 13, 20, 13, FEET_Y, P["wood"])
        line(d, [(13, 20), (14, 21)], P["wood"], 1)
    elif acc == "cap":
        rect(d, 4, hy, 11, hy + 2, P["red"])
        if face:
            rect(d, 3, hy + 3, 12, hy + 4, dim(P["red"], 0.80))
        elif direction == 1:
            rect(d, 2, hy + 3, 6, hy + 4, dim(P["red"], 0.80))
        elif direction == 2:
            rect(d, 9, hy + 3, 13, hy + 4, dim(P["red"], 0.80))
        else:
            rect(d, 4, hy - 1, 11, hy, dim(P["red"], 0.80))
    elif acc == "uniform":
        rect(d, 4, hy, 11, hy + 2, P["eav_blue"])
        rect(d, 4, hy + 2, 11, hy + 3, P["yellow"])
        if face:
            rect(d, 3, hy + 3, 12, hy + 4, dim(P["eav_blue"], 0.80))
        elif direction == 1:
            rect(d, 2, hy + 3, 6, hy + 4, dim(P["eav_blue"], 0.80))
        elif direction == 2:
            rect(d, 9, hy + 3, 13, hy + 4, dim(P["eav_blue"], 0.80))
        # gilet ad alta visibilita' + radio di servizio
        rect(d, 5, 16 + bob, 10, 22 + bob, P["yellow"])
        rect(d, 5, 18 + bob, 10, 18 + bob, P["white"])
        rect(d, 5, 21 + bob, 10, 21 + bob, P["white"])
        rect(d, 11, 18 + bob, 12, 20 + bob, P["ink"])
    elif acc == "apron":
        rect(d, 5, 3, 10, hy + 3, shade(P["yellow"], 0.85))   # cappello di paglia
        rect(d, 2, hy + 3, 13, hy + 4, shade(P["yellow"], 0.75))
        rect(d, 5, hy + 3, 10, hy + 3, P["brown"])
        if face or back:
            rect(d, 5, 15 + bob, 10, 22 + bob, P["white"])
            rect(d, 5, 15 + bob, 5, 17 + bob, dim(P["white"], 0.85))
            rect(d, 10, 15 + bob, 10, 17 + bob, dim(P["white"], 0.85))
            rect(d, 6, 19 + bob, 9, 19 + bob, P["terra"])
        else:
            x = 6 if direction == 1 else 8
            rect(d, x, 15 + bob, x + 3, 22 + bob, P["white"])


def character_cell(name: str, direction: int, frame: int) -> Image.Image:
    pal = CHARS[name]
    skin, hair = pal["skin"], pal["hair"]
    shirt, pants, shoes = pal["shirt"], pal["pants"], pal["shoes"]
    swing, bob = SWING[frame], BOUNCE[frame]
    img, d = start(FW, FH)
    contact(d, 3, 29, 12, 31)

    # Bracci da 3 px (altrimenti il contorno da 1 px mangerebbe il colore).
    left_far = direction == 2
    right_far = direction == 1
    for side, x0 in ((0, 2), (1, 11)):
        far = (side == 0 and left_far) or (side == 1 and right_far)
        tone = 0.68 if far else (0.92 if side == 0 else 0.82)
        offset = -swing if side == 0 else swing
        rect(d, x0, 15 + bob + offset, x0 + 2, 21 + bob + offset, dim(shirt, tone))
        rect(d, x0, 21 + bob + offset, x0 + 2, 23 + bob + offset,
             dim(skin, 0.78) if far else skin)

    # Gambe da 4 px, scarpe da 5 px: piedi sempre ancorati a y=30.
    rect(d, 8 - swing, 22, 11 - swing, 28, dim(pants, 0.82))       # gamba indietro
    rect(d, 7 - swing, 28, 11 - swing, FEET_Y, dim(shoes, 0.82))
    rect(d, 4 + swing, 22, 7 + swing, 28, pants)                   # gamba avanti
    rect(d, 4 + swing, 28, 8 + swing, FEET_Y, shoes)

    # Collo e torso.
    rect(d, 7, 11 + bob, 8, 13 + bob, skin)
    rect(d, 4, 13 + bob, 11, 22 + bob, shirt)
    rect(d, 4, 13 + bob, 5, 22 + bob, dim(shirt, 1.12))
    rect(d, 10, 13 + bob, 11, 22 + bob, dim(shirt, 0.78))
    rect(d, 6, 13 + bob, 9, 14 + bob, dim(shirt, 0.88))
    if name == "player":
        rect(d, 6, 14 + bob, 9, 14 + bob, P["red"])      # sciarpa

    # Testa, capelli e volto (profilo verso sinistra/destra, schiena senza volto).
    hy = 3 + bob
    rect(d, 4, hy, 11, hy + 8, skin)
    if direction == 3:
        rect(d, 4, hy, 11, hy + 7, hair)
        rect(d, 5, hy + 1, 7, hy + 2, dim(hair, 1.15))
    else:
        rect(d, 4, hy, 11, hy + 3, hair)
        rect(d, 4, hy + 3, 5, hy + 5, hair)
        rect(d, 10, hy + 3, 11, hy + 5, hair)
        if direction == 0:
            rect(d, 6, hy + 4, 6, hy + 5, P["ink"])
            rect(d, 9, hy + 4, 9, hy + 5, P["ink"])
            rect(d, 7, hy + 7, 8, hy + 7, dim(skin, 0.72))
        elif direction == 1:
            rect(d, 7, hy, 11, hy + 3, hair)
            rect(d, 3, hy + 5, 3, hy + 5, skin)          # naso
            rect(d, 5, hy + 4, 5, hy + 5, P["ink"])
            rect(d, 4, hy + 7, 5, hy + 7, dim(skin, 0.72))
        else:
            rect(d, 4, hy, 8, hy + 3, hair)
            rect(d, 12, hy + 5, 12, hy + 5, skin)        # naso
            rect(d, 10, hy + 4, 10, hy + 5, P["ink"])
            rect(d, 10, hy + 7, 11, hy + 7, dim(skin, 0.72))

    draw_character_accessory(d, pal, direction, bob)
    return outlined(img, (1, FW - 2, 0, FEET_Y))


def make_characters() -> None:
    for key in CHARS:
        sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))
        for row in range(SHEET_ROWS):
            for frame in range(SHEET_COLUMNS):
                sheet.paste(character_cell(key, row, frame), (frame * FW, row * FH))
        save_png(sheet, OUT / f"{key}.png")


# ---------------------------------------------------------------------------
# Veicoli (vista 3/4 dall'alto, orientati verso destra a rotazione 0)
# ---------------------------------------------------------------------------

def make_car(name: str, base, hi, lo) -> None:
    img, d = start(72, 40)
    contact(d, 4, 31, 68, 38)
    for wx in (14, 50):
        for wy in (8, 26):
            ellipse(d, wx, wy, wx + 12, wy + 10, P["ink"])
            ellipse(d, wx + 3, wy + 3, wx + 9, wy + 7, P["metal"])
    poly(d, [(8, 13), (13, 9), (16, 7), (54, 7), (60, 9), (67, 13),
             (69, 17), (69, 25), (66, 29), (60, 32), (54, 34), (16, 34),
             (10, 31), (5, 27), (4, 22), (4, 17)], base)
    poly(d, [(20, 11), (25, 9), (48, 9), (53, 12), (55, 17),
             (55, 24), (52, 29), (47, 31), (25, 31), (20, 28),
             (18, 23), (18, 16)], hi)
    # Parabrezza, lunotto e finestrini laterali.
    poly(d, [(48, 10), (53, 13), (54, 19), (48, 19), (46, 14)], P["glass"])
    poly(d, [(20, 12), (25, 10), (25, 24), (20, 26), (19, 20)], P["glass"])
    rect(d, 28, 10, 46, 14, P["glass"])
    rect(d, 28, 27, 46, 30, P["glass"])
    rect(d, 29, 11, 40, 12, P["glass_light"])
    rect(d, 29, 28, 40, 29, P["glass_light"])
    poly(d, [(49, 11), (52, 14), (52, 17), (49, 17)], rgba(P["glass_light"], 255))
    # Portiere, maniglie, cofano, fari e fanali.
    line(d, [(34, 10), (34, 31)], lo, 1)
    rect(d, 31, 16, 34, 17, P["ink_soft"])
    rect(d, 31, 25, 34, 26, P["ink_soft"])
    line(d, [(58, 10), (58, 31)], lo, 1)
    rect(d, 60, 19, 65, 21, hi)
    rect(d, 66, 14, 69, 17, P["white"])
    rect(d, 66, 24, 69, 27, P["white"])
    rect(d, 4, 14, 7, 17, P["red"])
    rect(d, 4, 24, 7, 27, P["red"])
    rect(d, 69, 19, 71, 22, P["ink_soft"])
    rect(d, 49, 7, 52, 9, lo)
    rect(d, 49, 31, 52, 33, lo)
    finish(img, name)


def make_bus() -> None:
    img, d = start(112, 44)
    base = shade(P["green_dark"], 0.95)
    hi = shade(P["green"], 0.90)
    lo = shade(P["green_dark"], 0.70)
    contact(d, 6, 36, 106, 42)
    for wx in (16, 84):
        ellipse(d, wx, 32, wx + 12, 41, P["ink"])
        ellipse(d, wx + 4, 35, wx + 8, 38, P["metal"])
    poly(d, [(8, 11), (14, 7), (20, 5), (98, 5), (105, 9),
             (110, 14), (110, 28), (105, 33), (98, 37), (14, 37),
             (8, 32), (4, 26), (4, 16)], base)
    rect(d, 14, 7, 103, 10, hi)                 # tetto in lamiera chiara
    for x in range(16, 101, 13):                # finestrini allineati
        rect(d, x, 11, x + 9, 21, P["glass"])
        rect(d, x, 11, x + 9, 13, P["glass_light"])
    rect(d, 10, 23, 104, 24, P["yellow"])       # fascia ANM
    for x in (30, 40, 70, 80):                  # porte a due ante
        rect(d, x, 11, x, 32, lo)
    tiny_text(d, 52, 27, "ANM", P["white"])
    rect(d, 101, 8, 108, 12, P["ink"])          # display di destinazione
    tiny_text(d, 102, 8, "E", P["white"])
    rect(d, 107, 15, 110, 18, P["white"])
    rect(d, 107, 24, 110, 27, P["white"])
    rect(d, 4, 15, 7, 18, P["red"])
    rect(d, 4, 25, 7, 28, P["red"])
    finish(img, "bus")


def make_scooter() -> None:
    img, d = start(52, 34)
    base = shade(P["metal_light"], 0.95)
    hi = shade(P["metal_light"], 1.10)
    lo = shade(P["metal"], 0.80)
    contact(d, 4, 28, 48, 33)
    for wx in (7, 33):
        ellipse(d, wx, 21, wx + 12, 33, P["ink"])
        ellipse(d, wx + 4, 25, wx + 8, 29, P["metal_light"])
    poly(d, [(12, 20), (35, 20), (40, 23), (38, 27), (14, 27), (10, 24)], base)
    poly(d, [(38, 20), (42, 9), (48, 8), (49, 22), (45, 26), (40, 25)], base)
    rect(d, 18, 24, 34, 25, hi)                 # pedana
    rect(d, 10, 14, 23, 19, P["ink_soft"])      # sella
    rect(d, 41, 6, 50, 8, P["ink_soft"])        # manubrio
    rect(d, 45, 3, 47, 6, P["ink_soft"])        # specchietto
    ellipse(d, 46, 12, 50, 16, P["white"])      # faro
    rect(d, 9, 17, 12, 19, P["red"])            # fanale posteriore
    line(d, [(49, 8), (48, 12)], lo, 1)
    finish(img, "scooter")


def make_train() -> None:
    """Treno EAV Circumflegrea: due casse, 36 m totali (576 px a 16 px/m)."""
    img, d = start(576, 56)
    car_w, gap = 280, 16
    rng = seeded("train_eav_details")
    for ci in range(2):
        x0 = ci * (car_w + gap)
        contact(d, x0 + 8, 46, x0 + 272, 54)
        for bx in (x0 + 40, x0 + 200):           # carrelli
            rect(d, bx, 44, bx + 42, 50, P["ink_soft"])
            rect(d, bx + 6, 47, bx + 14, 50, P["metal"])
            rect(d, bx + 28, 47, bx + 36, 50, P["metal"])
        poly(d, [(x0 + 6, 14), (x0 + 14, 10), (x0 + 266, 10), (x0 + 274, 14),
                 (x0 + 274, 38), (x0 + 266, 44), (x0 + 14, 44), (x0 + 6, 38)], P["eav_blue"])
        rect(d, x0 + 10, 11, x0 + 270, 14, shade(P["eav_blue"], 1.25))  # tetto
        rect(d, x0 + 8, 32, x0 + 272, 33, P["white"])                  # fascia bianca
        rect(d, x0 + 8, 34, x0 + 272, 37, P["yellow"])                 # fascia oro EAV
        for k in range(6):                       # finestrini allineati (passo 40 px)
            wx = x0 + 24 + 40 * k
            rect(d, wx, 16, wx + 28, 29, P["ink_soft"])
            rect(d, wx + 1, 17, wx + 27, 28, P["glass"])
            rect(d, wx + 1, 17, wx + 12, 21, P["glass_light"])
            if rng.random() < 0.5:               # dettaglio deterministico
                rect(d, wx + 16, 25, wx + 24, 25, shade(P["glass"], 1.15))
        for dx in (x0 + 8, x0 + 254):            # porte
            rect(d, dx, 15, dx + 18, 31, shade(P["eav_blue"], 0.75))
            rect(d, dx + 2, 17, dx + 16, 27, P["glass"])
            rect(d, dx + 2, 17, dx + 8, 21, P["glass_light"])
        tiny_text(d, x0 + 122, 34, "EAV", P["eav_blue"], scale=2)
    rect(d, car_w, 25, car_w + gap, 30, P["ink_soft"])   # gancio tra le casse
    # Pantografo e dispositivi di testa.
    line(d, [(118, 10), (132, 2), (146, 10)], P["metal_light"], 2)
    rect(d, 128, 2, 136, 4, P["ink_soft"])
    rect(d, 6, 20, 10, 24, P["yellow"])
    rect(d, 566, 20, 570, 24, P["red"])
    finish(img, "train_eav")


# ---------------------------------------------------------------------------
# Arredo urbano e oggetti di missione (dimensioni esatte da ART_SPEC.md)
# ---------------------------------------------------------------------------

def make_props() -> None:
    # Lampione 24x76
    img, d = start(24, 76)
    contact(d, 3, 72, 21, 75)
    rect(d, 8, 68, 16, 73, P["ink_soft"])
    rect(d, 11, 14, 13, 69, P["metal"])
    rect(d, 11, 14, 11, 69, P["metal_light"])
    line(d, [(12, 14), (12, 8), (19, 8)], P["metal"], 2)
    rect(d, 17, 8, 22, 15, P["ink"])
    rect(d, 18, 10, 21, 13, P["yellow"])
    rect(d, 20, 5, 20, 7, P["metal_light"])
    finish(img, "lamp")

    # Bidone 20x26
    img, d = start(20, 26)
    contact(d, 2, 23, 18, 25)
    rect(d, 3, 6, 17, 23, shade(P["green_dark"], 0.95))
    rect(d, 5, 9, 5, 22, shade(P["green"], 0.85))
    rect(d, 13, 9, 13, 22, shade(P["green_dark"], 0.75))
    rect(d, 2, 4, 18, 8, P["ink_soft"])
    rect(d, 8, 2, 12, 4, P["metal"])
    rect(d, 8, 11, 12, 13, P["white"])
    rect(d, 9, 15, 11, 15, P["white"])
    finish(img, "bin")

    # Panchina 56x26
    img, d = start(56, 26)
    contact(d, 3, 23, 53, 25)
    for sy in (4, 9):
        rect(d, 6, sy, 52, sy + 3, P["wood"])
        rect(d, 6, sy, 52, sy, shade(P["wood"], 1.12))
    rect(d, 3, 14, 53, 18, P["wood"])
    rect(d, 3, 14, 53, 14, shade(P["wood"], 1.15))
    rect(d, 3, 18, 53, 19, shade(P["wood"], 0.72))
    for lx in (7, 44):
        rect(d, lx, 5, lx + 2, 24, P["metal"])
    rect(d, 6, 24, 12, 25, P["ink_soft"])
    rect(d, 44, 24, 50, 25, P["ink_soft"])
    finish(img, "bench")

    # Albero 64x88 (chioma 4 m, tronco 1,5 m)
    img, d = start(64, 88)
    contact(d, 8, 83, 56, 86)
    poly(d, [(28, 44), (35, 44), (37, 84), (26, 84)], P["brown"])
    rect(d, 34, 46, 36, 83, shade(P["brown"], 0.75))
    line(d, [(31, 62), (24, 52)], shade(P["brown"], 0.85), 2)
    line(d, [(33, 56), (41, 47)], shade(P["brown"], 0.85), 2)
    for cx, cy, r in ((32, 36, 20), (19, 43, 13), (45, 42, 14),
                      (32, 20, 14), (23, 27, 11), (42, 27, 12)):
        ellipse(d, cx - r, cy - r, cx + r, cy + r, shade(P["green_dark"], 0.95))
    for cx, cy, r in ((30, 34, 16), (19, 41, 10), (44, 40, 11), (32, 21, 11)):
        ellipse(d, cx - r, cy - r, cx + r, cy + r, P["green"])
    rng = seeded("tree_leaves")
    for _ in range(18):
        lx = rng.randint(12, 52)
        ly = rng.randint(12, 48)
        if (lx - 32) ** 2 + (ly - 32) ** 2 < 20 ** 2:
            rect(d, lx, ly, lx + 2, ly + 1, P["green_light"])
    finish(img, "tree")

    # Fioriera 32x20
    img, d = start(32, 20)
    contact(d, 2, 17, 30, 19)
    poly(d, [(5, 10), (27, 10), (25, 18), (7, 18)], shade(P["terra"], 0.90))
    rect(d, 2, 8, 30, 11, shade(P["terra"], 1.10))
    rect(d, 5, 9, 27, 10, shade(P["terra_dark"], 0.95))
    for fx, color in ((9, P["red"]), (16, P["yellow"]), (23, P["white"])):
        rect(d, fx, 5, fx, 10, P["green"])
        rect(d, fx - 2, 6, fx + 2, 6, P["green_dark"])
        ellipse(d, fx - 2, 3, fx + 2, 7, color)
    finish(img, "planter")

    # Segnale stradale 20x36
    img, d = start(20, 36)
    contact(d, 2, 33, 18, 35)
    rect(d, 9, 16, 11, 34, P["metal"])
    rect(d, 7, 33, 13, 35, P["ink_soft"])
    ellipse(d, 2, 2, 18, 18, P["white"])
    ellipse(d, 4, 4, 16, 16, P["eav_blue"])
    line(d, [(7, 14), (14, 6)], P["white"], 2)
    finish(img, "sign")

    # Semaforo 16x48
    img, d = start(16, 48)
    contact(d, 2, 45, 14, 47)
    rect(d, 7, 20, 9, 46, P["ink_soft"])
    rect(d, 5, 45, 11, 47, P["ink"])
    rect(d, 3, 3, 13, 26, P["ink"])
    for ly, color in ((5, P["red"]), (12, P["yellow"]), (19, P["green"])):
        rect(d, 4, ly, 12, ly + 1, shade(P["ink"], 1.45))
        ellipse(d, 5, ly + 1, 11, ly + 6, color)
    finish(img, "traffic_light")

    # Macchinetta EAV 20x40
    img, d = start(20, 40)
    contact(d, 2, 37, 18, 39)
    rect(d, 3, 3, 17, 38, P["eav_blue"])
    rect(d, 15, 3, 17, 38, shade(P["eav_blue"], 0.70))
    rect(d, 5, 5, 15, 18, P["white"])
    rect(d, 6, 7, 14, 16, P["glass"])
    rect(d, 6, 7, 14, 9, P["glass_light"])
    for ky in (20, 23, 26):
        rect(d, 6, ky, 7, ky + 1, P["yellow"])
        rect(d, 10, ky, 11, ky + 1, P["white"])
        rect(d, 14, ky, 15, ky + 1, P["white"])
    rect(d, 6, 29, 14, 31, P["ink"])
    tiny_text(d, 6, 33, "EAV", P["white"])
    rect(d, 4, 37, 16, 39, P["metal"])
    finish(img, "ticket_machine")

    # Cane 24x24
    img, d = start(24, 24)
    contact(d, 2, 20, 22, 23)
    line(d, [(6, 12), (3, 8), (2, 6)], shade(P["brown"], 0.90), 2)
    ellipse(d, 6, 9, 18, 18, shade(P["brown"], 1.05))
    rect(d, 7, 17, 9, 21, P["brown"])
    rect(d, 14, 17, 16, 21, P["brown"])
    ellipse(d, 15, 5, 22, 12, shade(P["brown"], 1.15))
    rect(d, 16, 3, 18, 6, shade(P["brown"], 0.75))
    rect(d, 20, 3, 22, 6, shade(P["brown"], 0.75))
    rect(d, 21, 9, 23, 11, shade(P["brown"], 0.90))
    rect(d, 19, 7, 19, 8, P["ink"])
    finish(img, "dog")

    # Gatto 20x18
    img, d = start(20, 18)
    contact(d, 2, 15, 18, 17)
    line(d, [(5, 12), (2, 9), (4, 6)], P["concrete"], 2)
    ellipse(d, 4, 6, 14, 15, P["concrete"])
    for sx in (6, 9, 12):
        rect(d, sx, 7, sx + 1, 8, shade(P["concrete"], 0.75))
    ellipse(d, 12, 3, 18, 10, shade(P["concrete"], 1.05))
    poly(d, [(12, 5), (13, 1), (15, 4)], shade(P["concrete"], 1.05))
    poly(d, [(16, 4), (18, 1), (18, 6)], shade(P["concrete"], 1.05))
    rect(d, 14, 6, 14, 7, P["yellow"])
    rect(d, 17, 6, 17, 7, P["yellow"])
    rect(d, 15, 8, 16, 8, P["white"])
    finish(img, "cat")

    # Pacco 24x20
    img, d = start(24, 20)
    contact(d, 3, 17, 21, 19)
    rect(d, 3, 5, 21, 17, P["brown"])
    poly(d, [(3, 5), (7, 2), (21, 2), (17, 5)], shade(P["brown"], 1.18))
    rect(d, 11, 2, 13, 17, P["concrete_light"])
    line(d, [(3, 5), (21, 5)], shade(P["brown"], 0.70), 1)
    rect(d, 15, 9, 19, 13, P["white"])
    rect(d, 16, 10, 18, 10, P["ink_soft"])
    rect(d, 16, 12, 18, 12, P["ink_soft"])
    finish(img, "parcel")

    # Chiavi 16x12
    img, d = start(16, 12)
    contact(d, 2, 10, 14, 11)
    ellipse(d, 2, 2, 7, 7, P["yellow"])
    ellipse(d, 4, 4, 5, 5, (0, 0, 0, 0))
    ellipse(d, 7, 4, 12, 9, shade(P["yellow"], 0.90))
    ellipse(d, 9, 6, 10, 7, (0, 0, 0, 0))
    rect(d, 11, 6, 15, 7, P["metal_light"])
    rect(d, 13, 8, 14, 9, P["metal_light"])
    rect(d, 15, 8, 15, 9, P["metal_light"])
    finish(img, "keys")

    # Caffe' 16x20
    img, d = start(16, 20)
    contact(d, 2, 17, 14, 19)
    line(d, [(6, 2), (6, 4)], P["white"], 1)
    line(d, [(10, 1), (10, 4)], P["white"], 1)
    poly(d, [(3, 7), (13, 7), (11, 18), (5, 18)], P["white"])
    ellipse(d, 12, 9, 16, 14, P["white"])
    ellipse(d, 13, 10, 14, 13, (0, 0, 0, 0))
    ellipse(d, 2, 5, 14, 9, P["white"])
    ellipse(d, 4, 6, 12, 8, P["brown"])
    rect(d, 5, 12, 11, 13, P["red"])
    finish(img, "coffee")

    # Biglietto 20x14
    img, d = start(20, 14)
    contact(d, 2, 12, 18, 13)
    rect(d, 2, 3, 18, 11, P["white"])
    rect(d, 2, 3, 18, 5, P["eav_blue"])
    for py in (6, 8, 10):
        rect(d, 13, py, 14, py, P["ink_soft"])
    tiny_text(d, 4, 6, "EAV", P["eav_blue"])
    finish(img, "ticket")


# ---------------------------------------------------------------------------
# Manifest: dimensioni lette dai file generati, metadati completi
# ---------------------------------------------------------------------------

# nome -> (w, h, tipo, origine_x, origine_y)
EXPECTED = {
    "player": (SHEET_W, SHEET_H, "character", FW / 2, FEET_Y),
    "resident": (SHEET_W, SHEET_H, "character", FW / 2, FEET_Y),
    "worker": (SHEET_W, SHEET_H, "character", FW / 2, FEET_Y),
    "elderly": (SHEET_W, SHEET_H, "character", FW / 2, FEET_Y),
    "teen": (SHEET_W, SHEET_H, "character", FW / 2, FEET_Y),
    "railway": (SHEET_W, SHEET_H, "character", FW / 2, FEET_Y),
    "vendor": (SHEET_W, SHEET_H, "character", FW / 2, FEET_Y),
    "car_red": (72, 40, "vehicle", 36, 30),
    "car_silver": (72, 40, "vehicle", 36, 30),
    "bus": (112, 44, "vehicle", 56, 33),
    "scooter": (52, 34, "vehicle", 26, 25),
    "train_eav": (576, 56, "vehicle", 288, 28),
    "lamp": (24, 76, "prop", 12, 74),
    "bin": (20, 26, "prop", 10, 24),
    "bench": (56, 26, "prop", 28, 24),
    "tree": (64, 88, "prop", 32, 84),
    "planter": (32, 20, "prop", 16, 18),
    "sign": (20, 36, "prop", 10, 34),
    "traffic_light": (16, 48, "prop", 8, 46),
    "ticket_machine": (20, 40, "prop", 10, 38),
    "dog": (24, 24, "prop", 12, 21),
    "cat": (20, 18, "prop", 10, 16),
    "parcel": (24, 20, "prop", 12, 18),
    "keys": (16, 12, "prop", 8, 10),
    "coffee": (16, 20, "prop", 8, 18),
    "ticket": (20, 14, "prop", 10, 12),
}


def write_manifest() -> None:
    sprites = {}
    for name, (w, h, kind, ox, oy) in EXPECTED.items():
        path = OUT / f"{name}.png"
        with Image.open(path) as im:
            actual = im.size
            nonempty = im.getbbox() is not None
        if actual != (w, h) or not nonempty:
            raise RuntimeError(f"asset non valido: {name} {actual} bbox={'no' if not nonempty else 'si'}")
        entry = {
            "name": name,
            "file": f"{name}.png",
            "w": w,
            "h": h,
            "type": kind,
            "pixel_per_metro": PPM,
            "origin_x": ox,
            "origin_y": oy,
        }
        if kind == "character":
            entry.update({
                "frame_w": FW,
                "frame_h": FH,
                "frames": SHEET_COLUMNS * SHEET_ROWS,
                "frames_per_direction": SHEET_COLUMNS,
                "directions": list(DIRECTIONS),
                "feet_y": FEET_Y,
            })
        sprites[name] = entry
    manifest = {
        "version": "0.3.0",
        "pixel_per_metro": PPM,
        "projection": "three_quarter_oblique",
        "frame_w": FW,
        "frame_h": FH,
        "feet_y": FEET_Y,
        "directions": list(DIRECTIONS),
        "frames_per_direction": SHEET_COLUMNS,
        "frames_per_character": SHEET_COLUMNS * SHEET_ROWS,
        "characters": list(CHARS),
        "sheet_w": SHEET_W,
        "sheet_h": SHEET_H,
        "sprites": sprites,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    make_characters()
    make_car("car_red", P["red"], dim(P["red"], 1.15), dim(P["red"], 0.78))
    make_car("car_silver", P["metal_light"], dim(P["metal_light"], 1.10),
             shade(P["metal"], 0.90))
    make_bus()
    make_scooter()
    make_train()
    make_props()
    write_manifest()
    total = sum(f.stat().st_size for f in OUT.glob("*.png"))
    print(f"OK {len(EXPECTED)} sprite ({total / 1e6:.2f} MB) — sheet {SHEET_W}x{SHEET_H}, 16 px/m")


if __name__ == "__main__":
    main()
