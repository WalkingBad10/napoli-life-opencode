#!/usr/bin/env python3
"""Sprite originali in pixel art per NAPOLI LIFE 0.4.0.

Proiezione obliqua a tre quarti, scala uniforme 1 m = 16 px, zero anti-aliasing.
Ogni pixel e' posizionato deliberatamente: i personaggi usano una griglia
simbolica 16x32 (testa, busto, bracci, gambe e accessori disegnati a mano),
i veicoli e l'arredo urbano usano primitive intere. Tutti i colori appartengono
alla palette di artlib.py o sono derivati da shade()/dim(). Nessuna sfocatura,
nessun gradiente morbido, nessun pixel casuale: le uniche sequenze ripetitive
sono regolari (finestre, prese d'aria, carrelli).
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from artlib import P, ellipse, line, rect, rgba, save_png, shade

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/assets/sprites"

PPM = 16                  # pixel per metro (contratto ART_SPEC.md)
FW, FH = 16, 32           # frame personaggio: 1,0 x 2,0 m
FEET_Y = 30               # piedi a y=30, origine ai piedi
SHEET_COLUMNS, SHEET_ROWS = 4, 4
SHEET_W, SHEET_H = FW * SHEET_COLUMNS, FH * SHEET_ROWS  # 64 x 128
DIRECTIONS = ("down", "left", "right", "up")

INK = P["ink"]
SHADOW = (*rgba(P["shadow"])[:3], 44)   # ombra di contatto, alpha <= 45


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
    """Contorno scuro di 1 px intorno alle forme opache.

    L'ombra di contatto semitrasparente viene conservata e non genera
    contorno; i pixel opachi non vengono mai riscritti. Nessuna
    interpolazione: solo pixel pieni, quindi zero anti-aliasing.
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
            if src[x, y][3] > 0:
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
                    if nx < xlo or nx > xhi or opaque[ny][nx]:
                        continue
                    if dst[nx, ny][3] == 0:
                        dst[nx, ny] = edge
    return out


def finish(img: Image.Image, name: str) -> None:
    save_png(outlined(img), OUT / f"{name}.png")


# Font bitmap 3x5: maiuscole e cifre, senza anti-aliasing.
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
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("110", "001", "010", "100", "111"),
    "3": ("110", "001", "010", "001", "110"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "110", "101", "010"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("010", "101", "010", "101", "010"),
    "9": ("010", "101", "011", "001", "110"),
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


class Grid:
    """Griglia simbolica: ogni cella e' un token di palette o '.' (vuoto).

    `flip` speculare l'asse X: i profili vengono disegnati una sola volta
    verso sinistra e riflessi per la direzione destra.
    """

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.cells = [["." for _ in range(w)] for _ in range(h)]
        self.flip = False

    def _x(self, x: int) -> int:
        return self.w - 1 - x if self.flip else x

    def px(self, x: int, y: int, token: str) -> None:
        xx = self._x(int(x))
        if 0 <= xx < self.w and 0 <= y < self.h and token != ".":
            self.cells[y][xx] = token

    def span(self, y: int, x0: int, x1: int, token: str) -> None:
        if x1 < x0:
            x0, x1 = x1, x0
        for x in range(int(x0), int(x1) + 1):
            self.px(x, y, token)

    def col(self, x: int, y0: int, y1: int, token: str) -> None:
        for y in range(int(y0), int(y1) + 1):
            self.px(x, y, token)

    def box(self, x0: int, y0: int, x1: int, y1: int, token: str) -> None:
        for y in range(int(y0), int(y1) + 1):
            self.span(y, x0, x1, token)

    def image(self, colors: dict[str, tuple]) -> Image.Image:
        img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        px = img.load()
        for y, row in enumerate(self.cells):
            for x, token in enumerate(row):
                if token != ".":
                    px[x, y] = colors[token]
        return img


# ---------------------------------------------------------------------------
# Personaggi: 7 varianti, 4 direzioni x 4 frame, cella 16x32, piedi a y=30
# ---------------------------------------------------------------------------

CHARS = {
    "player":   {"skin": P["skin1"], "hair": P["hair2"], "shirt": shade(P["eav_light"], 0.85),
                 "pants": shade(P["ink_soft"], 0.90), "shoes": dim(P["ink"], 0.90),
                 "acc": "satchel", "hair_style": "short"},
    "resident": {"skin": P["skin2"], "hair": P["hair1"], "shirt": P["terra"],
                 "pants": shade(P["green_dark"], 0.95), "shoes": dim(P["ink"], 0.85),
                 "acc": "none", "hair_style": "long"},
    "worker":   {"skin": P["skin3"], "hair": P["hair3"], "shirt": P["yellow"],
                 "pants": shade(P["metal"], 0.75), "shoes": P["ink"],
                 "acc": "hardhat", "hair_style": "short"},
    "elderly":  {"skin": P["skin1"], "hair": P["concrete_light"], "shirt": shade(P["green"], 0.90),
                 "pants": shade(P["brown"], 0.75), "shoes": dim(P["ink"], 0.90),
                 "acc": "cane", "hair_style": "thin"},
    "teen":     {"skin": P["skin2"], "hair": P["hair1"], "shirt": P["stucco_pink"],
                 "pants": dim(P["ink_soft"], 0.80), "shoes": dim(P["ink"], 0.80),
                 "acc": "cap", "hair_style": "short"},
    "railway":  {"skin": P["skin1"], "hair": P["hair1"], "shirt": P["eav_blue"],
                 "pants": shade(P["eav_blue"], 0.60), "shoes": dim(P["ink"], 0.90),
                 "acc": "uniform", "hair_style": "short"},
    "vendor":   {"skin": P["skin2"], "hair": P["hair3"], "shirt": P["white"],
                 "pants": P["brown"], "shoes": dim(P["ink"], 0.90),
                 "acc": "apron", "hair_style": "bun"},
}

SWING = (0, 1, 0, -1)    # passo: gamba avanti / indietro
BOUNCE = (0, -1, 0, -1)  # rimbalzo del busto; i piedi restano a y=30

# (pants sinistra, scarpa sinistra, pantalone destro, scarpa destra)
LEG_FRAMES = (
    ((3, 6), (3, 7), (9, 11), (9, 12)),
    ((4, 7), (4, 8), (9, 11), (9, 12)),
    ((5, 7), (5, 9), (9, 11), (9, 12)),
    ((4, 7), (4, 8), (9, 11), (9, 12)),
)


def char_colors(pal: dict) -> dict[str, tuple]:
    """Mappa i token della griglia sulla palette e sulle sue derivate."""
    skin, hair = pal["skin"], pal["hair"]
    shirt, pants, shoes = pal["shirt"], pal["pants"], pal["shoes"]
    return {
        "s": rgba(skin), "S": rgba(dim(skin, 1.12)), "d": rgba(dim(skin, 0.78)),
        "h": rgba(hair), "H": rgba(dim(hair, 1.22)), "l": rgba(dim(hair, 0.70)),
        "c": rgba(shirt), "C": rgba(dim(shirt, 1.14)), "D": rgba(dim(shirt, 0.76)),
        "p": rgba(pants), "P": rgba(dim(pants, 1.12)), "q": rgba(dim(pants, 0.72)),
        "t": rgba(shoes), "T": rgba(dim(shoes, 1.30)),
        "o": rgba(P["ink"]), "O": rgba(P["ink_soft"]),
        "w": rgba(P["white"]), "W": rgba(dim(P["white"], 0.80)),
        "y": rgba(P["yellow"]), "Y": rgba(dim(P["yellow"], 1.18)),
        "r": rgba(P["red"]), "b": rgba(P["brown"]), "B": rgba(dim(P["brown"], 1.20)),
        "m": rgba(P["metal"]), "M": rgba(P["metal_light"]),
        "v": rgba(P["eav_blue"]), "L": rgba(P["eav_light"]),
        "g": rgba(P["green"]), "G": rgba(P["green_dark"]),
        "n": rgba(P["wood"]), "N": rgba(dim(P["wood"], 1.16)),
        "e": rgba(P["terra"]), "f": rgba(P["terra_dark"]),
    }


def draw_legs(g: Grid, frame: int, direction: int) -> None:
    (lp0, lp1), (ls0, ls1), (rp0, rp1), (rs0, rs1) = LEG_FRAMES[frame]
    # Gamba posteriore: sempre piu' scura, anche nelle viste frontali.
    g.box(rp0, 23, rp1, 28, "q")
    g.span(27, rp0, rp1, "q")
    g.span(29, rs0, rs1, "t")
    g.span(30, rs0, rs1, "t")
    g.px(rs0 + 1, 29, "T")
    # Gamba anteriore: piega del ginocchio sui frame di passo.
    g.box(lp0, 23, lp1, 28, "p")
    g.col(lp0, 23, 27, "P")
    if frame in (1, 3):
        g.span(27, lp0, lp1, "q")
    g.span(29, ls0, ls1, "t")
    g.span(30, ls0, ls1, "t")
    g.span(29, ls0, ls0 + 1, "T")
    if direction in (1, 2):
        g.span(28, rs0, rs1, "q")


def draw_arms(g: Grid, direction: int, frame: int, bob: int) -> None:
    swing = SWING[frame]
    if direction in (1, 2):
        # Profilo: braccio lontano piu' scuro, braccio vicino in primo piano.
        arms = ((3, -swing, "D", "d"), (11, swing, "c", "s"))
    else:
        arms = ((2, -swing, "C", "s"), (12, swing, "D", "d"))
    for x0, dy, sleeve, hand in arms:
        y0 = 14 + bob + dy
        g.box(x0, y0, x0 + 1, y0 + 6, sleeve)
        g.box(x0, y0 + 7, x0 + 1, y0 + 8, hand)
        g.px(x0 + 1, y0 + 7, "S" if hand == "s" else "d")


def draw_torso(g: Grid, direction: int, bob: int, name: str) -> None:
    ty = 13 + bob
    g.span(ty, 5, 10, "C")
    g.box(4, ty + 1, 11, 21, "c")
    g.col(4, ty + 1, 21, "C")          # luce da alto-sinistra
    g.col(11, ty + 1, 21, "D")         # ombra destra
    g.px(5, ty + 2, "C")
    g.px(10, ty + 2, "D")
    # Pieghe strutturali della veste, non pixel sparsi.
    g.px(6, ty + 4, "D")
    g.px(7, ty + 5, "D")
    g.px(8, ty + 6, "D")
    g.px(9, ty + 3, "D")
    g.span(ty + 1, 6, 7, "C")          # colletto
    g.span(ty + 1, 9, 10, "C")
    g.box(8, ty + 3, 9, ty + 4, "D")   # tasca
    g.px(8, ty + 3, "C")
    # Cintura e fibbia: anch'essa ancorata a y=22.
    g.span(22, 4, 11, "O")
    g.span(22, 7, 8, "y")
    if name == "worker":
        g.span(ty + 4, 4, 11, "M")     # bande reflexive da cantiere
        g.span(ty + 7, 4, 11, "M")
    if name == "teen":
        g.col(5, ty + 1, ty + 4, "b")  # tracolle dello zaino
        g.col(10, ty + 1, ty + 4, "b")


def draw_head(g: Grid, direction: int, bob: int, hair_style: str) -> None:
    hy = 3 + bob
    if direction == 3:
        # Schiena: capelli pieni, nuca e collo, nessun volto.
        g.span(hy, 5, 10, "h")
        g.span(hy + 1, 4, 11, "h")
        g.span(hy + 1, 5, 7, "H")
        g.span(hy + 1, 10, 11, "l")
        for yy in range(hy + 2, hy + 7):
            g.span(yy, 4, 11, "h")
        g.col(4, hy + 2, hy + 5, "H")
        g.col(11, hy + 2, hy + 6, "l")
        g.px(6, hy + 3, "H")
        g.span(hy + 7, 5, 10, "l")
    elif direction == 0:
        # Fronte: frangia, sopracciglia, occhi, naso, bocca e orecchie.
        g.span(hy, 5, 10, "h")
        g.span(hy + 1, 4, 11, "h")
        g.span(hy + 1, 5, 7, "H")
        g.span(hy + 1, 10, 11, "l")
        g.span(hy + 2, 4, 11, "h")
        g.span(hy + 2, 4, 5, "H")
        g.span(hy + 2, 10, 11, "l")
        g.span(hy + 3, 4, 11, "s")
        g.px(3, hy + 3, "s")
        g.px(12, hy + 3, "s")
        g.span(hy + 3, 4, 5, "S")
        g.span(hy + 3, 10, 11, "d")
        g.span(hy + 3, 5, 6, "l")
        g.span(hy + 3, 9, 10, "l")
        g.span(hy + 4, 4, 11, "s")
        g.px(3, hy + 4, "d")
        g.px(12, hy + 4, "S")
        g.span(hy + 4, 4, 5, "S")
        g.span(hy + 4, 10, 11, "d")
        g.px(6, hy + 4, "o")
        g.px(9, hy + 4, "o")
        g.span(hy + 5, 4, 11, "s")
        g.px(5, hy + 5, "S")
        g.px(10, hy + 5, "d")
        g.px(6, hy + 5, "o")
        g.px(9, hy + 5, "o")
        g.span(hy + 6, 4, 11, "s")
        g.span(hy + 6, 7, 8, "d")
        g.px(5, hy + 6, "S")
        g.px(10, hy + 6, "d")
        g.span(hy + 7, 5, 10, "s")
        g.span(hy + 7, 5, 6, "S")
        g.span(hy + 7, 9, 10, "d")
        g.span(hy + 7, 7, 8, "O")
    else:
        # Profilo disegnato verso sinistra; Grid.flip lo riflette a destra.
        g.span(hy, 5, 10, "h")
        g.span(hy + 1, 4, 11, "h")
        g.span(hy + 1, 6, 9, "H")
        g.px(11, hy + 1, "l")
        g.span(hy + 2, 5, 11, "h")
        g.span(hy + 2, 7, 9, "H")
        g.px(11, hy + 2, "l")
        g.span(hy + 3, 4, 10, "s")
        g.span(hy + 3, 4, 5, "S")
        g.px(8, hy + 3, "d")
        g.span(hy + 3, 9, 11, "h")
        g.px(3, hy + 3, "S")
        g.span(hy + 4, 4, 10, "s")
        g.px(3, hy + 4, "S")
        g.px(5, hy + 4, "o")
        g.px(8, hy + 4, "d")
        g.span(hy + 4, 9, 11, "h")
        g.span(hy + 5, 4, 10, "s")
        g.px(3, hy + 5, "S")
        g.px(5, hy + 5, "o")
        g.px(8, hy + 5, "d")
        g.span(hy + 5, 10, 11, "h")
        g.span(hy + 6, 3, 9, "s")
        g.px(3, hy + 6, "S")
        g.px(4, hy + 6, "O")
        g.px(6, hy + 6, "S")
        g.span(hy + 6, 9, 10, "h")
        g.span(hy + 7, 4, 9, "s")
        g.span(hy + 7, 4, 5, "S")
        g.px(9, hy + 7, "d")

    # Acconciature coerenti con l'identita' del personaggio.
    if hair_style == "long":
        if direction in (0, 3):
            g.col(3, hy + 3, hy + 7, "h")
            g.col(12, hy + 3, hy + 7, "l")
        else:
            g.col(10, hy + 4, hy + 7, "h")
            g.col(11, hy + 4, hy + 7, "l")
    elif hair_style == "thin" and direction == 0:
        g.span(hy + 3, 4, 5, "s")
        g.span(hy + 3, 10, 11, "s")
    elif hair_style == "bun":
        if direction == 3:
            g.box(11, hy + 1, 13, hy + 3, "h")
            g.px(12, hy + 2, "H")
        else:
            g.box(10, hy, 12, hy + 2, "h")
            g.px(11, hy + 1, "H")

    # Collo: due righe, coperte dal busto quando il frame e' abbassato.
    g.span(hy + 8, 7, 8, "s")
    g.span(hy + 9, 7, 8, "d")


def draw_accessory(g: Grid, pal: dict, direction: int, bob: int, name: str) -> None:
    acc = pal["acc"]
    hy = 3 + bob
    ty = 13 + bob

    if acc == "satchel":
        g.span(ty + 1, 5, 10, "r")       # sciarpa rossa del giocatore
        for i in range(7):               # tracolla: dal collo all'anca
            g.px(6 + (i * 4) // 6, ty + 1 + i, "b")
        g.box(11, ty + 6, 13, ty + 9, "b")
        g.span(ty + 6, 11, 13, "B")
        g.px(12, ty + 7, "y")

    elif acc == "hardhat":
        g.span(hy - 2, 5, 10, "y")
        g.span(hy - 1, 4, 11, "y")
        g.span(hy - 1, 6, 7, "Y")
        g.span(hy, 3, 12, "B")           # visiera
        g.span(hy, 4, 10, "y")

    elif acc == "cane":
        g.col(13, 21, 29, "n")           # bastone da passeggio
        g.col(14, 22, 29, "B")
        g.span(20, 12, 14, "n")          # manico a gomito
        g.span(21, 13, 14, "B")
        g.px(12, 21, "s")

    elif acc == "cap":
        g.span(hy - 1, 5, 10, "r")
        g.span(hy, 4, 11, "r")
        g.span(hy - 1, 7, 8, "B")
        if direction != 3:
            if direction == 1:
                g.span(hy + 2, 2, 7, "B")   # visiera verso sinistra
            else:
                g.span(hy + 2, 3, 12, "B")

    elif acc == "uniform":
        g.span(hy - 1, 5, 10, "v")       # berretto EAV
        g.span(hy, 4, 11, "v")
        g.span(hy, 5, 10, "y")           # fascia dorata
        if direction == 1:
            g.span(hy + 2, 2, 7, "O")
        elif direction != 3:
            g.span(hy + 2, 3, 12, "O")
        # Gilet ad alta visibilita' con bande riflettenti.
        g.box(5, ty + 2, 10, ty + 8, "y")
        g.span(ty + 4, 5, 10, "w")
        g.span(ty + 7, 5, 10, "w")
        g.col(5, ty + 2, ty + 8, "B")
        g.col(10, ty + 2, ty + 8, "B")
        g.box(12, ty + 4, 13, ty + 6, "o")   # radio di servizio
        g.px(13, ty + 3, "m")

    elif acc == "apron":
        g.span(hy - 2, 6, 9, "y")        # cappello di paglia da barista
        g.span(hy - 1, 5, 10, "y")
        g.span(hy - 1, 7, 8, "Y")
        g.span(hy, 3, 12, "B")
        g.span(hy, 4, 11, "y")
        g.col(5, ty, ty + 1, "w")        # bretelle
        g.col(10, ty, ty + 1, "w")
        g.box(5, ty + 2, 10, ty + 9, "w")
        g.col(5, ty + 2, ty + 9, "W")
        g.col(10, ty + 2, ty + 9, "W")
        g.box(6, ty + 5, 8, ty + 6, "e") # tasca del grembiule
        g.span(ty + 8, 5, 10, "f")       # nastro in vita


def character_cell(name: str, direction: int, frame: int) -> Image.Image:
    pal = CHARS[name]
    bob = BOUNCE[frame]
    img = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    contact(d, 3, 29, 12, 31)

    g = Grid(FW, FH)
    g.flip = direction == 2
    draw_legs(g, frame, direction)
    draw_arms(g, direction, frame, bob)
    draw_torso(g, direction, bob, name)
    draw_head(g, direction, bob, pal["hair_style"])
    draw_accessory(g, pal, direction, bob, name)

    img.alpha_composite(g.image(char_colors(pal)))
    return outlined(img, (1, FW - 2, 0, FEET_Y))


def make_characters() -> None:
    for key in CHARS:
        sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))
        for row in range(SHEET_ROWS):
            for frame in range(SHEET_COLUMNS):
                sheet.paste(character_cell(key, row, frame), (frame * FW, row * FH))
        save_png(sheet, OUT / f"{key}.png")


# ---------------------------------------------------------------------------
# Veicoli: vista 3/4 dall'alto, orientati a destra a rotazione 0
# ---------------------------------------------------------------------------

def make_car(name: str, base, hi, lo) -> None:
    img, d = start(72, 40)
    contact(d, 5, 32, 67, 37)

    # Ruote lontane: intraviste sopra la carrozzeria.
    for wx in (12, 48):
        ellipse(d, wx, 8, wx + 12, 18, rgba(P["ink"]))
        ellipse(d, wx + 2, 10, wx + 10, 16, rgba(P["metal"]))
        ellipse(d, wx + 4, 11, wx + 8, 15, rgba(P["metal_light"]))

    # Carrozzeria: cofano anteriore a destra, bagagliaio a sinistra.
    poly(d, [(4, 17), (8, 12), (13, 8), (17, 6), (53, 6), (60, 8),
             (67, 12), (70, 16), (70, 24), (67, 28), (60, 32), (54, 34),
             (16, 34), (10, 31), (5, 27)], base)
    poly(d, [(17, 30), (53, 30), (60, 28), (64, 25), (63, 31),
             (54, 35), (16, 35), (9, 32)], lo)
    poly(d, [(10, 13), (16, 9), (54, 9), (62, 12), (65, 16),
             (18, 16)], hi)

    # Abitacolo: cornice scura, vetri incassati e riflessi netti.
    poly(d, [(19, 12), (25, 9), (47, 9), (53, 12), (55, 17), (55, 24),
             (52, 29), (47, 31), (25, 31), (19, 28), (17, 23), (17, 17)],
         rgba(P["ink_soft"]))
    poly(d, [(20, 12), (25, 10), (47, 10), (52, 13), (54, 17), (54, 24),
             (51, 28), (47, 30), (25, 30), (20, 27), (18, 22), (18, 17)],
         rgba(P["glass"]))
    poly(d, [(20, 12), (25, 10), (25, 25), (20, 27), (19, 21)], rgba(P["glass"]))
    poly(d, [(27, 11), (33, 11), (33, 29), (27, 29)], rgba(P["glass"]))
    poly(d, [(35, 11), (46, 11), (47, 29), (35, 29)], rgba(P["glass"]))
    poly(d, [(48, 11), (52, 13), (53, 18), (48, 18)], rgba(P["glass"]))
    rect(d, 28, 12, 29, 17, rgba(P["glass_light"]))
    rect(d, 36, 12, 40, 14, rgba(P["glass_light"]))
    rect(d, 36, 24, 41, 25, rgba(P["glass_light"]))
    rect(d, 20, 14, 21, 20, rgba(P["glass_light"]))
    rect(d, 49, 12, 52, 14, rgba(P["glass_light"]))
    line(d, [(48, 18), (53, 18)], rgba(P["ink_soft"]), 1)  # tergicristallo

    # Portiere, maniglie, specchietti, griglia e fanali.
    line(d, [(34, 10), (34, 30)], lo, 1)
    line(d, [(58, 10), (58, 30)], lo, 1)
    rect(d, 30, 17, 33, 18, rgba(P["ink_soft"]))
    rect(d, 30, 25, 33, 26, rgba(P["ink_soft"]))
    poly(d, [(54, 14), (60, 12), (61, 15), (55, 17)], hi)
    poly(d, [(54, 24), (60, 26), (61, 29), (55, 27)], lo)
    rect(d, 58, 9, 61, 10, rgba(P["metal_light"]))
    rect(d, 66, 18, 70, 22, rgba(P["ink"]))
    rect(d, 67, 19, 67, 21, rgba(P["metal_light"]))
    rect(d, 69, 19, 69, 21, rgba(P["metal_light"]))
    rect(d, 65, 13, 69, 16, rgba(P["white"]))
    rect(d, 67, 14, 69, 15, rgba(P["yellow"]))
    rect(d, 65, 24, 69, 27, rgba(P["white"]))
    rect(d, 67, 25, 69, 26, rgba(P["yellow"]))
    rect(d, 70, 19, 71, 21, rgba(P["white"]))
    rect(d, 4, 14, 7, 17, rgba(P["red"]))
    rect(d, 4, 24, 7, 27, rgba(P["red"]))
    rect(d, 4, 18, 6, 19, rgba(P["glass_light"]))
    rect(d, 4, 22, 6, 23, rgba(P["glass_light"]))
    rect(d, 59, 8, 63, 9, lo)            # sfiatatoi sul cofano
    line(d, [(42, 6), (42, 4)], rgba(P["metal"]), 1)  # antenna

    # Ruote vicine: arco scuro, pneumatico, cerchio e mozzo.
    for wx in (12, 48):
        rect(d, wx + 1, 29, wx + 11, 30, rgba(P["ink_soft"]))
        ellipse(d, wx, 30, wx + 12, 40, rgba(P["ink"]))
        ellipse(d, wx + 2, 32, wx + 10, 38, rgba(P["metal"]))
        ellipse(d, wx + 4, 33, wx + 8, 37, rgba(P["metal_light"]))
        rect(d, wx + 5, 34, wx + 7, 36, rgba(P["ink_soft"]))
    finish(img, name)


def make_bus() -> None:
    img, d = start(112, 44)
    base = shade(P["green_dark"], 0.95)
    hi = shade(P["green"], 0.90)
    lo = shade(P["green_dark"], 0.70)
    contact(d, 6, 37, 106, 42)

    for wx in (16, 84):
        ellipse(d, wx, 32, wx + 12, 41, rgba(P["ink"]))
        ellipse(d, wx + 2, 34, wx + 10, 40, rgba(P["metal"]))
        ellipse(d, wx + 4, 35, wx + 8, 39, rgba(P["metal_light"]))
        rect(d, wx + 5, 36, wx + 7, 38, rgba(P["ink_soft"]))

    poly(d, [(8, 11), (14, 7), (20, 5), (98, 5), (105, 9),
             (110, 14), (110, 28), (105, 33), (98, 37), (14, 37),
             (8, 32), (4, 26), (4, 16)], base)
    poly(d, [(12, 34), (100, 34), (105, 30), (105, 36), (98, 39),
             (14, 39), (7, 34)], lo)
    rect(d, 16, 5, 101, 8, hi)           # tetto in lamiera
    rect(d, 20, 4, 96, 5, shade(P["metal_light"], 0.95))
    for vx in range(26, 96, 16):
        rect(d, vx, 6, vx + 5, 7, lo)    # griglie di ventilazione

    # Finestrini regolari con riflesso inclinato.
    for wx in range(16, 101, 13):
        rect(d, wx, 11, wx + 9, 21, rgba(P["ink_soft"]))
        rect(d, wx + 1, 12, wx + 8, 20, rgba(P["glass"]))
        rect(d, wx + 1, 12, wx + 8, 14, rgba(P["glass_light"]))
        rect(d, wx + 1, 15, wx + 3, 18, rgba(P["glass_light"]))

    # Due porte a doppia anta, con vetro e pedana.
    for px in (29, 69):
        rect(d, px, 11, px + 10, 32, lo)
        rect(d, px + 1, 12, px + 4, 21, rgba(P["glass"]))
        rect(d, px + 6, 12, px + 9, 21, rgba(P["glass"]))
        rect(d, px + 1, 12, px + 4, 14, rgba(P["glass_light"]))
        rect(d, px + 6, 12, px + 9, 14, rgba(P["glass_light"]))
        line(d, [(px + 5, 12), (px + 5, 32)], rgba(P["ink"]), 1)
        rect(d, px + 1, 33, px + 9, 35, rgba(P["metal_light"]))

    rect(d, 10, 23, 104, 24, rgba(P["yellow"]))     # fascia ANM
    tiny_text(d, 47, 26, "ANM", rgba(P["white"]))
    rect(d, 86, 6, 107, 11, rgba(P["ink"]))         # insegna destinazione
    tiny_text(d, 87, 7, "NAPOLI", rgba(P["yellow"]))
    poly(d, [(104, 13), (110, 12), (110, 16), (104, 17)], hi)  # specchietto
    rect(d, 101, 5, 104, 6, rgba(P["metal_light"]))
    rect(d, 106, 19, 110, 22, rgba(P["white"]))     # fari
    rect(d, 108, 20, 110, 21, rgba(P["yellow"]))
    rect(d, 106, 27, 110, 30, rgba(P["red"]))
    rect(d, 4, 16, 7, 19, rgba(P["red"]))
    rect(d, 4, 26, 7, 29, rgba(P["red"]))
    rect(d, 108, 33, 110, 35, rgba(P["white"]))     # targa
    rect(d, 4, 19, 7, 21, rgba(P["metal_light"]))
    finish(img, "bus")


def make_scooter() -> None:
    img, d = start(52, 34)
    base = shade(P["metal_light"], 0.95)
    hi = shade(P["metal_light"], 1.10)
    lo = shade(P["metal"], 0.80)
    contact(d, 4, 29, 48, 33)

    for wx, wy in ((7, 21), (33, 21)):
        ellipse(d, wx, wy, wx + 12, wy + 12, rgba(P["ink"]))
        ellipse(d, wx + 2, wy + 2, wx + 10, wy + 10, rgba(P["metal"]))
        ellipse(d, wx + 4, wy + 4, wx + 8, wy + 8, rgba(P["metal_light"]))
        rect(d, wx + 5, wy + 5, wx + 7, wy + 7, rgba(P["ink_soft"]))

    poly(d, [(11, 19), (35, 19), (40, 22), (38, 27), (14, 27), (10, 24)], base)
    poly(d, [(14, 24), (37, 24), (38, 27), (14, 27)], lo)
    rect(d, 17, 23, 34, 24, hi)          # pedana
    poly(d, [(36, 20), (42, 9), (48, 8), (50, 21), (46, 26), (40, 25)], base)
    poly(d, [(43, 10), (47, 9), (48, 20), (44, 21)], hi)
    line(d, [(40, 25), (36, 20)], lo, 1)

    rect(d, 9, 14, 23, 18, rgba(P["ink"]))          # sella
    rect(d, 11, 14, 21, 15, rgba(P["ink_soft"]))
    line(d, [(12, 17), (20, 17)], rgba(P["metal_light"]), 1)  # cucitura
    rect(d, 8, 18, 11, 20, lo)           # portapacchi posteriore
    rect(d, 5, 17, 8, 18, rgba(P["metal_light"]))

    rect(d, 40, 6, 50, 8, rgba(P["ink"]))           # manubrio
    rect(d, 42, 5, 48, 6, rgba(P["metal_light"]))
    line(d, [(46, 7), (47, 3)], lo, 1)
    ellipse(d, 45, 2, 49, 5, rgba(P["ink"]))        # specchietto
    ellipse(d, 46, 3, 48, 4, rgba(P["metal_light"]))
    ellipse(d, 45, 12, 50, 17, rgba(P["white"]))    # faro
    ellipse(d, 46, 13, 49, 16, rgba(P["yellow"]))
    rect(d, 9, 17, 12, 19, rgba(P["red"]))
    rect(d, 12, 11, 16, 14, rgba(P["eav_blue"]))    # targa laterale
    rect(d, 13, 12, 15, 12, rgba(P["white"]))
    finish(img, "scooter")


def make_train() -> None:
    """Treno EAV Circumflegrea: due casse, 36 m (576 px), asse orizzontale."""
    img, d = start(576, 56)
    car_w, gap = 280, 16

    for ci in range(2):
        x0 = ci * (car_w + gap)
        contact(d, x0 + 8, 46, x0 + 272, 54)

        # Carrelli: telaio, quattro ruote, molle e gancio.
        for bx in (x0 + 40, x0 + 200):
            rect(d, bx, 42, bx + 42, 50, rgba(P["ink_soft"]))
            rect(d, bx + 2, 43, bx + 40, 44, rgba(P["metal"]))
            for wx in (bx + 5, bx + 16, bx + 27, bx + 38):
                ellipse(d, wx, 45, wx + 6, 51, rgba(P["ink"]))
                ellipse(d, wx + 2, 47, wx + 4, 49, rgba(P["metal_light"]))
            rect(d, bx + 9, 50, bx + 33, 52, rgba(P["ink"]))
            for sx in (bx + 12, bx + 30):
                rect(d, sx, 40, sx + 2, 43, rgba(P["metal_light"]))

        # Cassa e tetto: la vista resta di lato, senza rotazione.
        poly(d, [(x0 + 6, 14), (x0 + 14, 10), (x0 + 266, 10), (x0 + 274, 14),
                 (x0 + 274, 38), (x0 + 266, 44), (x0 + 14, 44), (x0 + 6, 38)],
             rgba(P["eav_blue"]))
        rect(d, x0 + 10, 9, x0 + 270, 12, rgba(shade(P["eav_blue"], 1.28)))
        rect(d, x0 + 14, 7, x0 + 266, 9, rgba(shade(P["eav_blue"], 1.42)))
        rect(d, x0 + 8, 38, x0 + 272, 41, rgba(shade(P["eav_blue"], 0.62)))
        rect(d, x0 + 8, 31, x0 + 272, 33, rgba(P["white"]))
        rect(d, x0 + 8, 34, x0 + 272, 37, rgba(P["yellow"]))
        rect(d, x0 + 8, 41, x0 + 272, 42, rgba(P["ink_soft"]))

        # Griglie del tetto, allineate ai carrelli.
        for vx in (x0 + 50, x0 + 210):
            rect(d, vx, 6, vx + 22, 8, rgba(P["ink_soft"]))
            for gx in range(vx + 2, vx + 21, 4):
                rect(d, gx, 7, gx + 1, 7, rgba(P["metal_light"]))

        # Finestre a passo regolare: cornice, vetro, riflesso, sedili.
        for k in range(6):
            wx = x0 + 30 + 38 * k
            rect(d, wx, 15, wx + 29, 30, rgba(P["ink_soft"]))
            rect(d, wx + 1, 16, wx + 28, 29, rgba(P["glass"]))
            rect(d, wx + 1, 16, wx + 12, 20, rgba(P["glass_light"]))
            rect(d, wx + 1, 21, wx + 3, 26, rgba(P["glass_light"]))
            rect(d, wx + 17, 26, wx + 26, 27, rgba(shade(P["glass"], 0.72)))

        # Porte a due ante con vetro diviso.
        for dx in (x0 + 8, x0 + 254):
            rect(d, dx, 15, dx + 18, 31, rgba(shade(P["eav_blue"], 0.72)))
            rect(d, dx + 2, 17, dx + 8, 28, rgba(P["glass"]))
            rect(d, dx + 10, 17, dx + 16, 28, rgba(P["glass"]))
            rect(d, dx + 2, 17, dx + 5, 20, rgba(P["glass_light"]))
            rect(d, dx + 10, 17, dx + 13, 20, rgba(P["glass_light"]))
            line(d, [(dx + 9, 16), (dx + 9, 30)], rgba(P["ink"]), 1)

        tiny_text(d, x0 + 126, 35, "EAV", rgba(P["eav_blue"]))
        rect(d, x0 + 258, 12, x0 + 271, 16, rgba(P["ink"]))
        tiny_text(d, x0 + 259, 13, "EAV", rgba(P["yellow"]))

        # Testate: fanali, paraurti e targa.
        rect(d, x0 + 4, 19, x0 + 7, 23, rgba(P["yellow"]))
        rect(d, x0 + 268, 19, x0 + 271, 23, rgba(P["red"]))
        rect(d, x0 + 6, 25, x0 + 13, 27, rgba(P["white"]))
        rect(d, x0 + 263, 25, x0 + 270, 27, rgba(P["ink_soft"]))

    # Gancio intercassa e pantografo sulla prima cassa.
    rect(d, car_w, 25, car_w + gap, 29, rgba(P["ink_soft"]))
    rect(d, car_w + 3, 26, car_w + 13, 28, rgba(P["metal"]))
    line(d, [(car_w + 12, 28), (car_w + 12, 32)], rgba(P["ink"]), 1)
    rect(d, 118, 9, 142, 10, rgba(P["ink_soft"]))
    line(d, [(122, 9), (132, 2), (142, 9)], rgba(P["metal_light"]), 2)
    line(d, [(128, 9), (138, 2), (146, 9)], rgba(P["metal"]), 1)
    rect(d, 130, 1, 140, 3, rgba(P["ink_soft"]))
    rect(d, 132, 1, 138, 2, rgba(P["metal_light"]))
    finish(img, "train_eav")


# ---------------------------------------------------------------------------
# Arredo urbano e oggetti di missione (dimensioni esatte da ART_SPEC.md)
# ---------------------------------------------------------------------------

def make_props() -> None:
    # Lampione 24x76
    img, d = start(24, 76)
    contact(d, 3, 72, 21, 75)
    rect(d, 6, 71, 18, 74, rgba(P["ink_soft"]))       # basamento
    rect(d, 8, 69, 16, 71, rgba(P["metal"]))
    rect(d, 11, 14, 13, 69, rgba(P["metal"]))         # fusto
    rect(d, 11, 14, 11, 69, rgba(P["metal_light"]))
    rect(d, 13, 20, 13, 69, rgba(P["ink_soft"]))
    for by in (26, 40, 54, 66):                       # giunti del fusto
        rect(d, 10, by, 14, by + 1, rgba(P["metal_light"]))
    line(d, [(12, 14), (12, 8), (19, 8)], rgba(P["metal"]), 2)
    line(d, [(12, 8), (19, 8)], rgba(P["metal_light"]), 1)
    poly(d, [(17, 8), (22, 9), (22, 16), (17, 15)], rgba(P["ink"]))
    rect(d, 19, 10, 21, 14, rgba(P["yellow"]))        # vetro
    rect(d, 19, 10, 20, 11, rgba(P["white"]))
    rect(d, 19, 6, 21, 8, rgba(P["ink_soft"]))        # cappello
    rect(d, 20, 4, 20, 5, rgba(P["metal_light"]))
    finish(img, "lamp")

    # Bidone 20x26
    img, d = start(20, 26)
    contact(d, 2, 23, 18, 25)
    rect(d, 3, 7, 17, 23, rgba(shade(P["green_dark"], 0.95)))
    rect(d, 4, 8, 5, 22, rgba(shade(P["green"], 0.85)))
    rect(d, 13, 8, 16, 22, rgba(shade(P["green_dark"], 0.72)))
    for ry in (11, 15, 19):
        rect(d, 4, ry, 16, ry, rgba(shade(P["green_dark"], 0.80)))
    rect(d, 2, 4, 18, 8, rgba(P["ink_soft"]))
    rect(d, 3, 4, 17, 5, rgba(P["green"]))
    rect(d, 8, 2, 12, 4, rgba(P["metal"]))
    rect(d, 9, 3, 11, 3, rgba(P["metal_light"]))
    rect(d, 7, 12, 13, 15, rgba(P["white"]))
    rect(d, 8, 13, 12, 13, rgba(P["green_dark"]))
    rect(d, 9, 22, 11, 24, rgba(P["metal_light"]))    # pedale
    finish(img, "bin")

    # Panchina 56x26
    img, d = start(56, 26)
    contact(d, 3, 23, 53, 25)
    for sy in (4, 9):
        rect(d, 6, sy, 52, sy + 3, rgba(P["wood"]))
        rect(d, 6, sy, 52, sy, rgba(shade(P["wood"], 1.15)))
        rect(d, 6, sy + 3, 52, sy + 3, rgba(shade(P["wood"], 0.70)))
        for gx in (12, 26, 40):                        # venature del legno
            rect(d, gx, sy + 1, gx + 4, sy + 1, rgba(shade(P["wood"], 0.86)))
    rect(d, 3, 14, 53, 18, rgba(P["wood"]))
    rect(d, 3, 14, 53, 14, rgba(shade(P["wood"], 1.15)))
    rect(d, 3, 18, 53, 19, rgba(shade(P["wood"], 0.72)))
    for gx in (9, 24, 39):
        rect(d, gx, 16, gx + 5, 16, rgba(shade(P["wood"], 0.86)))
    for lx in (7, 44):
        rect(d, lx, 5, lx + 2, 24, rgba(P["metal"]))
        rect(d, lx, 5, lx, 24, rgba(P["metal_light"]))
        rect(d, lx - 1, 5, lx + 3, 6, rgba(P["ink_soft"]))
    line(d, [(10, 21), (44, 21)], rgba(P["metal"]), 1)  # traversa
    rect(d, 6, 24, 12, 25, rgba(P["ink_soft"]))
    rect(d, 44, 24, 50, 25, rgba(P["ink_soft"]))
    finish(img, "bench")

    # Albero 64x88
    img, d = start(64, 88)
    contact(d, 8, 83, 56, 86)
    poly(d, [(28, 44), (35, 44), (37, 84), (26, 84)], rgba(P["brown"]))
    rect(d, 34, 46, 36, 83, rgba(shade(P["brown"], 0.75)))
    rect(d, 28, 46, 29, 83, rgba(shade(P["brown"], 1.15)))
    for by in (54, 66, 78):                            # scorza
        rect(d, 31, by, 32, by + 1, rgba(shade(P["brown"], 0.70)))
    line(d, [(31, 62), (24, 52)], shade(P["brown"], 0.85), 2)
    line(d, [(33, 56), (41, 47)], shade(P["brown"], 0.85), 2)
    line(d, [(30, 50), (20, 44)], shade(P["brown"], 0.85), 2)
    for cx, cy, r in ((32, 36, 20), (19, 43, 13), (45, 42, 14),
                      (32, 20, 14), (23, 27, 11), (42, 27, 12)):
        ellipse(d, cx - r, cy - r, cx + r, cy + r, rgba(shade(P["green_dark"], 0.95)))
    for cx, cy, r in ((30, 34, 16), (19, 41, 10), (44, 40, 11), (32, 21, 11)):
        ellipse(d, cx - r, cy - r, cx + r, cy + r, rgba(P["green"]))
    for cx, cy, r in ((27, 30, 10), (17, 38, 6), (42, 37, 7), (30, 19, 7)):
        ellipse(d, cx - r, cy - r, cx + r, cy + r, rgba(P["green_light"]))
    # Ciuffi regolari lungo il bordo della chioma, non pixel casuali.
    for lx, ly in ((17, 29), (24, 22), (33, 14), (42, 20), (49, 30),
                   (14, 41), (27, 48), (39, 48), (50, 41)):
        rect(d, lx, ly, lx + 2, ly + 1, rgba(P["green_light"]))
        rect(d, lx + 1, ly + 2, lx + 2, ly + 2, rgba(P["green_dark"]))
    finish(img, "tree")

    # Fioriera 32x20
    img, d = start(32, 20)
    contact(d, 2, 17, 30, 19)
    poly(d, [(5, 10), (27, 10), (25, 18), (7, 18)], rgba(shade(P["terra"], 0.90)))
    rect(d, 2, 8, 30, 11, rgba(shade(P["terra"], 1.10)))
    rect(d, 5, 9, 27, 10, rgba(P["terra_dark"]))
    rect(d, 8, 12, 24, 12, rgba(shade(P["terra"], 1.04)))
    for fx, color in ((9, P["red"]), (16, P["yellow"]), (23, P["white"])):
        rect(d, fx, 5, fx, 10, rgba(P["green"]))
        rect(d, fx - 2, 6, fx + 2, 6, rgba(P["green_dark"]))
        rect(d, fx - 3, 7, fx - 1, 7, rgba(P["green"]))
        rect(d, fx + 1, 8, fx + 3, 8, rgba(P["green"]))
        ellipse(d, fx - 2, 3, fx + 2, 7, rgba(color))
        rect(d, fx, 4, fx, 5, rgba(P["yellow"]))
    finish(img, "planter")

    # Segnale stradale 20x36
    img, d = start(20, 36)
    contact(d, 2, 33, 18, 35)
    rect(d, 9, 16, 11, 34, rgba(P["metal"]))
    rect(d, 9, 16, 9, 34, rgba(P["metal_light"]))
    rect(d, 7, 33, 13, 35, rgba(P["ink_soft"]))
    ellipse(d, 2, 2, 18, 18, rgba(P["white"]))
    ellipse(d, 3, 3, 17, 17, rgba(P["red"]))
    ellipse(d, 4, 4, 16, 16, rgba(P["white"]))
    rect(d, 6, 9, 14, 11, rgba(P["red"]))
    rect(d, 9, 4, 11, 6, rgba(P["ink_soft"]))
    finish(img, "sign")


    # Semaforo 16x48
    img, d = start(16, 48)
    contact(d, 2, 45, 14, 47)
    rect(d, 7, 20, 9, 46, rgba(P["ink_soft"]))
    rect(d, 7, 20, 7, 46, rgba(P["metal_light"]))
    rect(d, 5, 45, 11, 47, rgba(P["ink"]))
    rect(d, 3, 3, 13, 26, rgba(P["ink"]))
    rect(d, 4, 4, 12, 25, rgba(shade(P["ink"], 1.30)))
    for ly, color in ((5, P["red"]), (12, P["yellow"]), (19, P["green"])):
        rect(d, 3, ly, 13, ly, rgba(P["ink"]))
        rect(d, 4, ly + 1, 12, ly + 5, rgba(shade(P["ink"], 0.75)))
        ellipse(d, 5, ly + 1, 11, ly + 6, rgba(color))
        rect(d, 6, ly + 2, 7, ly + 3, rgba(shade(color, 1.22)))
    rect(d, 4, 26, 12, 27, rgba(P["ink"]))
    finish(img, "traffic_light")

    # Macchinetta EAV 20x40
    img, d = start(20, 40)
    contact(d, 2, 37, 18, 39)
    rect(d, 3, 3, 17, 38, rgba(P["eav_blue"]))
    rect(d, 3, 3, 4, 38, rgba(P["eav_light"]))
    rect(d, 15, 3, 17, 38, rgba(shade(P["eav_blue"], 0.70)))
    rect(d, 5, 5, 15, 18, rgba(P["white"]))
    rect(d, 6, 7, 14, 16, rgba(P["glass"]))
    rect(d, 6, 7, 14, 9, rgba(P["glass_light"]))
    rect(d, 7, 10, 9, 14, rgba(P["glass_light"]))
    rect(d, 5, 18, 15, 19, rgba(P["yellow"]))
    for ky in (21, 24, 27):
        rect(d, 6, ky, 7, ky + 1, rgba(P["yellow"]))
        rect(d, 10, ky, 11, ky + 1, rgba(P["white"]))
        rect(d, 14, ky, 15, ky + 1, rgba(P["metal_light"]))
    rect(d, 6, 30, 14, 32, rgba(P["ink"]))
    rect(d, 7, 31, 13, 31, rgba(P["glass_light"]))
    tiny_text(d, 5, 34, "EAV", rgba(P["white"]))
    rect(d, 4, 37, 16, 39, rgba(P["metal"]))
    rect(d, 4, 37, 16, 37, rgba(P["metal_light"]))
    finish(img, "ticket_machine")

    # Cane 24x24
    img, d = start(24, 24)
    contact(d, 2, 20, 22, 23)
    line(d, [(6, 12), (3, 8), (2, 6)], shade(P["brown"], 0.90), 2)
    ellipse(d, 6, 9, 18, 18, rgba(shade(P["brown"], 1.05)))
    rect(d, 7, 9, 16, 10, rgba(shade(P["brown"], 1.18)))
    rect(d, 7, 17, 9, 21, rgba(P["brown"]))
    rect(d, 14, 17, 16, 21, rgba(P["brown"]))
    rect(d, 8, 20, 9, 21, rgba(shade(P["brown"], 0.75)))
    rect(d, 15, 20, 16, 21, rgba(shade(P["brown"], 0.75)))
    ellipse(d, 15, 5, 22, 12, rgba(shade(P["brown"], 1.15)))
    rect(d, 16, 3, 18, 6, rgba(shade(P["brown"], 0.75)))
    rect(d, 20, 3, 22, 6, rgba(shade(P["brown"], 0.75)))
    rect(d, 21, 9, 23, 11, rgba(shade(P["brown"], 0.90)))
    rect(d, 19, 7, 19, 8, rgba(P["ink"]))
    rect(d, 20, 10, 21, 10, rgba(P["ink"]))
    rect(d, 14, 11, 17, 12, rgba(P["red"]))          # collare
    rect(d, 16, 13, 16, 14, rgba(P["yellow"]))
    finish(img, "dog")

    # Gatto 20x18
    img, d = start(20, 18)
    contact(d, 2, 15, 18, 17)
    line(d, [(5, 12), (2, 9), (4, 6)], rgba(P["concrete"]), 2)
    ellipse(d, 4, 6, 14, 15, rgba(P["concrete"]))
    rect(d, 5, 13, 6, 16, rgba(P["concrete"]))
    rect(d, 10, 13, 11, 16, rgba(P["concrete"]))
    for sx in (6, 9, 12):
        rect(d, sx, 7, sx + 1, 8, rgba(shade(P["concrete"], 0.75)))
    ellipse(d, 12, 3, 18, 10, rgba(shade(P["concrete"], 1.05)))
    poly(d, [(12, 5), (13, 1), (15, 4)], rgba(shade(P["concrete"], 1.05)))
    poly(d, [(16, 4), (18, 1), (18, 6)], rgba(shade(P["concrete"], 1.05)))
    rect(d, 14, 6, 14, 7, rgba(P["yellow"]))
    rect(d, 17, 6, 17, 7, rgba(P["yellow"]))
    rect(d, 15, 8, 16, 8, rgba(P["white"]))
    rect(d, 18, 8, 19, 9, rgba(P["white"]))
    finish(img, "cat")

    # Pacco 24x20
    img, d = start(24, 20)
    contact(d, 3, 17, 21, 19)
    rect(d, 3, 5, 21, 17, rgba(P["brown"]))
    rect(d, 3, 15, 21, 17, rgba(shade(P["brown"], 0.78)))
    poly(d, [(3, 5), (7, 2), (21, 2), (17, 5)], rgba(shade(P["brown"], 1.18)))
    poly(d, [(3, 5), (7, 2), (7, 15), (3, 12)], rgba(shade(P["brown"], 0.90)))
    rect(d, 11, 2, 13, 17, rgba(P["concrete_light"]))
    line(d, [(3, 5), (21, 5)], shade(P["brown"], 0.70), 1)
    rect(d, 15, 9, 19, 13, rgba(P["white"]))
    rect(d, 16, 10, 18, 10, rgba(P["ink_soft"]))
    rect(d, 16, 12, 18, 12, rgba(P["ink_soft"]))
    finish(img, "parcel")

    # Chiavi 16x12
    img, d = start(16, 12)
    contact(d, 2, 10, 14, 11)
    ellipse(d, 2, 2, 7, 7, rgba(P["yellow"]))
    ellipse(d, 4, 4, 5, 5, (0, 0, 0, 0))
    ellipse(d, 7, 4, 12, 9, rgba(shade(P["yellow"], 0.90)))
    ellipse(d, 9, 6, 10, 7, (0, 0, 0, 0))
    rect(d, 11, 6, 15, 7, rgba(P["metal_light"]))
    rect(d, 13, 8, 14, 9, rgba(P["metal_light"]))
    rect(d, 15, 8, 15, 9, rgba(P["metal_light"]))
    rect(d, 3, 3, 4, 3, rgba(shade(P["yellow"], 1.18)))
    finish(img, "keys")

    # Caffe' 16x20
    img, d = start(16, 20)
    contact(d, 2, 17, 14, 19)
    line(d, [(6, 2), (6, 4)], rgba(P["white"]), 1)
    line(d, [(10, 1), (10, 4)], rgba(P["white"]), 1)
    poly(d, [(3, 7), (13, 7), (11, 18), (5, 18)], rgba(P["white"]))
    ellipse(d, 12, 9, 16, 14, rgba(P["white"]))
    ellipse(d, 13, 10, 14, 13, (0, 0, 0, 0))
    ellipse(d, 2, 5, 14, 9, rgba(P["white"]))
    ellipse(d, 4, 6, 12, 8, rgba(P["brown"]))
    rect(d, 5, 12, 11, 13, rgba(P["red"]))
    rect(d, 6, 15, 10, 16, rgba(shade(P["white"], 0.86)))
    rect(d, 3, 18, 13, 19, rgba(P["white"]))
    finish(img, "coffee")

    # Biglietto 20x14
    img, d = start(20, 14)
    contact(d, 2, 12, 18, 13)
    rect(d, 2, 3, 18, 11, rgba(P["white"]))
    rect(d, 2, 3, 18, 5, rgba(P["eav_blue"]))
    rect(d, 2, 10, 18, 11, rgba(P["concrete"]))
    for py in (6, 8, 10):
        rect(d, 13, py, 14, py, rgba(P["ink_soft"]))
    tiny_text(d, 4, 6, "EAV", rgba(P["eav_blue"]))
    rect(d, 4, 3, 4, 3, rgba(P["yellow"]))
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
        "version": "0.4.0",
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
    print(f"OK {len(EXPECTED)} sprite ({total / 1e6:.2f} MB) - sheet {SHEET_W}x{SHEET_H}, 16 px/m")


if __name__ == "__main__":
    main()

