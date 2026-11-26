#!/usr/bin/env python3
"""Genera gli interni pixel art originali di NAPOLI LIFE (576x384, 48 px/m).

Proiezione obliqua "cabinet" a tre quarti: pavimento a griglia squadrata,
pareti posteriori a mattoni/piastrelle/intonaco, arredi costruiti come volumi
(fronte + faccia superiore + fianco) con ombre di contatto minime.

Niente anti-aliasing, gradienti morbidi, sfocature o dettagli sparsi a caso:
tutte le geometrie sono su griglia, i contorni sono scuri e coerenti e la
palette e' quella ristretta di artlib.py. Il seed e' sempre stabile.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw
from artlib import P, ellipse, line, rect, rgba, save_png, seeded, shade

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/assets/interiors"
W, H = 576, 384
PPM = 48
FLOOR_Y = 112
TILE = 48

INK = P["ink"]
EDGE = P["black"]
SOFT = P["ink_soft"]
SHADOW = None                          # impostato da room_base() sul colore del pavimento
HILITE = P["glass_light"]              # riflesso piatto e opaco, non gradiente


def S(color, factor, alpha=255):
    """Tinta piatta derivata dalla palette (nessun gradiente)."""
    if isinstance(color, str):
        return rgba(shade(color, factor), alpha)
    r, g, b = color[:3]                       # shade() di artlib accetta solo hex
    f = max(0.0, min(1.6, factor))
    return (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), alpha)


def poly(d, pts, fill, outline=EDGE, width=1):
    pts = [(int(x), int(y)) for x, y in pts]
    d.polygon(pts, fill=fill)
    if outline is not None:
        d.line(pts + [pts[0]], fill=outline, width=width)


def contact(d, cx, cy, rx, ry=4):
    ellipse(d, cx - rx, cy - ry, cx + rx, cy + ry, SHADOW)


def box(d, x, y, w, h, dep, front, top=None, side=None, outline=EDGE):
    """Volume a tre quarti. (x, y) e' l'angolo basso-sinistra del fronte.

    `dep` e' lo spostamento obliquo a 45 gradi del bordo posteriore.
    """
    top = S(front, 1.16) if top is None else top
    side = S(front, 0.76) if side is None else side
    poly(d, [(x + w, y - h), (x + w + dep, y - h - dep),
             (x + w + dep, y - dep), (x + w, y)], side, outline)
    poly(d, [(x, y - h), (x + dep, y - h - dep),
             (x + w + dep, y - h - dep), (x + w, y - h)], top, outline)
    rect(d, x, y - h, x + w, y, front, outline)


# --- bitmap font 5x7: testo nitido, nessun anti-aliasing --------------------
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x1F),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1E, 0x01, 0x01, 0x0E, 0x01, 0x01, 0x1E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x10, 0x1E, 0x01, 0x01, 0x1E),
    "6": (0x0C, 0x10, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x01, 0x0E),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    "-": (0, 0, 0, 0x1F, 0, 0, 0),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    ">": (0x10, 0x08, 0x04, 0x02, 0x04, 0x08, 0x10),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
}


def text(d, x, y, label, color, scale=1, space=1):
    cx = int(x)
    for ch in str(label).upper():
        glyph = FONT.get(ch, FONT["?"])
        for row, bits in enumerate(glyph):
            for col in range(5):
                if bits & (1 << (4 - col)):
                    rect(d, cx + col * scale, y + row * scale,
                         cx + (col + 1) * scale - 1, y + (row + 1) * scale - 1, color)
        cx += (5 + space) * scale


def text_w(label, scale=1, space=1):
    return len(label) * (5 + space) * scale - space * scale


def sign(d, x, y, w, label, bg, scale=1, fg=P["white"]):
    h = 11 * scale + 8
    rect(d, x, y, x + w, y + h, EDGE)
    rect(d, x + 2, y + 2, x + w - 2, y + h - 2, bg)
    rect(d, x + 3, y + 3, x + w - 3, y + 4, S(bg, 1.22))
    text(d, x + (w - text_w(label, scale)) // 2, y + 5, label, fg, scale)
    return h


# --- architettura della stanza ---------------------------------------------
def brick_wall(d, base, phase=0):
    rect(d, 0, 0, W, FLOOR_Y, base)
    y, row = 0, 0
    while y < FLOOR_Y:
        off = 16 if (row + phase) % 2 else 0
        idx = 0
        for x in range(-off, W, 32):
            c = base if (idx + row) % 2 == 0 else S(base, 0.94)
            rect(d, x + 1, y + 1, x + 31, y + 11, c)
            rect(d, x + 1, y + 1, x + 31, y + 2, S(c, 1.07))
            idx += 1
        rect(d, 0, y + 12, W, y + 12, S(base, 0.76))
        y += 12
        row += 1


def tile_wall(d, y0, y1, a, b, size=24, phase=0):
    rect(d, 0, y0, W, y1, S(b, 0.84))
    y, row = y0, 0
    while y < y1:
        for col, x in enumerate(range(0, W, size)):
            c = a if (col + row + phase) % 2 == 0 else b
            rect(d, x + 1, y + 1, x + size - 1, y + size - 1, c)
            rect(d, x + 1, y + 1, x + size - 2, y + 2, S(c, 1.08))
        y += size
        row += 1


def floor_grid(d, base, alt, phase=0):
    """Griglia quadrata allineata agli assi: 48 px = 1 m."""
    for row in range(0, 8):
        y0 = FLOOR_Y + row * TILE
        if y0 >= H:
            break
        yb = min(H - 1, y0 + TILE - 1)
        for col in range(12):
            x0 = col * TILE
            xb = min(W - 1, x0 + TILE - 1)
            c = base if (row + col + phase) % 2 == 0 else alt
            rect(d, x0, y0, xb, yb, c)
            rect(d, x0, y0, xb, y0, S(c, 1.07))
            rect(d, x0, y0, x0, yb, S(c, 1.07))
            rect(d, x0, yb, xb, yb, S(c, 0.87))
            rect(d, xb, y0, xb, yb, S(c, 0.87))
            if (row + col) % 3 == 0:
                rect(d, x0 + 22, y0 + 22, x0 + 25, y0 + 23, S(c, 0.80))


def baseboard(d, wall):
    rect(d, 0, FLOOR_Y - 6, W, FLOOR_Y - 1, S(wall, 0.72))
    rect(d, 0, FLOOR_Y - 6, W, FLOOR_Y - 5, S(wall, 1.12))
    rect(d, 0, FLOOR_Y - 1, W, FLOOR_Y, EDGE)
    rect(d, 0, FLOOR_Y, W, FLOOR_Y + 2, S(wall, 0.66))


def room_base(key, wall, floor, alt, pattern):
    global SHADOW
    SHADOW = S(floor, 0.82)            # ombra di contatto piatta, coerente col pavimento
    phase = seeded(key).randrange(2)  # seed stabile, solo phase di griglia
    img = Image.new("RGBA", (W, H), rgba(wall))
    d = ImageDraw.Draw(img, "RGBA")
    rect(d, 0, 0, W, FLOOR_Y, wall)
    if pattern == "block":
        brick_wall(d, wall, phase)
    elif pattern == "tile":
        tile_wall(d, 36, FLOOR_Y - 6, P["white"], P["concrete_light"], 24, phase)
        rect(d, 0, 32, W, 36, P["terra"], EDGE)
    elif pattern == "panel":
        for x in (18, 210, 402):
            rect(d, x, 14, x + 156, 86, S(wall, 0.94), S(wall, 0.80))
            rect(d, x + 5, 19, x + 151, 81, S(wall, 1.05), S(wall, 0.86))
    else:  # intonaco napoletano con fregio
        rect(d, 0, 10, W, 14, S(wall, 0.91), S(wall, 0.80))
        rect(d, 0, 18, W, 20, S(wall, 1.09))
        rect(d, 0, 94, W, 96, S(wall, 0.92))
    floor_grid(d, floor, alt, phase)
    baseboard(d, wall)
    return img, d


# --- arredi e dettagli ------------------------------------------------------
def window(d, x, y, w, h, cols=3):
    rect(d, x, y, x + w, y + h, EDGE)
    rect(d, x + 4, y + 4, x + w - 4, y + h - 4, P["glass"])
    inner = w - 8
    for c in range(cols):
        gx = x + 4 + (c * inner) // cols
        gw = inner // cols
        rect(d, gx + 2, y + 6, gx + gw - 2, y + h // 2 - 2, HILITE)
        if c:
            rect(d, gx, y + 4, gx, y + h - 4, EDGE)
    rect(d, x + 4, y + h // 2, x + w - 4, y + h // 2, EDGE)
    rect(d, x - 3, y + h, x + w + 3, y + h + 5, S(P["white"], 0.90), EDGE)


def curtains(d, x, y, w, h):
    rect(d, x - 8, y - 5, x + w + 8, y - 2, P["metal_light"], EDGE)
    for side in (0, 1):
        cx = x - 2 if side == 0 else x + w - 22
        rect(d, cx, y, cx + 24, y + h, P["white"], EDGE)
        for k in range(4):
            fold = S(P["white"], 0.86 if k % 2 else 0.98)
            rect(d, cx + 2 + k * 6, y + 2, cx + 4 + k * 6, y + h - 2, fold)


def pendant(d, x, color=P["yellow"]):
    rect(d, x - 1, 0, x + 1, 16, EDGE)
    poly(d, [(x - 12, 28), (x + 12, 28), (x + 7, 17), (x - 7, 17)],
         S(P["brown"], 1.05), EDGE)
    rect(d, x - 4, 28, x + 4, 33, color, EDGE)
    line(d, [(x - 12, 32), (x - 16, 36)], color, 1)
    line(d, [(x + 12, 32), (x + 16, 36)], color, 1)


def person(d, x, y, shirt, skin=P["skin2"], hair=P["hair1"], pants=None):
    """Persona 16x32 con i piedi in (x, y), coerente con lo sprite del giocatore."""
    pants = pants if pants is not None else S(P["ink_soft"], 1.15)
    contact(d, x, y + 1, 9, 3)
    rect(d, x - 6, y - 9, x - 2, y - 1, pants, EDGE)
    rect(d, x + 2, y - 9, x + 6, y - 1, pants, EDGE)
    rect(d, x - 7, y - 3, x - 2, y, EDGE)
    rect(d, x + 2, y - 3, x + 7, y, EDGE)
    rect(d, x - 8, y - 23, x + 8, y - 9, shirt, EDGE)
    rect(d, x - 11, y - 21, x - 8, y - 11, S(shirt, 0.82), EDGE)
    rect(d, x + 8, y - 21, x + 11, y - 11, S(shirt, 0.82), EDGE)
    rect(d, x - 10, y - 13, x - 8, y - 10, skin)
    rect(d, x + 8, y - 13, x + 10, y - 10, skin)
    rect(d, x - 2, y - 26, x + 2, y - 22, skin)
    rect(d, x - 6, y - 33, x + 6, y - 23, skin, EDGE)
    rect(d, x - 7, y - 35, x + 7, y - 30, hair, EDGE)
    rect(d, x - 7, y - 32, x - 5, y - 26, hair)
    rect(d, x - 3, y - 29, x - 2, y - 28, EDGE)
    rect(d, x + 2, y - 29, x + 3, y - 28, EDGE)


def bench(d, x, y, w=104):
    contact(d, x + w // 2 + 5, y + 3, w // 2, 4)
    rect(d, x + 10, y - 12, x + 15, y, P["metal"], EDGE)
    rect(d, x + w - 16, y - 12, x + w - 11, y, P["metal"], EDGE)
    box(d, x, y - 12, w, 12, 14, S(P["wood"], 0.86), P["wood"], S(P["wood"], 0.74))
    bx = x + 14
    rect(d, bx, y - 44, bx + w - 26, y - 14, S(P["wood"], 0.92), EDGE)
    for sx in range(bx + 4, bx + w - 30, 16):
        rect(d, sx, y - 42, sx + 6, y - 16, S(P["wood"], 1.12))
    rect(d, bx + 2, y - 16, bx + 6, y - 12, P["metal"], EDGE)
    rect(d, bx + w - 32, y - 16, bx + w - 28, y - 12, P["metal"], EDGE)


def cafe_table(d, cx, cy):
    contact(d, cx, cy + 4, 26, 4)
    rect(d, cx - 12, cy - 2, cx + 12, cy + 2, P["metal"], EDGE)
    rect(d, cx - 3, cy - 16, cx + 3, cy, P["metal"], EDGE)
    box(d, cx - 24, cy - 16, 48, 8, 14, P["wood"], S(P["wood"], 1.14), S(P["wood"], 0.80))
    rect(d, cx - 16, cy - 32, cx - 8, cy - 26, P["white"], EDGE)
    rect(d, cx - 6, cy - 30, cx + 2, cy - 24, P["white"], EDGE)
    rect(d, cx - 14, cy - 30, cx - 10, cy - 28, S(P["terra"], 1.05))


def chair(d, x, y):
    contact(d, x + 4, y + 2, 13, 3)
    rect(d, x - 9, y - 14, x - 6, y, P["metal"], EDGE)
    rect(d, x + 8, y - 14, x + 11, y, P["metal"], EDGE)
    box(d, x - 12, y - 14, 24, 8, 10, S(P["wood"], 0.92), P["wood"], S(P["wood"], 0.78))
    rect(d, x - 2, y - 40, x + 9, y - 22, S(P["wood"], 0.94), EDGE)
    rect(d, x, y - 38, x + 7, y - 24, S(P["wood"], 1.12))


def door_bottom(d, label="USCITA"):
    sign(d, 250, 310, 76, label, P["eav_blue"], 1)
    rect(d, 248, 336, 328, H - 1, EDGE)
    rect(d, 252, 340, 324, H - 1, S(P["wood"], 0.86))
    rect(d, 256, 344, 286, 378, P["glass"], EDGE)
    rect(d, 290, 344, 320, 378, P["glass"], EDGE)
    rect(d, 258, 346, 271, 360, HILITE)
    rect(d, 292, 346, 305, 360, HILITE)
    rect(d, 284, 358, 287, 365, P["yellow"], EDGE)
    rect(d, 289, 358, 292, 365, P["yellow"], EDGE)
    rect(d, 244, H - 12, 332, H - 1, S(P["ink_soft"], 1.2), EDGE)
    rect(d, 248, H - 9, 328, H - 4, S(P["brown"], 0.92))


def make_manifest(name, seed_spawn, colliders, interactables, door_y=374):
    return {
        "file": f"assets/interiors/{name}.png",
        "door": {"x": 288, "y": door_y, "target": "world", "spawn": seed_spawn},
        "interactables": interactables,
        "colliders": colliders,
    }


# --- 1. Stazione EAV --------------------------------------------------------
def station():
    img, d = room_base("station", P["concrete_light"], P["concrete"],
                       S(P["concrete"], 0.94), "block")

    # pilastri e vetrate della sala d'attesa
    for px in (0, 142, 426, 566):
        rect(d, px, 0, px + 10, FLOOR_Y - 6, S(P["concrete_light"], 0.90), EDGE)
    window(d, 18, 16, 116, 78, 3)
    window(d, 432, 16, 126, 78, 4)

    # insegna blu EAV
    sign(d, 244, 4, 88, "EAV", P["eav_blue"], 2)
    rect(d, 246, 32, 330, 34, P["yellow"])

    # banchino biglietti + addetto
    contact(d, 338, 110, 72, 5)
    rect(d, 276, 24, 400, 78, EDGE)
    rect(d, 279, 27, 397, 75, P["eav_blue"])
    rect(d, 282, 30, 394, 33, S(P["eav_blue"], 1.3))
    text(d, 284, 38, "EAV", P["white"], 2, 1)
    text(d, 282, 60, "BIGLIETTI", P["white"], 1, 0)
    rect(d, 304, 44, 348, 72, EDGE)
    rect(d, 307, 47, 345, 69, P["glass"])
    rect(d, 309, 49, 322, 59, HILITE)
    person(d, 326, 82, P["eav_blue"], P["skin2"], P["hair1"])
    box(d, 270, 108, 136, 30, 16, P["eav_blue"], P["eav_light"], S(P["eav_blue"], 0.78))
    rect(d, 274, 84, 402, 88, S(P["eav_light"], 0.86), EDGE)
    rect(d, 330, 94, 356, 100, EDGE)
    rect(d, 333, 96, 353, 98, P["yellow"])
    for kx in (286, 300, 314):
        rect(d, kx, 94, kx + 7, 101, P["ink"], EDGE)

    # tabellone partenze su piedistallo
    contact(d, 206, 174, 58, 4)
    box(d, 150, 164, 112, 48, 10, S(SOFT, 1.05), S(SOFT, 1.28), S(SOFT, 0.78))
    rect(d, 156, 120, 258, 160, EDGE)
    rect(d, 159, 123, 255, 157, S(P["green_dark"], 1.45))
    rect(d, 159, 123, 255, 131, P["eav_blue"])
    text(d, 176, 125, "PARTENZE", P["yellow"], 1, 0)
    for i, row in enumerate(("06:12 TORREGAVETA", "06:40 NAPOLI", "07:05 TORREGAVETA")):
        text(d, 162, 135 + i * 7, row, P["white"], 1, 0)
    rect(d, 160, 164, 166, 174, P["metal"], EDGE)
    rect(d, 246, 164, 252, 174, P["metal"], EDGE)

    # panchine simmetriche e due viaggiatori intenzionalmente posizionati
    bench(d, 52, 284, 104)
    bench(d, 420, 284, 104)
    person(d, 194, 232, P["terra"], P["skin1"], P["hair2"])
    person(d, 404, 250, P["green_dark"], P["skin3"], P["hair1"])
    rect(d, 516, 224, 548, 274, P["metal"], EDGE)
    rect(d, 520, 228, 544, 250, P["glass"], EDGE)
    rect(d, 524, 230, 532, 240, HILITE)
    line(d, [(532, 252), (532, 270)], P["yellow"], 2)

    door_bottom(d)
    save_png(img, OUT / "station.png")
    return make_manifest(
        "station", [0, -5.2],
        [[270, 20, 406, 92], [150, 108, 262, 172]],
        [
            {"id": "ticket_clerk", "name": "Addetto EAV", "x": 348, "y": 76, "kind": "ticket"},
            {"id": "timetable", "name": "Tabellone partenze", "x": 206, "y": 140, "kind": "read"},
            {"id": "station_exit", "name": "Uscita", "x": 288, "y": 370, "kind": "exit"},
        ],
        370,
    )


# --- 2. Bar napoletano ------------------------------------------------------
def bar():
    img, d = room_base("bar", P["stucco_cream"], P["stucco_ochre"],
                       S(P["stucco_ochre"], 0.95), "tile")

    sign(d, 36, 8, 120, "BAR", P["terra"], 2)
    sign(d, 172, 16, 158, "CAFFE NAPOLI", P["brown"], 1)
    pendant(d, 148)
    pendant(d, 430)

    # barista dietro il bancone
    person(d, 164, 166, P["white"], P["skin2"], P["hair1"])

    # bancone in legno con vista a tre quarti
    contact(d, 172, 262, 146, 5)
    box(d, 20, 258, 284, 88, 18, P["brown"], S(P["wood"], 1.12), S(P["brown"], 0.76))
    for sx in range(28, 304, 24):
        rect(d, sx, 176, sx + 2, 252, S(P["brown"], 0.72))
    rect(d, 28, 244, 296, 249, P["metal_light"], EDGE)
    rect(d, 28, 252, 296, 254, S(P["brown"], 0.62))

    # macchina espresso professionale (a destra del barista, non davanti a lui)
    box(d, 216, 152, 66, 26, 12, P["metal_light"], S(P["metal_light"], 1.12), P["metal"])
    rect(d, 220, 130, 278, 149, P["ink"])
    rect(d, 223, 133, 275, 140, S(P["metal_light"], 0.92))
    for gx in (230, 248, 266):
        rect(d, gx, 141, gx + 8, 147, P["metal_light"], EDGE)
        rect(d, gx + 2, 147, gx + 6, 151, P["yellow"])
    line(d, [(282, 138), (288, 144), (288, 152)], P["metal_light"], 2)
    for cx in (226, 242, 260):
        rect(d, cx, 120, cx + 10, 126, P["white"], EDGE)
        rect(d, cx + 2, 118, cx + 8, 120, S(P["terra"], 1.05))
    rect(d, 292, 136, 308, 152, P["ink"], EDGE)
    rect(d, 295, 139, 305, 148, S(P["terra"], 0.85))

    # tazzine sul bancone
    for cx in (52, 82, 110, 288):
        rect(d, cx, 154, cx + 14, 160, P["white"], EDGE)
        rect(d, cx + 3, 150, cx + 11, 154, S(P["terra"], 1.05))

    # vetrina dei dolci
    contact(d, 392, 246, 76, 4)
    box(d, 318, 242, 148, 80, 14, P["ink"], S(P["ink"], 1.28), S(P["ink"], 0.80))
    rect(d, 322, 166, 462, 238, P["ink"])
    for sy in (196, 222):
        rect(d, 324, sy, 460, sy + 2, P["metal_light"])
    for i in range(5):
        px = 330 + i * 26
        c1 = (P["terra"], P["yellow"], P["white"], P["brown"], P["stucco_pink"])[i]
        ellipse(d, px, 184, px + 18, 195, c1, EDGE)
        ellipse(d, px + 4, 181, px + 14, 188, S(c1, 1.14))
        c2 = (P["yellow"], P["terra"], P["brown"], P["white"], P["stucco_pink"])[i]
        ellipse(d, px, 210, px + 18, 221, c2, EDGE)
        ellipse(d, px + 4, 207, px + 14, 214, S(c2, 1.14))
    rect(d, 328, 168, 338, 236, S(P["white"], 0.94))
    rect(d, 444, 168, 450, 236, S(P["white"], 0.94))
    rect(d, 322, 166, 462, 170, S(P["ink"], 1.5))
    for mx in (388, 454):
        rect(d, mx, 166, mx + 2, 238, P["ink"])

    # frigo delle bevande
    contact(d, 514, 262, 40, 4)
    box(d, 476, 260, 76, 132, 12, P["white"], P["concrete_light"], S(P["white"], 0.78))
    rect(d, 482, 136, 546, 190, S(P["glass"], 0.85), EDGE)
    rect(d, 482, 198, 546, 252, S(P["glass"], 0.85), EDGE)
    for by in (148, 170, 210, 232):
        for bx in (488, 506, 524):
            bc = (P["red"], P["green"], P["yellow"], P["eav_blue"])[(bx + by) // 18 % 4]
            rect(d, bx, by, bx + 8, by + 14, bc, EDGE)
            rect(d, bx + 2, by + 2, bx + 4, by + 5, S(bc, 1.25))
    rect(d, 540, 162, 544, 182, P["metal_light"], EDGE)

    # tavolini, sedie e clienti
    cafe_table(d, 110, 322)
    chair(d, 60, 336)
    chair(d, 158, 338)
    person(d, 72, 318, P["eav_blue"], P["skin1"], P["hair2"])
    cafe_table(d, 352, 324)
    chair(d, 302, 338)
    chair(d, 400, 338)
    person(d, 398, 320, P["terra"], P["skin3"], P["hair3"])

    door_bottom(d)
    save_png(img, OUT / "bar.png")
    return make_manifest(
        "bar", [-17, -56.0],
        [[20, 162, 304, 260], [318, 158, 466, 242], [476, 122, 552, 260]],
        [
            {"id": "barista", "name": "Barista", "x": 164, "y": 120, "kind": "barista"},
            {"id": "pastries", "name": "Vetrina dolci", "x": 394, "y": 200, "kind": "buy_food"},
            {"id": "bar_exit", "name": "Esci dal bar", "x": 288, "y": 374, "kind": "exit"},
        ],
    )


# --- 3. Negozio -------------------------------------------------------------
def shop():
    img, d = room_base("shop", P["stucco_green"], P["concrete_light"],
                       S(P["concrete_light"], 0.94), "panel")
    sign(d, 224, 6, 128, "NEGOZIO", P["green_dark"], 1)

    # due scaffalature regolari
    for base_x in (34, 122):
        contact(d, base_x + 42, 242, 43, 4)
        box(d, base_x, 238, 84, 122, 14, S(P["wood"], 0.92),
            S(P["wood"], 1.08), S(P["wood"], 0.74))
        for sy in (150, 180, 210):
            rect(d, base_x + 2, sy, base_x + 82, sy + 2, S(P["wood"], 1.18))
            for i in range(6):
                bx = base_x + 6 + i * 13
                pc = (P["red"], P["yellow"], P["green"], P["eav_blue"],
                      P["white"], P["terra"])[(i + sy // 30) % 6]
                rect(d, bx, sy - 16, bx + 9, sy, pc, EDGE)
                rect(d, bx + 2, sy - 14, bx + 4, sy - 10, S(pc, 1.22))
        rect(d, base_x + 4, 232, base_x + 80, 236, S(P["wood"], 0.72))

    # scaffale stretto laterale
    contact(d, 276, 260, 26, 4)
    box(d, 250, 258, 50, 130, 12, S(P["wood"], 0.88), P["wood"], S(P["wood"], 0.72))
    for sy in (152, 180, 208, 236):
        rect(d, 252, sy, 298, sy + 2, S(P["wood"], 1.18))
        for i in range(3):
            bx = 254 + i * 15
            pc = (P["white"], P["red"], P["yellow"])[(sy + i * 10) // 28 % 3]
            rect(d, bx, sy - 15, bx + 11, sy, pc, EDGE)

    # commerciante dietro il banco
    person(d, 400, 196, S(P["stucco_yellow"], 0.92), P["skin2"], P["hair2"])

    # banco cassa
    contact(d, 402, 266, 70, 4)
    box(d, 330, 262, 140, 70, 14, P["wood"], S(P["wood"], 1.14), S(P["wood"], 0.76))
    for sx in range(340, 470, 26):
        rect(d, sx, 200, sx + 2, 258, S(P["wood"], 0.74))
    box(d, 344, 200, 42, 14, 8, P["metal_light"], S(P["metal_light"], 1.1), P["metal"])
    rect(d, 348, 182, 382, 198, EDGE)
    rect(d, 351, 185, 379, 195, P["glass"])
    text(d, 352, 187, "CASSA", P["yellow"], 1, 0)
    for kx in (390, 404, 418):
        rect(d, kx, 190, kx + 8, 198, P["metal_light"], EDGE)
    rect(d, 446, 196, 462, 200, P["yellow"], EDGE)

    # frigo a destra
    contact(d, 518, 270, 34, 4)
    box(d, 486, 268, 64, 128, 12, P["white"], P["concrete_light"], S(P["white"], 0.78))
    rect(d, 492, 148, 544, 200, S(P["glass"], 0.88), EDGE)
    rect(d, 492, 210, 544, 262, S(P["glass"], 0.85), EDGE)
    for by in (158, 180, 220, 242):
        for bx in (498, 516):
            pc = (P["red"], P["green"], P["yellow"])[(bx + by) // 20 % 3]
            rect(d, bx, by, bx + 10, by + 14, pc, EDGE)
    rect(d, 538, 172, 542, 194, P["metal_light"], EDGE)

    door_bottom(d)
    save_png(img, OUT / "shop.png")
    return make_manifest(
        "shop", [3.7, -59.0],
        [[30, 108, 210, 242], [250, 120, 300, 260],
         [330, 188, 470, 264], [486, 140, 550, 268]],
        [
            {"id": "shopkeeper", "name": "Commerciante", "x": 400, "y": 186, "kind": "shop"},
            {"id": "shop_exit", "name": "Esci dal negozio", "x": 288, "y": 374, "kind": "exit"},
        ],
    )


# --- 4. Casa ----------------------------------------------------------------
def home():
    img, d = room_base("home", P["stucco_cream"], S(P["wood"], 0.92),
                       S(P["wood"], 0.86), "plain")

    # finestra con tende
    window(d, 40, 24, 136, 76, 3)
    curtains(d, 40, 24, 136, 80)
    poly(d, [(52, 120), (164, 120), (196, 216), (20, 216)],
         S(S(P["wood"], 0.92), 1.12), None)

    # lampada a soffitto
    pendant(d, 300, P["yellow"])

    # letto a tre quarti
    contact(d, 104, 332, 72, 5)
    box(d, 30, 328, 140, 22, 16, S(P["wood"], 0.88), P["wood"], S(P["wood"], 0.74))
    rect(d, 46, 268, 62, 306, S(P["wood"], 0.82), EDGE)
    rect(d, 30, 244, 62, 306, S(P["wood"], 0.90), EDGE)
    rect(d, 34, 248, 58, 302, S(P["wood"], 1.12))
    rect(d, 62, 252, 164, 300, P["white"], EDGE)
    rect(d, 62, 276, 164, 300, S(P["eav_light"], 0.86), EDGE)
    rect(d, 66, 280, 160, 284, S(P["eav_light"], 1.12))
    rect(d, 68, 256, 102, 270, S(P["white"], 0.94), EDGE)
    rect(d, 106, 256, 140, 270, S(P["white"], 0.94), EDGE)
    rect(d, 32, 322, 168, 326, S(P["wood"], 1.16))

    # cucina: pensili, backsplash e basi
    for cx in (240, 330):
        box(d, cx, 110, 76, 50, 12, S(P["wood"], 0.92),
            S(P["wood"], 1.08), S(P["wood"], 0.76))
        rect(d, cx + 34, 68, cx + 42, 84, P["metal_light"], EDGE)
    tile_wall(d, 112, 166, P["white"], P["concrete_light"], 16, 0)
    contact(d, 326, 268, 96, 4)
    box(d, 230, 264, 190, 94, 14, S(P["wood"], 0.90), S(P["concrete_light"], 1.02),
        S(P["wood"], 0.74))
    for sx in range(240, 420, 32):
        rect(d, sx, 176, sx + 2, 260, S(P["wood"], 0.70))
        rect(d, sx + 12, 206, sx + 22, 210, P["metal_light"], EDGE)
    rect(d, 250, 160, 288, 174, P["metal_light"], EDGE)
    rect(d, 256, 164, 282, 170, P["glass"], EDGE)
    line(d, [(269, 166), (269, 172)], P["metal"], 2)
    rect(d, 296, 158, 324, 174, P["ink"], EDGE)
    for bx in (302, 314):
        rect(d, bx, 162, bx + 6, 168, P["metal_light"])
    rect(d, 340, 154, 400, 174, P["terra"], EDGE)
    rect(d, 344, 158, 396, 170, S(P["terra"], 1.18))

    # TV e mobiletto
    contact(d, 512, 248, 38, 4)
    box(d, 474, 244, 76, 56, 12, S(P["ink_soft"], 1.1), S(P["ink_soft"], 1.3),
        S(P["ink_soft"], 0.8))
    rect(d, 480, 196, 544, 236, P["ink"], EDGE)
    rect(d, 484, 200, 540, 232, P["glass"], EDGE)
    rect(d, 488, 204, 508, 220, HILITE)
    rect(d, 506, 244, 518, 250, P["metal_light"], EDGE)

    # tappeto, tavolo, sedia e pianta in angolo
    rect(d, 208, 288, 388, 356, S(P["terra"], 1.15), EDGE)
    rect(d, 216, 296, 380, 348, S(P["terra"], 0.92), S(P["white"], 0.88))
    rect(d, 224, 304, 372, 340, S(P["terra"], 1.08))
    cafe_table(d, 300, 320)
    chair(d, 246, 336)
    contact(d, 70, 226, 16, 4)
    rect(d, 58, 206, 82, 226, P["terra"], EDGE)
    rect(d, 56, 204, 84, 208, S(P["terra"], 1.18), EDGE)
    for px, py in ((70, 194), (58, 198), (82, 198), (66, 184), (76, 186)):
        ellipse(d, px - 9, py - 9, px + 9, py + 9, P["green"], EDGE)

    door_bottom(d)
    save_png(img, OUT / "home.png")
    return make_manifest(
        "home", [-0.75, 100.2],
        [[30, 226, 170, 330], [230, 150, 420, 268], [470, 180, 552, 246]],
        [
            {"id": "bed", "name": "Letto (riposa)", "x": 100, "y": 280, "kind": "sleep"},
            {"id": "home_exit", "name": "Esci di casa", "x": 288, "y": 374, "kind": "exit"},
        ],
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rooms = {
        "station": station(),
        "bar": bar(),
        "shop": shop(),
        "home": home(),
    }
    for name, data in rooms.items():
        data["name"] = name
        data["size_px"] = [W, H]
        data["scale_ppm"] = PPM
    (OUT / "manifest.json").write_text(
        json.dumps(rooms, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OK 4 interni pixel art (576x384 @ 48 px/m)")


if __name__ == "__main__":
    main()
