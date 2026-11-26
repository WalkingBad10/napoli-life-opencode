#!/usr/bin/env python3
"""Genera gli interni pixel art originali di NAPOLI LIFE (576x384, 48 px/m).

Proiezione obliqua "cabinet" a tre quarti: pavimento a piastrelle regolari,
pareti piastrellate/intonicate, arredi costruiti come volumi (fronte + faccia
superiore + fianco) con ombre di contatto piatte e minime.

Niente anti-aliasing, gradienti, sfocature o texture casuali: ogni dettaglio e'
disegnato su coordinate intere, con la palette ristretta di artlib.py e con
varianti di luminosita' calcolate da shade()/S(). Tutto e' deterministico.
"""

from __future__ import annotations

import json
import math
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
    """Mattoni regolari a corsie sfalsate, senza texture casuale."""
    rect(d, 0, 0, W, FLOOR_Y, base)
    y, row = 0, 0
    while y < FLOOR_Y:
        off = 16 if (row + phase) % 2 else 0
        idx = 0
        for x in range(-off, W, 32):
            c = base if (idx + row) % 2 == 0 else S(base, 0.94)
            rect(d, x + 1, y + 1, x + 31, y + 11, c)
            rect(d, x + 1, y + 1, x + 31, y + 2, S(c, 1.06))
            rect(d, x + 1, y + 10, x + 31, y + 11, S(c, 0.90))
            idx += 1
        rect(d, 0, y + 12, W, y + 12, S(base, 0.76))
        y += 12
        row += 1


def tile_wall(d, y0, y1, a, b, size=16, phase=0):
    """Rivestimento a piastrelle quadre con giunto regolare."""
    rect(d, 0, y0, W, y1, S(b, 0.84))
    y, row = y0, 0
    while y < y1:
        for col, x in enumerate(range(0, W, size)):
            c = a if (col + row + phase) % 2 == 0 else b
            rect(d, x + 1, y + 1, x + size - 1, y + size - 1, c)
            rect(d, x + 1, y + 1, x + size - 2, y + 2, S(c, 1.07))
            rect(d, x + 1, y + size - 2, x + size - 1, y + size - 1, S(c, 0.90))
        y += size
        row += 1


def panel_wall(d, wall):
    """Pannelli regolari in legno/intonaco del negozio."""
    for x in (18, 210, 402):
        rect(d, x, 14, x + 156, 86, S(wall, 0.94), S(wall, 0.80))
        rect(d, x + 5, 19, x + 151, 81, S(wall, 1.05), S(wall, 0.86))
        rect(d, x + 8, 22, x + 148, 78, S(wall, 0.98))
        for px in (x + 14, x + 142):
            rect(d, px, 44, px + 4, 56, S(P["wood"], 0.92), EDGE)


def greca(d, x0, y0, x1, y1, color):
    """Fregio a greca squadrata: modulo fisso di 16 px, nessun caso."""
    rect(d, x0, y0, x1, y0, color)
    rect(d, x0, y1, x1, y1, color)
    x = x0 + 2
    while x + 15 <= x1 - 2:
        rect(d, x, y0 + 2, x + 14, y0 + 3, color)
        rect(d, x + 2, y0 + 3, x + 2, y1 - 2, color)
        rect(d, x + 2, y1 - 2, x + 12, y1 - 2, color)
        rect(d, x + 12, y0 + 5, x + 12, y1 - 2, color)
        rect(d, x + 7, y0 + 5, x + 12, y0 + 5, color)
        rect(d, x + 7, y0 + 5, x + 7, y0 + 8, color)
        x += 16


def floor_tiles(d, base, alt, size=24, accent=None, phase=0):
    """Piastrelle regolari da 0,5 m (24 px a 48 px/m), con giunto dritto."""
    rows = (H - FLOOR_Y + size - 1) // size
    cols = (W + size - 1) // size
    for r in range(rows):
        y0 = FLOOR_Y + r * size
        yb = min(H - 1, y0 + size - 1)
        for c in range(cols):
            x0, xb = c * size, min(W - 1, c * size + size - 1)
            tone = base if (r + c + phase) % 2 == 0 else alt
            rect(d, x0, y0, xb, yb, tone)
            rect(d, x0, y0, xb, y0, S(tone, 1.06))
            rect(d, x0, y0, x0, yb, S(tone, 1.03))
            rect(d, x0, yb, xb, yb, S(tone, 0.89))
            rect(d, xb, y0, xb, yb, S(tone, 0.89))
            if accent is not None and (r + c + phase) % 4 == 0:
                rect(d, x0 + 4, y0 + 4, x0 + 7, y0 + 5, accent)


def floor_planks(d, base, alt):
    """Assi di legno regolari, sfalsate a coppie (casa)."""
    pw, ph = 96, 16
    for r in range((H - FLOOR_Y + ph - 1) // ph):
        y0 = FLOOR_Y + r * ph
        yb = min(H - 1, y0 + ph - 1)
        shift = pw // 2 if r % 2 else 0
        for c, x0 in enumerate(range(-shift, W, pw)):
            tone = base if (c + r) % 2 == 0 else alt
            xa, xb = max(0, x0), min(W - 1, x0 + pw - 1)
            rect(d, xa, y0, xb, yb, tone)
            rect(d, xa, y0, xb, y0, S(tone, 1.05))
            rect(d, xa, yb, xb, yb, S(tone, 0.88))
            if xa > 0:
                rect(d, xa, y0, xa, yb, S(tone, 0.84))


def baseboard(d, wall):
    rect(d, 0, FLOOR_Y - 6, W, FLOOR_Y - 1, S(wall, 0.72))
    rect(d, 0, FLOOR_Y - 6, W, FLOOR_Y - 5, S(wall, 1.12))
    rect(d, 0, FLOOR_Y - 1, W, FLOOR_Y, EDGE)
    rect(d, 0, FLOOR_Y, W, FLOOR_Y + 2, S(wall, 0.66))


def room_base(key, wall, floor, alt, pattern):
    global SHADOW
    SHADOW = S(floor, 0.88, 96)        # ombra di contatto piatta e leggera
    phase = seeded(key).randrange(2)  # seed stabile, solo fase della griglia
    img = Image.new("RGBA", (W, H), rgba(wall))
    d = ImageDraw.Draw(img, "RGBA")
    rect(d, 0, 0, W, FLOOR_Y, wall)
    if pattern == "block":
        brick_wall(d, wall, phase)
    elif pattern == "tile":
        tile_wall(d, 36, FLOOR_Y - 6, P["white"], P["concrete_light"], 16, phase)
        rect(d, 0, 32, W, 36, P["terra"], EDGE)
        greca(d, 0, 4, W, 18, S(P["terra_dark"], 1.05))
    elif pattern == "panel":
        panel_wall(d, wall)
    else:  # intonaco napoletano con fregio
        rect(d, 0, 10, W, 14, S(wall, 0.91), S(wall, 0.80))
        rect(d, 0, 18, W, 20, S(wall, 1.09))
        rect(d, 0, 94, W, 96, S(wall, 0.92))
        greca(d, 0, 22, W, 34, S(P["terra"], 0.92))
    if pattern == "plain":
        floor_planks(d, floor, alt)
    else:
        floor_tiles(d, floor, alt, 24,
                    S(alt, 0.92) if pattern != "block" else None, phase)
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
        rect(d, gx + 2, y + h // 2 + 3, gx + gw - 3, y + h - 6, S(P["glass"], 0.86))
        if c:
            rect(d, gx, y + 4, gx, y + h - 4, EDGE)
    rect(d, x + 4, y + h // 2, x + w - 4, y + h // 2 + 1, EDGE)
    rect(d, x - 4, y + h, x + w + 4, y + h + 5, S(P["white"], 0.94), EDGE)
    rect(d, x - 2, y + h + 6, x + w + 2, y + h + 7, S(P["white"], 0.82))


def curtains(d, x, y, w, h):
    rect(d, x - 8, y - 5, x + w + 8, y - 2, P["metal_light"], EDGE)
    for side in (0, 1):
        cx = x - 2 if side == 0 else x + w - 22
        rect(d, cx, y, cx + 24, y + h, P["white"], EDGE)
        for k in range(4):
            fold = S(P["white"], 0.86 if k % 2 else 0.98)
            rect(d, cx + 2 + k * 6, y + 2, cx + 4 + k * 6, y + h - 2, fold)
        rect(d, cx, y + h - 4, cx + 24, y + h, S(P["terra"], 0.92))


def pendant(d, x, color=P["yellow"]):
    """Lampada a pendaglio: catena, paralume e riflesso piatto, senza sfumature."""
    rect(d, x - 3, 0, x + 3, 2, P["metal"], EDGE)
    rect(d, x - 1, 2, x + 1, 15, EDGE)
    poly(d, [(x - 13, 28), (x + 13, 28), (x + 7, 16), (x - 7, 16)],
         S(P["brown"], 1.05), EDGE)
    rect(d, x - 11, 27, x + 11, 29, S(P["wood"], 1.18))
    rect(d, x - 4, 29, x + 4, 33, color, EDGE)
    line(d, [(x - 12, 30), (x - 17, 34)], color, 1)
    line(d, [(x + 12, 30), (x + 17, 34)], color, 1)
    line(d, [(x, 34), (x, 38)], color, 1)


def person(d, x, y, shirt, skin=P["skin2"], hair=P["hair1"], pants=None,
           apron=None, cap=None):
    """Persona esattamente 16x32 px, piedi in (x, y): come lo sprite del mondo."""
    pants = pants if pants is not None else S(P["ink_soft"], 1.15)
    contact(d, x, y + 1, 8, 3)
    rect(d, x - 6, y - 10, x - 2, y - 2, pants, EDGE)
    rect(d, x + 2, y - 10, x + 6, y - 2, pants, EDGE)
    rect(d, x - 7, y - 3, x - 2, y, EDGE)
    rect(d, x + 2, y - 3, x + 7, y, EDGE)
    rect(d, x - 7, y - 22, x + 5, y - 10, shirt, EDGE)
    rect(d, x - 8, y - 20, x - 6, y - 12, S(shirt, 0.82), EDGE)
    rect(d, x + 5, y - 20, x + 7, y - 12, S(shirt, 0.82), EDGE)
    rect(d, x - 8, y - 13, x - 6, y - 10, skin)
    rect(d, x + 5, y - 13, x + 7, y - 10, skin)
    if apron is not None:
        rect(d, x - 5, y - 19, x + 4, y - 10, apron, EDGE)
        rect(d, x - 4, y - 21, x - 3, y - 18, apron)
        rect(d, x + 2, y - 21, x + 3, y - 18, apron)
        rect(d, x - 4, y - 14, x + 3, y - 13, S(apron, 0.86))
    rect(d, x - 2, y - 24, x + 2, y - 21, skin)
    rect(d, x - 5, y - 30, x + 3, y - 23, skin, EDGE)
    rect(d, x - 6, y - 31, x + 4, y - 28, hair, EDGE)
    rect(d, x - 6, y - 30, x - 5, y - 25, hair)
    rect(d, x - 4, y - 27, x - 3, y - 26, EDGE)
    rect(d, x + 1, y - 27, x + 2, y - 26, EDGE)
    if cap is not None:
        rect(d, x - 6, y - 31, x + 4, y - 29, cap, EDGE)
        rect(d, x - 7, y - 29, x + 6, y - 28, cap, EDGE)


def seated_person(d, x, y, shirt, skin=P["skin2"], hair=P["hair1"], pants=None):
    """Cliente seduto: stessa altezza 32 px, gambe piegate e piedi a terra."""
    pants = pants if pants is not None else S(P["ink_soft"], 1.15)
    contact(d, x, y + 1, 8, 3)
    rect(d, x - 6, y - 9, x - 2, y - 2, pants, EDGE)
    rect(d, x + 2, y - 9, x + 6, y - 2, pants, EDGE)
    rect(d, x - 7, y - 3, x - 2, y, EDGE)
    rect(d, x + 2, y - 3, x + 7, y, EDGE)
    rect(d, x - 7, y - 15, x + 5, y - 9, pants, EDGE)
    rect(d, x - 7, y - 23, x + 5, y - 14, shirt, EDGE)
    rect(d, x - 8, y - 21, x - 6, y - 15, S(shirt, 0.82), EDGE)
    rect(d, x + 5, y - 21, x + 7, y - 15, S(shirt, 0.82), EDGE)
    rect(d, x - 2, y - 24, x + 2, y - 21, skin)
    rect(d, x - 5, y - 30, x + 3, y - 23, skin, EDGE)
    rect(d, x - 6, y - 31, x + 4, y - 28, hair, EDGE)
    rect(d, x - 4, y - 27, x - 3, y - 26, EDGE)
    rect(d, x + 1, y - 27, x + 2, y - 26, EDGE)


def bench(d, x, y, w=104):
    contact(d, x + w // 2 + 5, y + 3, w // 2, 4)
    rect(d, x + 10, y - 12, x + 15, y, P["metal"], EDGE)
    rect(d, x + w - 16, y - 12, x + w - 11, y, P["metal"], EDGE)
    box(d, x, y - 12, w, 12, 14, S(P["wood"], 0.86), P["wood"], S(P["wood"], 0.74))
    bx = x + 14
    rect(d, bx, y - 44, bx + w - 26, y - 14, S(P["wood"], 0.92), EDGE)
    for sx in range(bx + 4, bx + w - 30, 16):
        rect(d, sx, y - 42, sx + 6, y - 16, S(P["wood"], 1.12))
    rect(d, bx + 2, y - 42, bx + w - 28, y - 39, S(P["wood"], 1.16))
    rect(d, bx + 2, y - 20, bx + w - 28, y - 18, S(P["wood"], 1.12))
    rect(d, bx + 2, y - 16, bx + 6, y - 12, P["metal"], EDGE)
    rect(d, bx + w - 32, y - 16, bx + w - 28, y - 12, P["metal"], EDGE)


def cafe_table(d, cx, cy):
    contact(d, cx, cy + 4, 26, 4)
    rect(d, cx - 12, cy - 2, cx + 12, cy + 2, P["metal"], EDGE)
    rect(d, cx - 3, cy - 16, cx + 3, cy, P["metal"], EDGE)
    poly(d, [(cx - 24, cy - 14), (cx - 10, cy - 28),
             (cx + 38, cy - 28), (cx + 24, cy - 14)], S(P["white"], 0.94), EDGE)
    rect(d, cx - 23, cy - 14, cx + 24, cy - 8, P["white"], EDGE)
    rect(d, cx - 21, cy - 13, cx + 22, cy - 11, S(P["concrete_light"], 0.96))
    cup(d, cx - 10, cy - 8)
    cup(d, cx + 12, cy - 8)


def chair(d, x, y):
    contact(d, x + 4, y + 2, 13, 3)
    rect(d, x - 9, y - 14, x - 6, y, P["metal"], EDGE)
    rect(d, x + 8, y - 14, x + 11, y, P["metal"], EDGE)
    box(d, x - 12, y - 14, 24, 8, 10, S(P["wood"], 0.92), P["wood"], S(P["wood"], 0.78))
    rect(d, x - 2, y - 34, x + 9, y - 20, S(P["wood"], 0.94), EDGE)
    rect(d, x, y - 32, x + 7, y - 22, S(P["wood"], 1.12))


def cup(d, cx, cy, saucer=True):
    if saucer:
        ellipse(d, cx - 10, cy - 2, cx + 10, cy + 2, S(P["white"], 0.92), EDGE)
    rect(d, cx - 6, cy - 7, cx + 5, cy - 1, P["white"], EDGE)
    rect(d, cx - 4, cy - 6, cx + 3, cy - 4, S(P["terra"], 0.88))
    ellipse(d, cx + 5, cy - 6, cx + 9, cy - 2, None, EDGE)


def sugar_bowl(d, cx, cy):
    ellipse(d, cx - 11, cy - 4, cx + 11, cy, P["white"], EDGE)
    rect(d, cx - 9, cy - 8, cx + 9, cy - 4, P["white"], EDGE)
    ellipse(d, cx - 5, cy - 10, cx + 5, cy - 7, S(P["metal_light"], 1.05), EDGE)
    rect(d, cx - 1, cy - 12, cx + 1, cy - 10, P["metal_light"], EDGE)
    line(d, [(cx + 10, cy - 8), (cx + 14, cy - 13)], P["metal_light"], 1)


def espresso_machine(d, x, y, w=78, h=48):
    """Macchina espresso professionale: caldaia, manometri, 3 gruppi, vapore."""
    poly(d, [(x, y - h), (x + 10, y - h - 10), (x + w + 10, y - h - 10),
             (x + w, y - h)], S(P["metal_light"], 1.14), EDGE)
    poly(d, [(x + w, y - h), (x + w + 10, y - h - 10),
             (x + w + 10, y - 10), (x + w, y)], S(P["metal"], 1.06), EDGE)
    rect(d, x, y - h, x + w, y, P["metal_light"], EDGE)
    rect(d, x + 3, y - h + 3, x + w - 3, y - h + 17, P["ink"], EDGE)
    text(d, x + 8, y - h + 7, "NAPOLI", S(P["white"], 0.96), 1, 0)
    for gx in (x + 12, x + w - 23):
        ellipse(d, gx, y - h + 21, gx + 10, y - h + 31, P["white"], EDGE)
        line(d, [(gx + 5, y - h + 26), (gx + 8, y - h + 23)], P["red"], 1)
        rect(d, gx + 4, y - h + 29, gx + 6, y - h + 31, P["ink"])
    rect(d, x + 30, y - h + 22, x + 46, y - h + 31, S(P["terra"], 0.86), EDGE)
    rect(d, x + 33, y - h + 24, x + 43, y - h + 28, P["yellow"], EDGE)
    for gx in (x + 10, x + 33, x + 56):
        rect(d, gx, y - h + 34, gx + 16, y - h + 41, P["metal"], EDGE)
        rect(d, gx + 3, y - h + 36, gx + 13, y - h + 39, S(P["metal_light"], 1.12))
        rect(d, gx + 6, y - h + 41, gx + 10, y - h + 44, P["metal"], EDGE)
        rect(d, gx + 2, y - h + 44, gx + 14, y - h + 46, P["metal_light"], EDGE)
        rect(d, gx + 14, y - h + 42, gx + 23, y - h + 44, P["brown"], EDGE)
    rect(d, x + 3, y - 7, x + w - 3, y - 2, P["metal"], EDGE)
    for dx in range(x + 6, x + w - 4, 6):
        rect(d, dx, y - 6, dx + 1, y - 3, S(P["metal_light"], 0.92))
    line(d, [(x + w + 6, y - h + 24), (x + w + 11, y - h + 36),
             (x + w + 6, y - h + 47)], P["metal_light"], 2)
    ellipse(d, x + w + 2, y - h + 20, x + w + 9, y - h + 27, P["yellow"], EDGE)
    for cx in (x + 8, x + 24, x + 40, x + 56):
        rect(d, cx, y - h - 8, cx + 9, y - h - 2, P["white"], EDGE)
        rect(d, cx + 1, y - h - 7, cx + 8, y - h - 6, S(P["terra"], 0.88))


def sfogliatella(d, cx, cy):
    """Sfogliatella: conchiglia a sfoglie radiali, ben distinta in vetrina."""
    ellipse(d, cx - 10, cy - 6, cx + 10, cy + 4, S(P["terra"], 1.06), EDGE)
    rect(d, cx - 8, cy - 6, cx + 8, cy - 3, S(P["terra_light"], 1.02))
    for i in range(5):
        ox = cx - 8 + i * 4
        line(d, [(ox, cy - 4), (ox + 3, cy + 2)], S(P["terra_dark"], 1.05), 1)
    rect(d, cx - 7, cy - 7, cx + 7, cy - 6, P["yellow"])
    line(d, [(cx - 6, cy - 1), (cx + 6, cy - 1)], S(P["white"], 0.90), 1)


def baba(d, cx, cy):
    """Babà al rum: cilindro glassato con sciroppo e granella."""
    rect(d, cx - 7, cy - 4, cx + 7, cy + 5, P["brown"], EDGE)
    ellipse(d, cx - 7, cy - 7, cx + 7, cy + 2, S(P["brown"], 1.10), EDGE)
    ellipse(d, cx - 5, cy - 7, cx + 5, cy - 3, P["yellow"], EDGE)
    rect(d, cx - 2, cy - 6, cx + 2, cy - 5, S(P["white"], 0.94))
    rect(d, cx + 3, cy - 4, cx + 5, cy - 3, S(P["terra_dark"], 1.05))


def cannolo(d, cx, cy):
    """Cannolo siciliano: tubo dorato, ricotta alle estremita' e gocce."""
    rect(d, cx - 10, cy - 4, cx + 10, cy + 4, S(P["stucco_yellow"], 0.94), EDGE)
    rect(d, cx - 8, cy - 3, cx + 8, cy - 1, S(P["wood"], 1.16))
    ellipse(d, cx - 11, cy - 5, cx - 5, cy + 3, S(P["brown"], 1.05), EDGE)
    ellipse(d, cx + 5, cy - 5, cx + 11, cy + 3, S(P["brown"], 1.05), EDGE)
    ellipse(d, cx - 8, cy - 3, cx - 4, cy + 1, P["white"], EDGE)
    ellipse(d, cx + 4, cy - 3, cx + 8, cy + 1, P["white"], EDGE)
    for dx in (-4, 1, 5):
        rect(d, cx + dx, cy + 1, cx + dx + 1, cy + 2, S(P["brown"], 0.82))


def display_case(d, x, y, w, h):
    """Vetrina con due ripiani, dolci riconoscibili e riflessi piatti."""
    contact(d, x + w // 2, y + h + 2, w // 2, 4)
    rect(d, x, y, x + w, y + h, EDGE)
    rect(d, x + 3, y + 3, x + w - 3, y + h - 3, S(P["glass"], 0.78))
    rect(d, x + 3, y + 8, x + w - 3, y + 12, S(P["wood"], 0.92), EDGE)
    text(d, x + 8, y + 3, "PASTICCERIA", S(P["white"], 0.96), 1, 0)
    for sy, label in ((y + 34, "SFOGLIATELLE"), (y + 60, "BABA  CANNOLI")):
        rect(d, x + 4, sy, x + w - 4, sy + 2, P["metal_light"])
        text(d, x + 7, sy + 3, label, S(P["white"], 0.92), 1, 0)
    for i in range(4):
        sfogliatella(d, x + 24 + i * 34, y + 32)
        baba(d, x + 24 + i * 34, y + 58)
    for i in range(3):
        cannolo(d, x + 36 + i * 44, y + 56)
    rect(d, x + 8, y + 14, x + 13, y + h - 12, S(P["white"], 0.94))
    rect(d, x + 20, y + 14, x + 22, y + h - 12, S(P["white"], 0.86))
    rect(d, x + w - 10, y + 14, x + w - 6, y + h - 12, S(P["white"], 0.88))
    rect(d, x + 2, y + h - 9, x + w - 2, y + h - 2, S(P["wood"], 0.84), EDGE)


def fridge(d, x, y, w, h):
    """Frigo bevande con due ante vetrate e bottiglie allineate."""
    contact(d, x + w // 2, y + h + 2, w // 2, 4)
    box(d, x, y + h, w, h, 12, P["white"], P["concrete_light"], S(P["white"], 0.78))
    rect(d, x + 3, y + 10, x + w - 3, y + h - 10, S(P["glass"], 0.86), EDGE)
    text(d, x + 8, y + 2, "BEVANDE", P["eav_blue"], 1, 0)
    rect(d, x + 6, y + 13, x + w - 6, y + 15, P["metal_light"])
    rect(d, x + 6, y + 66, x + w - 6, y + 68, P["metal_light"])
    for by in (24, 46, 76, 98):
        for bx, bc in ((x + 9, P["red"]), (x + 27, P["eav_blue"]),
                       (x + 45, P["green"])):
            bottle(d, bx, by + 17, bc)
    rect(d, x + w - 10, y + 20, x + w - 6, y + 42, P["metal_light"], EDGE)
    rect(d, x + w - 10, y + 74, x + w - 6, y + 96, P["metal_light"], EDGE)


def chalk_text(d, x, y, label, color, scale=1):
    """Testo a gesso: stesse lettere 5x7, con lieve sfalsamento regolare."""
    cx = int(x)
    for i, ch in enumerate(str(label).upper()):
        glyph = FONT.get(ch, FONT["?"])
        dy = 1 if i % 4 == 2 else 0
        for row, bits in enumerate(glyph):
            for col in range(5):
                if bits & (1 << (4 - col)):
                    rect(d, cx + col * scale, y + row * scale + dy,
                         cx + (col + 1) * scale - 1,
                         y + (row + 1) * scale - 1 + dy, color)
        cx += 6 * scale


def menu_board(d, x, y, w, h):
    """Menu scritto a mano su lavagna: PREZZI, CAFFE, SFOGLIATELLE."""
    rect(d, x + 18, y - 28, x + 22, y, P["metal"], EDGE)
    rect(d, x + w - 22, y - 28, x + w - 18, y, P["metal"], EDGE)
    rect(d, x, y, x + w, y + h, P["wood"], EDGE)
    rect(d, x + 3, y + 3, x + w - 3, y + h - 3, S(P["ink"], 1.18), EDGE)
    chalk_text(d, x + 8, y + 7, "PREZZI", P["yellow"])
    line(d, [(x + 7, y + 19), (x + w - 7, y + 19)], S(P["white"], 0.72), 1)
    rows = (("CAFFE", "1.20"), ("SFOGLIATELLE", "2.00"),
            ("BABA", "2.00"), ("CANNOLI", "2.00"))
    for i, (name, price) in enumerate(rows):
        ry = y + 24 + i * 12
        chalk_text(d, x + 8, ry, name, S(P["white"], 0.94))
        chalk_text(d, x + w - 8 - text_w(price), ry, price, S(P["white"], 0.94))
    line(d, [(x + 8, y + h - 7), (x + w - 8, y + h - 7)], S(P["yellow"], 0.88), 1)


def clock(d, cx, cy, r):
    """Orologio da parete a lancette, quadrante piatto."""
    ellipse(d, cx - r, cy - r, cx + r, cy + r, S(P["wood"], 0.92), EDGE)
    ellipse(d, cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3, P["white"], EDGE)
    for k in range(12):
        a = math.radians(k * 30)
        x0 = int(cx + math.cos(a) * (r - 6))
        y0 = int(cy + math.sin(a) * (r - 6))
        x1 = int(cx + math.cos(a) * (r - 4))
        y1 = int(cy + math.sin(a) * (r - 4))
        line(d, [(x0, y0), (x1, y1)], P["ink"], 1)
    line(d, [(cx, cy), (cx + 5, cy - 6)], P["ink"], 2)
    line(d, [(cx, cy), (cx - 7, cy + 2)], P["red"], 2)
    ellipse(d, cx - 1, cy - 1, cx + 1, cy + 1, P["ink"])


def turnstile(d, x, y):
    """Tornello a tre bracci per la biglietteria EAV."""
    contact(d, x + 13, y + 2, 16, 3)
    rect(d, x, y - 10, x + 26, y, P["metal"], EDGE)
    rect(d, x + 3, y - 8, x + 23, y - 2, P["eav_blue"], EDGE)
    rect(d, x + 10, y - 24, x + 16, y - 10, P["metal_light"], EDGE)
    line(d, [(x + 13, y - 22), (x + 2, y - 14)], P["yellow"], 2)
    line(d, [(x + 13, y - 22), (x + 24, y - 14)], P["yellow"], 2)
    line(d, [(x + 13, y - 22), (x + 13, y - 31)], P["yellow"], 2)
    ellipse(d, x + 10, y - 27, x + 16, y - 21, P["eav_blue"], EDGE)


def pasta_pack(d, x, y, color):
    rect(d, x, y - 16, x + 9, y, color, EDGE)
    rect(d, x + 1, y - 13, x + 8, y - 8, P["white"])
    line(d, [(x + 2, y - 5), (x + 7, y - 5)], S(color, 0.78), 1)
    line(d, [(x + 2, y - 3), (x + 7, y - 3)], S(color, 0.78), 1)


def bottle(d, x, y, color):
    rect(d, x + 3, y - 18, x + 6, y - 13, color, EDGE)
    rect(d, x + 2, y - 13, x + 7, y, color, EDGE)
    rect(d, x + 2, y - 9, x + 7, y - 5, P["white"])
    rect(d, x + 3, y - 19, x + 6, y - 18, S(P["yellow"], 0.96))


def tin(d, x, y, color):
    rect(d, x, y - 11, x + 9, y, color, EDGE)
    ellipse(d, x, y - 13, x + 9, y - 9, S(color, 1.14), EDGE)
    rect(d, x + 1, y - 8, x + 8, y - 5, P["white"])


def price_tag(d, x, y, label):
    rect(d, x, y, x + 32, y + 11, EDGE)
    rect(d, x + 1, y + 1, x + 31, y + 10, P["white"])
    text(d, x + 3, y + 3, label, P["ink"], 1, 0)


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

    # rivestimento regolare piastrellato e fascia aziendale EAV
    tile_wall(d, 58, FLOOR_Y - 6, P["concrete_light"],
              S(P["concrete_light"], 0.94), 16, 0)
    rect(d, 0, 52, W, 58, P["eav_blue"], EDGE)
    rect(d, 0, 53, W, 54, S(P["eav_light"], 1.05))
    for px in (0, 142, 426, 566):
        rect(d, px, 0, px + 10, FLOOR_Y - 6, S(P["concrete_light"], 0.90), EDGE)
        rect(d, px + 2, 0, px + 8, 5, P["eav_blue"])
    window(d, 18, 16, 116, 78, 3)
    window(d, 432, 16, 126, 78, 4)

    # insegna EAV e orologio da parete
    rect(d, 142, 6, 238, 34, EDGE)
    rect(d, 145, 9, 235, 31, P["eav_blue"])
    text(d, 173, 12, "EAV", P["yellow"], 2, 1)
    rect(d, 152, 27, 228, 29, P["yellow"])
    clock(d, 204, 72, 17)

    # biglietteria con addetto, vetro e orario digitale
    contact(d, 338, 110, 72, 5)
    rect(d, 276, 24, 400, 88, EDGE)
    rect(d, 279, 27, 397, 85, P["eav_blue"])
    rect(d, 282, 30, 394, 33, S(P["eav_blue"], 1.3))
    rect(d, 282, 37, 394, 49, S(P["ink"], 1.18), EDGE)
    text(d, 285, 39, "BIGLIETTI", P["white"], 1, 0)
    person(d, 326, 86, P["eav_blue"], P["skin2"], P["hair1"], cap=P["eav_blue"])
    rect(d, 304, 52, 348, 82, EDGE)
    rect(d, 307, 55, 345, 79, S(P["glass"], 0.92, 132))
    rect(d, 309, 57, 322, 66, HILITE)
    rect(d, 354, 55, 392, 74, EDGE)
    rect(d, 357, 58, 389, 71, P["ink"])
    text(d, 359, 61, "06:40", P["yellow"], 1, 0)
    text(d, 359, 69, "EAV", P["white"], 1, 0)
    box(d, 270, 108, 136, 30, 16, P["eav_blue"], P["eav_light"], S(P["eav_blue"], 0.78))
    rect(d, 274, 84, 402, 88, S(P["eav_light"], 0.86), EDGE)
    rect(d, 330, 94, 356, 100, EDGE)
    rect(d, 333, 96, 353, 98, P["yellow"])
    for kx in (286, 300, 314):
        rect(d, kx, 94, kx + 7, 101, P["ink"], EDGE)

    # tabellone partenze: ora, destinazione e binario
    contact(d, 206, 176, 58, 4)
    rect(d, 156, 118, 258, 164, EDGE)
    rect(d, 159, 121, 255, 162, S(P["green_dark"], 1.45))
    rect(d, 159, 121, 255, 131, P["eav_blue"])
    text(d, 162, 123, "PARTENZE", P["yellow"], 1, 0)
    text(d, 231, 123, "EAV", P["white"], 1, 0)
    text(d, 162, 132, "ORA DEST BIN", S(P["yellow"], 0.86), 1, 0)
    for i, row in enumerate(("06:12 TORREGAVETA 1", "06:40 NAPOLI 2",
                             "07:05 TORREGAVETA 1")):
        text(d, 162, 139 + i * 8, row, P["white"], 1, 0)
    rect(d, 160, 164, 166, 178, P["metal"], EDGE)
    rect(d, 246, 164, 252, 178, P["metal"], EDGE)

    # tornelli d'ingresso e indicazioni
    sign(d, 424, 148, 104, "INGRESSO", P["eav_blue"], 1)
    turnstile(d, 440, 232)
    turnstile(d, 510, 232)
    rect(d, 424, 246, 540, 248, P["yellow"])

    # panchine regolari e viaggiatori
    bench(d, 52, 284, 104)
    seated_person(d, 90, 280, P["terra"], P["skin1"], P["hair2"])
    bench(d, 420, 284, 104)
    person(d, 194, 232, P["green_dark"], P["skin2"], P["hair1"])
    person(d, 404, 252, P["terra"], P["skin3"], P["hair3"])

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

    # pilastri napoletani e fregio della parete
    for px in (0, 166, 470, 566):
        rect(d, px, 0, px + 8, FLOOR_Y - 6, S(P["white"], 0.94), EDGE)
        rect(d, px + 2, 20, px + 6, 104, S(P["terra"], 0.92))

    # insegna "BAR NAPOLITANO" e cartiglio dolci
    rect(d, 172, 22, 404, 54, P["terra"], EDGE)
    rect(d, 176, 26, 400, 50, S(P["terra"], 1.12), EDGE)
    text(d, 220, 32, "BAR NAPOLITANO", P["white"], 2, 0)
    rect(d, 178, 46, 398, 48, S(P["yellow"], 0.96))
    sign(d, 472, 30, 92, "DOLCI", P["brown"], 1)

    # menu scritto a mano e lampade a pendaglio
    menu_board(d, 16, 28, 140, 78)
    pendant(d, 180)
    pendant(d, 420)

    # barista con grembiule e papillon
    person(d, 164, 178, P["white"], P["skin2"], P["hair1"],
           apron=S(P["terra"], 0.88), cap=P["terra"])
    rect(d, 162, 157, 166, 159, P["red"], EDGE)

    # bancone: fronte in legno a pannelli e piano in marmo
    contact(d, 172, 262, 146, 5)
    box(d, 20, 258, 284, 88, 18, P["brown"], S(P["wood"], 1.12), S(P["brown"], 0.76))
    poly(d, [(20, 170), (38, 152), (322, 152), (304, 170)],
         S(P["white"], 0.96), EDGE)
    rect(d, 20, 170, 304, 176, S(P["concrete_light"], 1.02), EDGE)
    line(d, [(44, 158), (68, 158), (82, 164), (104, 164)], S(P["glass_light"], 0.94), 1)
    line(d, [(128, 156), (150, 156), (162, 162), (184, 162)], S(P["glass_light"], 0.94), 1)
    line(d, [(244, 158), (266, 158), (278, 164), (300, 164)], S(P["glass_light"], 0.94), 1)
    for px in (28, 76, 124, 172, 220, 268):
        rect(d, px, 182, px + 40, 244, S(P["brown"], 0.76), EDGE)
        rect(d, px + 3, 185, px + 37, 241, S(P["wood"], 0.92), EDGE)
        rect(d, px + 6, 188, px + 34, 238, S(P["brown"], 0.96))
        rect(d, px + 10, 192, px + 30, 234, S(P["wood"], 1.06))
        for cy in (190, 236):
            rect(d, px + 18, cy, px + 22, cy + 2, P["yellow"])
    rect(d, 20, 177, 304, 181, P["metal_light"], EDGE)
    rect(d, 20, 246, 304, 252, S(P["brown"], 0.66), EDGE)

    # macchina espresso professionale a tre gruppi
    espresso_machine(d, 212, 160)

    # tazzine, zuccheriera e portaricette sul piano
    for cx in (52, 82, 110, 300):
        cup(d, cx, 166)
    sugar_bowl(d, 190, 164)
    rect(d, 138, 154, 166, 166, S(P["wood"], 0.90), EDGE)
    rect(d, 141, 156, 163, 160, P["white"])
    text(d, 143, 157, "EAV", S(P["terra"], 0.92), 1, 0)

    # vetrina: sfogliatelle, baba' e cannoli su due ripiani
    display_case(d, 318, 158, 148, 84)

    # frigo delle bevande
    fridge(d, 476, 122, 76, 138)

    # tavolini, sedie e clienti seduti (sempre 16x32)
    chair(d, 72, 344)
    seated_person(d, 72, 342, P["eav_blue"], P["skin1"], P["hair2"])
    cafe_table(d, 110, 322)
    chair(d, 158, 340)
    chair(d, 394, 344)
    seated_person(d, 394, 342, P["terra"], P["skin3"], P["hair3"])
    cafe_table(d, 352, 324)
    person(d, 470, 318, P["green_dark"], P["skin2"], P["hair1"])

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

    # luci a soffitto e cartelli di reparto
    rect(d, 60, 4, 132, 8, P["metal_light"], EDGE)
    rect(d, 444, 4, 516, 8, P["metal_light"], EDGE)
    sign(d, 34, 86, 84, "PASTA", P["white"], 1, P["green_dark"])
    sign(d, 122, 86, 84, "OLIO", P["white"], 1, P["green_dark"])
    sign(d, 250, 104, 50, "RISO", P["white"], 1, P["green_dark"])

    # due scaffalature ordinate con merce riconoscibile
    for base_x in (34, 122):
        contact(d, base_x + 42, 242, 43, 4)
        box(d, base_x, 238, 84, 122, 14, S(P["wood"], 0.92),
            S(P["wood"], 1.08), S(P["wood"], 0.74))
        for sy in (150, 180, 210):
            rect(d, base_x + 2, sy, base_x + 82, sy + 2, S(P["wood"], 1.18))
            for i in range(6):
                bx = base_x + 6 + i * 13
                if sy == 150:
                    pasta_pack(d, bx, sy, P["terra"] if i % 2 else P["yellow"])
                elif sy == 180:
                    bottle(d, bx + 1, sy, (P["red"], P["green"], P["eav_blue"])[i % 3])
                else:
                    tin(d, bx + 1, sy, (P["white"], P["terra"], P["stucco_yellow"])[i % 3])
            price_tag(d, base_x + 48, sy + 3, "1.20" if sy != 210 else "2.00")
        rect(d, base_x + 4, 232, base_x + 80, 236, S(P["wood"], 0.72))

    # scaffale stretto laterale
    contact(d, 276, 260, 26, 4)
    box(d, 250, 258, 50, 130, 12, S(P["wood"], 0.88), P["wood"], S(P["wood"], 0.72))
    for sy in (152, 180, 208, 236):
        rect(d, 252, sy, 298, sy + 2, S(P["wood"], 1.18))
        for i in range(3):
            bx = 254 + i * 15
            if i == 0:
                pasta_pack(d, bx, sy, P["white"])
            elif i == 1:
                bottle(d, bx + 1, sy, P["red"])
            else:
                tin(d, bx + 1, sy, P["yellow"])
        text(d, 266, sy + 3, "2.00", P["ink"], 1, 0)

    # cassetta di frutta ordinata, davanti allo scaffale
    contact(d, 190, 302, 25, 4)
    box(d, 166, 300, 46, 18, 8, S(P["wood"], 0.90), P["wood"], S(P["wood"], 0.74))
    for fx in (174, 188, 202):
        ellipse(d, fx - 6, 276, fx + 6, 288, P["red"], EDGE)
        ellipse(d, fx - 2, 275, fx + 1, 277, P["green_light"])

    # commerciante con grembiule dietro il banco
    person(d, 400, 196, S(P["stucco_yellow"], 0.92), P["skin2"], P["hair2"],
           apron=S(P["white"], 0.94))

    # banco cassa con registratore, tastierino e bilancia
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
    rect(d, 440, 184, 466, 199, P["metal_light"], EDGE)
    rect(d, 443, 187, 463, 194, P["ink"])
    text(d, 444, 188, "12.40", P["yellow"], 1, 0)
    ellipse(d, 450, 174, 458, 182, P["white"], EDGE)
    rect(d, 446, 196, 462, 200, P["yellow"], EDGE)

    # frigo delle bevande fredde
    contact(d, 518, 270, 34, 4)
    box(d, 486, 268, 64, 128, 12, P["white"], P["concrete_light"], S(P["white"], 0.78))
    rect(d, 492, 148, 544, 200, S(P["glass"], 0.88), EDGE)
    rect(d, 492, 210, 544, 262, S(P["glass"], 0.85), EDGE)
    text(d, 500, 140, "FREDDE", P["eav_blue"], 1, 0)
    for by in (162, 184, 224, 246):
        for bx in (498, 516):
            pc = (P["red"], P["green"], P["yellow"])[(bx + by) // 20 % 3]
            bottle(d, bx, by + 14, pc)
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

    # finestra con tende e fascia di luce piatta sul pavimento
    window(d, 40, 24, 136, 76, 3)
    curtains(d, 40, 24, 136, 80)
    poly(d, [(52, 120), (164, 120), (196, 216), (20, 216)],
         S(S(P["wood"], 0.92), 1.12), None)

    # quadri, orologio e lampada
    for fx, tone in ((196, P["terra"]), (232, P["green"])):
        rect(d, fx, 38, fx + 24, 64, P["wood"], EDGE)
        rect(d, fx + 3, 41, fx + 21, 61, S(P["white"], 0.94))
        rect(d, fx + 5, 52, fx + 19, 59, S(tone, 0.92))
        ellipse(d, fx + 9, 44, fx + 15, 50, S(P["skin2"], 0.94))
    clock(d, 450, 48, 15)
    pendant(d, 300, P["yellow"])

    # letto con coperchio piegato e cuscini
    contact(d, 104, 332, 72, 5)
    box(d, 30, 328, 140, 22, 16, S(P["wood"], 0.88), P["wood"], S(P["wood"], 0.74))
    rect(d, 46, 268, 62, 306, S(P["wood"], 0.82), EDGE)
    rect(d, 30, 244, 62, 306, S(P["wood"], 0.90), EDGE)
    rect(d, 34, 248, 58, 302, S(P["wood"], 1.12))
    rect(d, 62, 268, 168, 304, P["white"], EDGE)
    rect(d, 62, 276, 168, 304, S(P["eav_light"], 0.86), EDGE)
    rect(d, 66, 280, 164, 284, S(P["eav_light"], 1.12))
    rect(d, 62, 290, 168, 304, S(P["terra"], 1.05), EDGE)
    for fx in (82, 106, 130, 154):
        line(d, [(fx, 292), (fx + 4, 302)], S(P["terra_dark"], 1.05), 1)
    rect(d, 62, 288, 168, 291, S(P["terra_light"], 1.02))
    rect(d, 68, 256, 102, 270, S(P["white"], 0.94), EDGE)
    rect(d, 106, 256, 140, 270, S(P["white"], 0.94), EDGE)
    line(d, [(70, 258), (100, 258)], S(P["concrete_light"], 1.05), 1)
    line(d, [(108, 258), (138, 258)], S(P["concrete_light"], 1.05), 1)
    rect(d, 32, 322, 168, 326, S(P["wood"], 1.16))
    ellipse(d, 180, 336, 196, 342, P["terra"], EDGE)
    ellipse(d, 200, 336, 216, 342, P["terra"], EDGE)

    # cucina: pensili, backsplash, lavello, fornelli e oggetti quotidiani
    for cx in (240, 330):
        box(d, cx, 110, 76, 50, 12, S(P["wood"], 0.92),
            S(P["wood"], 1.08), S(P["wood"], 0.76))
        rect(d, cx + 34, 94, cx + 42, 98, P["metal_light"], EDGE)
    tile_wall(d, 112, 166, P["white"], P["concrete_light"], 16, 0)
    contact(d, 326, 268, 96, 4)
    box(d, 230, 264, 190, 94, 14, S(P["wood"], 0.90), S(P["concrete_light"], 1.02),
        S(P["wood"], 0.74))
    for sx in range(240, 420, 32):
        rect(d, sx, 176, sx + 2, 260, S(P["wood"], 0.70))
        rect(d, sx + 12, 206, sx + 22, 210, P["metal_light"], EDGE)
    rect(d, 250, 158, 292, 174, P["metal_light"], EDGE)
    rect(d, 256, 162, 282, 170, P["glass"], EDGE)
    line(d, [(273, 160), (273, 148), (281, 148), (281, 156)], P["metal"], 2)
    cup(d, 266, 170, saucer=False)
    rect(d, 296, 158, 324, 174, P["ink"], EDGE)
    for bx in (302, 314):
        ellipse(d, bx, 162, bx + 6, 168, S(P["metal_light"], 0.94))
    rect(d, 300, 148, 320, 162, S(P["terra"], 1.02), EDGE)
    ellipse(d, 299, 146, 321, 151, S(P["terra_light"], 1.02), EDGE)
    rect(d, 306, 142, 314, 146, P["metal_light"], EDGE)
    rect(d, 340, 154, 400, 172, S(P["wood"], 1.06), EDGE)
    rect(d, 348, 148, 370, 158, S(P["white"], 0.94), EDGE)
    line(d, [(352, 150), (366, 150)], S(P["terra"], 0.92), 1)
    rect(d, 376, 146, 394, 156, P["eav_blue"], EDGE)

    # TV con scena semplice e mobiletto
    contact(d, 512, 248, 38, 4)
    box(d, 474, 244, 76, 56, 12, S(P["ink_soft"], 1.1), S(P["ink_soft"], 1.3),
        S(P["ink_soft"], 0.8))
    rect(d, 480, 196, 544, 236, P["ink"], EDGE)
    rect(d, 484, 200, 540, 232, S(P["eav_light"], 0.92), EDGE)
    rect(d, 486, 216, 538, 230, S(P["green"], 1.05))
    poly(d, [(486, 230), (500, 216), (514, 230)], S(P["green_dark"], 1.1), None)
    ellipse(d, 526, 204, 536, 214, P["yellow"])
    rect(d, 488, 203, 500, 209, S(P["white"], 0.86))
    rect(d, 506, 244, 518, 250, P["metal_light"], EDGE)

    # tappeto con bordo a greca, tavolo, sedia, libro e pianta
    rect(d, 150, 292, 330, 356, S(P["terra"], 1.15), EDGE)
    rect(d, 158, 300, 322, 348, S(P["terra"], 0.92), S(P["white"], 0.88))
    rect(d, 166, 308, 314, 340, S(P["terra"], 1.08))
    for rx in range(166, 306, 24):
        rect(d, rx, 302, rx + 12, 304, S(P["yellow"], 0.94))
        rect(d, rx, 344, rx + 12, 346, S(P["yellow"], 0.94))
    chair(d, 156, 344)
    cafe_table(d, 210, 326)
    rect(d, 196, 306, 212, 310, P["eav_blue"], EDGE)
    rect(d, 198, 307, 210, 308, S(P["white"], 0.94))
    contact(d, 70, 226, 16, 4)
    rect(d, 58, 206, 82, 226, P["terra"], EDGE)
    rect(d, 56, 204, 84, 208, S(P["terra"], 1.18), EDGE)
    for px, py in ((70, 194), (58, 198), (82, 198), (66, 184), (76, 186)):
        ellipse(d, px - 9, py - 9, px + 9, py + 9, P["green"], EDGE)
        ellipse(d, px - 3, py - 4, px + 2, py, P["green_light"])

    door_bottom(d)
    save_png(img, OUT / "home.png")
    return make_manifest(
        "home", [-0.75, 100.2],
        [[30, 226, 170, 330], [230, 150, 420, 268], [470, 180, 552, 246]],
        [
            {"id": "bed", "name": "Letto (riposa)", "x": 100, "y": 280, "kind": "sleep"},
            {"id": "wardrobe", "name": "Armadio e arredi", "x": 470, "y": 150, "kind": "furnish"},
            {"id": "home_exit", "name": "Esci di casa", "x": 288, "y": 374, "kind": "exit"},
        ],
    )


# --- 5. Pizzeria Carpe Diem (OSM way/655446533) -----------------------------
def pizzeria():
    img, d = room_base("pizzeria", P["stucco_ochre"], P["concrete_light"],
                       S(P["concrete_light"], 0.95), "tile")

    # Fascia in terracotta, insegna dedicata e finestra sul lato sinistro.
    rect(d, 0, 32, W, 36, P["terra"], EDGE)
    greca(d, 0, 4, W, 18, S(P["terra_dark"], 1.05))
    sign(d, 166, 16, 244, "PIZZERIA CARPE DIEM", P["terra"], 2)
    window(d, 18, 36, 116, 70, 3)
    curtains(d, 18, 36, 116, 74)
    pendant(d, 244)
    pendant(d, 404)

    # Lavagna dei prezzi, fissata alla parete senza invadere il corridoio.
    menu_board(d, 430, 38, 130, 68)

    # Forno a legna: volume in mattoni, arcata, brace e pala appesa.
    contact(d, 138, 272, 92, 5)
    box(d, 46, 266, 168, 106, 14, S(P["terra"], 0.94),
        S(P["terra_light"], 1.04), S(P["terra"], 0.76))
    rect(d, 64, 180, 148, 250, S(P["ink"], 1.05), EDGE)
    ellipse(d, 64, 166, 148, 226, S(P["ink"], 1.05), EDGE)
    ellipse(d, 72, 174, 140, 218, S(P["terra_dark"], 1.04), EDGE)
    ellipse(d, 80, 182, 132, 210, S(P["yellow"], 0.96))
    for fx in (88, 100, 112, 124):
        poly(d, [(fx - 4, 208), (fx, 190 + (fx % 3) * 2), (fx + 4, 208)],
             S(P["red"], 1.05), None)
    text(d, 84, 232, "FORNO", P["white"], 1, 0)
    rect(d, 62, 252, 150, 258, S(P["wood"], 0.86), EDGE)
    line(d, [(58, 258), (58, 286)], P["metal_light"], 2)
    ellipse(d, 50, 276, 66, 290, P["metal"], EDGE)
    rect(d, 50, 282, 60, 284, P["metal_light"])

    # Pizzaiolo dietro il banco: il banco copre le gambe, come in un locale vero.
    person(d, 410, 188, P["white"], P["skin2"], P["hair3"],
           apron=S(P["white"], 0.94), cap=P["white"])

    # Banco in muratura con piano in marmo, cassa e pizze appena sfornate.
    contact(d, 414, 296, 100, 5)
    box(d, 318, 292, 190, 82, 16, P["terra_dark"],
        S(P["wood"], 1.12), S(P["terra_dark"], 0.74))
    poly(d, [(318, 210), (334, 194), (524, 194), (508, 210)],
         S(P["white"], 0.96), EDGE)
    rect(d, 318, 210, 508, 216, S(P["concrete_light"], 1.02), EDGE)
    for px in (334, 380, 426, 472):
        rect(d, px, 224, px + 30, 284, S(P["terra"], 0.78), EDGE)
        rect(d, px + 3, 227, px + 27, 281, S(P["wood"], 0.94))
    rect(d, 340, 196, 374, 210, P["ink"], EDGE)
    rect(d, 343, 198, 371, 206, P["glass"])
    text(d, 344, 199, "CASSA", P["yellow"], 1, 0)
    for cx in (400, 444, 488):
        ellipse(d, cx - 15, 200, cx + 15, 210, S(P["stucco_yellow"], 0.96), EDGE)
        ellipse(d, cx - 11, 202, cx + 11, 208, P["terra"])
        for ox in (-6, 0, 6):
            ellipse(d, cx + ox - 2, 203, cx + ox + 1, 206, P["white"])
    rect(d, 476, 232, 500, 246, P["eav_blue"], EDGE)
    text(d, 478, 235, "4.50", P["yellow"], 1, 0)

    # Due tavolini ai lati: il passaggio centrale dalla porta al banco resta libero.
    cafe_table(d, 104, 330)
    chair(d, 104, 350)
    person(d, 104, 348, P["eav_blue"], P["skin1"], P["hair2"])
    cafe_table(d, 500, 330)
    chair(d, 500, 350)
    seated_person(d, 500, 348, P["green_dark"], P["skin3"], P["hair1"])

    door_bottom(d, "USCITA")
    save_png(img, OUT / "pizzeria.png")
    return make_manifest(
        "pizzeria", [-126.3, 123.9],
        [[46, 160, 228, 270], [318, 190, 524, 294]],
        [
            {"id": "pizzaiolo", "name": "Pizzaiolo", "x": 410, "y": 166, "kind": "pizzaiolo"},
            {"id": "pizza_counter", "name": "Banco pizze", "x": 412, "y": 300, "kind": "buy_pizza"},
            {"id": "pizza_menu", "name": "Menu della pizzeria", "x": 494, "y": 110, "kind": "read"},
            {"id": "pizza_exit", "name": "Esci dalla pizzeria", "x": 288, "y": 370, "kind": "exit"},
        ],
    )


# --- 6. Supermercato --------------------------------------------------------
def supermarket():
    img, d = room_base("supermarket", P["stucco_green"], P["concrete_light"],
                       S(P["concrete_light"], 0.94), "tile")
    sign(d, 36, 18, 190, "CONAD", P["eav_blue"], 2)
    window(d, 410, 16, 132, 78, 3)

    for ry in (150, 222):
        box(d, 44, ry, 210, 48, 16, S(P["green_dark"], 0.86),
            P["green"], S(P["green_dark"], 0.72))
        for sx in range(52, 250, 24):
            rect(d, sx, ry - 44, sx + 12, ry - 12, P["white"], EDGE)
            rect(d, sx + 2, ry - 42, sx + 10, ry - 38, P["terra"])
            rect(d, sx + 2, ry - 34, sx + 10, ry - 30, P["eav_blue"])
    box(d, 330, 250, 190, 52, 18, S(P["eav_blue"], 0.86),
        P["eav_blue"], S(P["eav_blue"], 0.70))
    rect(d, 346, 214, 504, 220, P["yellow"], EDGE)
    text(d, 360, 224, "CASSE", P["ink"], 1, 0)
    for cx in (376, 434, 492):
        rect(d, cx, 232, cx + 22, 240, P["ink"])
        rect(d, cx + 3, 234, cx + 19, 237, P["glass_light"])
    person(d, 420, 316, P["eav_blue"], apron=P["white"], cap=P["yellow"])
    person(d, 190, 300, P["terra"], P["skin2"], P["hair2"])

    door_bottom(d, "USCITA")
    save_png(img, OUT / "supermarket.png")
    return make_manifest(
        "supermarket", [128.606, 162.528],
        [[44, 86, 270, 150], [44, 158, 270, 222], [330, 180, 538, 250]],
        [
            {"id": "supermarket_cashier", "name": "Cassiere", "x": 430, "y": 300, "kind": "shop"},
            {"id": "supermarket_shelf", "name": "Scaffale", "x": 150, "y": 236, "kind": "read"},
            {"id": "supermarket_notice", "name": "Prezzi del quartiere", "x": 500, "y": 150, "kind": "read"},
            {"id": "supermarket_exit", "name": "Esci dal supermercato", "x": 288, "y": 356, "kind": "exit"},
        ],
    )


# --- 7. Tabaccheria ---------------------------------------------------------
def tobacco():
    img, d = room_base("tobacco", P["stucco_yellow"], P["stucco_ochre"],
                       S(P["stucco_ochre"], 0.95), "plain")
    rect(d, 40, 8, 300, 46, P["green_dark"], EDGE)
    text(d, 58, 18, "TABACCHERIA", P["yellow"], 2, 1)
    rect(d, 312, 10, 360, 44, P["yellow"], EDGE)
    text(d, 326, 18, "T", P["green_dark"], 3, 0)

    box(d, 60, 220, 250, 56, 18, S(P["wood"], 0.86), P["wood"], S(P["wood"], 0.72))
    text(d, 94, 184, "TABACCHI E LOTTERIE", P["ink"], 1, 0)
    for bx in (80, 128, 176, 224, 272):
        rect(d, bx, 190, bx + 32, 204, P["white"], EDGE)
        rect(d, bx + 4, 192, bx + 28, 195, P["green_dark"])
        rect(d, bx + 6, 198, bx + 26, 200, P["terra"])
    box(d, 380, 250, 140, 48, 16, S(P["metal_light"], 0.86),
        P["metal_light"], S(P["metal"], 0.90))
    rect(d, 400, 218, 500, 236, P["ink"], EDGE)
    rect(d, 406, 220, 494, 226, P["glass_light"])
    person(d, 448, 306, P["green_dark"], apron=P["white"], cap=P["yellow"])
    person(d, 190, 310, P["eav_blue"], P["skin3"], P["hair3"])

    door_bottom(d, "USCITA")
    save_png(img, OUT / "tobacco.png")
    return make_manifest(
        "tobacco", [627.065, 408.345],
        [[60, 146, 328, 220], [380, 186, 536, 250]],
        [
            {"id": "tobacco_clerk", "name": "Tabaccaio", "x": 450, "y": 282, "kind": "shop"},
            {"id": "tobacco_sign", "name": "Insegna T e avvisi", "x": 344, "y": 140, "kind": "read"},
            {"id": "tobacco_counter", "name": "Banco tabacchi", "x": 180, "y": 250, "kind": "read"},
            {"id": "tobacco_exit", "name": "Esci dalla tabaccheria", "x": 288, "y": 356, "kind": "exit"},
        ],
    )


# --- 8. Scommesse d'oro (fittizio) -----------------------------------------
def bookmaker():
    img, d = room_base("bookmaker", P["stucco_yellow"], P["concrete"],
                       S(P["concrete"], 0.94), "panel")
    rect(d, 40, 10, 384, 52, P["yellow"], EDGE)
    text(d, 62, 22, "SCOMMESSE D ORO", P["ink"], 2, 1)
    text(d, 90, 46, "10:00-22:00", P["ink_soft"], 1, 0)
    for sx in (60, 190, 320):
        rect(d, sx, 74, sx + 100, 136, P["ink"], EDGE)
        rect(d, sx + 4, 78, sx + 96, 132, P["glass"], EDGE)
        for row, color in enumerate((P["white"], P["yellow"], P["green_light"])):
            rect(d, sx + 8, 84 + row * 16, sx + 92, 90 + row * 16, color)
        rect(d, sx + 8, 118, sx + 48, 124, P["eav_blue"])
    box(d, 60, 246, 300, 52, 18, S(P["yellow"], 0.86),
        P["yellow"], S(P["stucco_ochre"], 0.90))
    text(d, 88, 216, "SCHEDINE E RISULTATI", P["ink"], 1, 0)
    person(d, 200, 310, P["stucco_yellow"], apron=P["white"], cap=P["yellow"])
    person(d, 440, 300, P["eav_blue"], P["skin2"], P["hair1"])

    door_bottom(d, "USCITA")
    save_png(img, OUT / "bookmaker.png")
    return make_manifest(
        "bookmaker", [-231.534, 78.236],
        [[60, 176, 170, 246], [190, 176, 300, 246], [320, 176, 430, 246],
         [60, 176, 360, 246]],
        [
            {"id": "bookmaker_clerk", "name": "Addetto scommesse", "x": 210, "y": 282, "kind": "shop"},
            {"id": "bookmaker_notice", "name": "Attivita fittizia", "x": 470, "y": 160, "kind": "read"},
            {"id": "bookmaker_board", "name": "Tabellone risultati", "x": 250, "y": 150, "kind": "read"},
            {"id": "bookmaker_exit", "name": "Esci", "x": 288, "y": 356, "kind": "exit"},
        ],
    )


# --- 9. Forno / panetteria --------------------------------------------------
def bakery():
    img, d = room_base("bakery", P["stucco_cream"], P["stucco_ochre"],
                       S(P["stucco_ochre"], 0.95), "tile")
    sign(d, 60, 16, 180, "ANEMA E PANE", P["terra"], 1)
    display_case(d, 64, 152, 246, 92)
    box(d, 360, 232, 158, 66, 18, S(P["metal_light"], 0.80),
        P["metal_light"], S(P["metal"], 0.90))
    rect(d, 382, 184, 496, 210, P["ink"], EDGE)
    rect(d, 388, 188, 490, 206, P["terra_dark"])
    text(d, 402, 192, "FORNO", P["yellow"], 1, 0)
    person(d, 440, 300, P["white"], apron=P["stucco_cream"], cap=P["white"])
    person(d, 200, 316, P["green_dark"], P["skin2"], P["hair2"])

    door_bottom(d, "USCITA")
    save_png(img, OUT / "bakery.png")
    return make_manifest(
        "bakery", [242.973, 300.093],
        [[64, 52, 328, 152], [360, 148, 536, 232]],
        [
            {"id": "bakery_case", "name": "Vetrina dolci", "x": 190, "y": 268, "kind": "buy_food"},
            {"id": "bakery_baker", "name": "Fornaio", "x": 440, "y": 270, "kind": "read"},
            {"id": "bakery_menu", "name": "Menu del forno", "x": 344, "y": 140, "kind": "read"},
            {"id": "bakery_exit", "name": "Esci dal forno", "x": 288, "y": 356, "kind": "exit"},
        ],
    )


# --- 10. Negozio d'abbigliamento --------------------------------------------
def clothing():
    img, d = room_base("clothing", P["stucco_pink"], P["concrete_light"],
                       S(P["concrete_light"], 0.94), "panel")
    sign(d, 50, 16, 180, "TOYS CENTER", P["eav_blue"], 1)
    for rx in (64, 160, 256):
        rect(d, rx, 124, rx + 6, 232, P["metal"], EDGE)
        rect(d, rx + 74, 124, rx + 80, 232, P["metal"], EDGE)
        rect(d, rx, 128, rx + 80, 134, P["metal_light"], EDGE)
        for sx in (rx + 14, rx + 44):
            rect(d, sx, 138, sx + 20, 196, P["eav_blue"], EDGE)
            rect(d, sx + 4, 134, sx + 16, 142, P["white"])
            rect(d, sx, 170, sx + 20, 174, P["white"])
    box(d, 390, 236, 140, 50, 16, S(P["wood"], 0.86), P["wood"], S(P["wood"], 0.72))
    rect(d, 410, 176, 510, 222, P["glass"], EDGE)
    rect(d, 414, 180, 506, 218, P["glass_light"])
    text(d, 430, 204, "PROVE", P["ink"], 1, 0)
    person(d, 458, 310, P["terra"], apron=P["white"], cap=P["yellow"])
    person(d, 190, 306, P["stucco_pink"], P["skin1"], P["hair2"])

    door_bottom(d, "USCITA")
    save_png(img, OUT / "clothing.png")
    return make_manifest(
        "clothing", [640.968, 339.512],
        [[64, 116, 350, 232], [390, 170, 546, 236]],
        [
            {"id": "clothing_clerk", "name": "Commesso", "x": 458, "y": 272, "kind": "shop"},
            {"id": "clothing_rack", "name": "Scaffale abiti", "x": 210, "y": 252, "kind": "read"},
            {"id": "clothing_fitting", "name": "Camerino", "x": 460, "y": 250, "kind": "read"},
            {"id": "clothing_exit", "name": "Esci dal negozio", "x": 288, "y": 356, "kind": "exit"},
        ],
    )


# --- 11. Officina -----------------------------------------------------------
def workshop():
    img, d = room_base("workshop", P["stucco_blue"], P["asphalt_light"],
                       S(P["asphalt_light"], 0.94), "block")
    sign(d, 50, 16, 190, "OFFICINA", P["eav_blue"], 2)
    box(d, 48, 248, 240, 56, 18, S(P["metal"], 0.82),
        P["metal"], S(P["metal"], 0.70))
    for tx in (70, 122, 174, 226):
        rect(d, tx, 210, tx + 30, 226, P["red"], EDGE)
        rect(d, tx + 4, 214, tx + 26, 218, P["metal_light"])
    box(d, 352, 238, 166, 62, 18, S(P["rust"], 0.86),
        S(P["rust"], 1.10), S(P["rust"], 0.72))
    ellipse(d, 382, 194, 434, 232, P["ink"], EDGE)
    ellipse(d, 390, 202, 426, 224, P["metal_light"], EDGE)
    person(d, 300, 310, P["eav_blue"], apron=P["yellow"], cap=P["yellow"])
    person(d, 490, 300, P["green_dark"], P["skin3"], P["hair3"])

    door_bottom(d, "USCITA")
    save_png(img, OUT / "workshop.png")
    return make_manifest(
        "workshop", [477.917, 391.476],
        [[48, 174, 306, 248], [352, 158, 536, 238]],
        [
            {"id": "workshop_mechanic", "name": "Meccanico", "x": 300, "y": 282, "kind": "shop"},
            {"id": "workshop_tools", "name": "Banco attrezzi", "x": 180, "y": 278, "kind": "read"},
            {"id": "workshop_part", "name": "Ricambi", "x": 440, "y": 270, "kind": "read"},
            {"id": "workshop_exit", "name": "Esci dall'officina", "x": 288, "y": 356, "kind": "exit"},
        ],
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rooms = {
        "station": station(),
        "bar": bar(),
        "shop": shop(),
        "home": home(),
        "pizzeria": pizzeria(),
        "supermarket": supermarket(),
        "tobacco": tobacco(),
        "bookmaker": bookmaker(),
        "bakery": bakery(),
        "clothing": clothing(),
        "workshop": workshop(),
    }
    for name, data in rooms.items():
        # Il nome visualizzato della pizzeria viene dal POI OSM way/655446533.
        data["name"] = "Pizzeria Carpe Diem" if name == "pizzeria" else name
        data["size_px"] = [W, H]
        data["scale_ppm"] = PPM

    # Metadati di versione: il manifest resta indicizzato per nome stanza,
    # come richiesto dal loader; la voce `version` e' una stringa e la sua
    # PNG evita che il preload di BootScene segnali un asset mancante.
    rooms["version"] = "0.6.0"
    img, d = room_base("version", P["eav_blue"], P["concrete_light"],
                       S(P["concrete_light"], 0.94), "tile")
    sign(d, 148, 118, 280, "NAPOLI LIFE 0.6.0", P["eav_blue"], 1)
    door_bottom(d, "VERSIONE")
    save_png(img, OUT / "version.png")

    (OUT / "manifest.json").write_text(
        json.dumps(rooms, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {len(rooms) - 1} interni + versione 0.6.0 (576x384 @ 48 px/m)")


if __name__ == "__main__":
    main()
