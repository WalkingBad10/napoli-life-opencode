"""Utility condivise per la generazione procedurale della pixel art di NAPOLI LIFE.

Tutta la grafica è originale, generata da codice: nessun asset di giochi esistenti.
"""

from __future__ import annotations

import hashlib
import random
from PIL import Image, ImageDraw

# Palette naturale, ispirata all'architettura napoletana (non copiata da altri giochi).
P = {
    "ink": "#2e2a26", "ink_soft": "#4a4038", "shadow": "#00000055",
    "asphalt": "#616563", "asphalt_dark": "#4d5150", "asphalt_light": "#737776",
    "concrete": "#b8b3a6", "concrete_light": "#d2ccbb", "curb": "#ded7c4",
    "stucco_cream": "#e6d5b6", "stucco_ochre": "#d9b785", "stucco_pink": "#d9a892",
    "stucco_yellow": "#e3c57e", "stucco_green": "#b7c2a0", "stucco_blue": "#a8bfc6",
    "terra": "#b2644d", "terra_dark": "#8d4c3c", "terra_light": "#c8795c",
    "roof_grey": "#8d8a80", "glass": "#5d7f8d", "glass_light": "#93b6bd",
    "green": "#6f8b53", "green_dark": "#4d6b3d", "green_light": "#8fa968",
    "metal": "#6c7072", "metal_light": "#a9adb0", "rust": "#a35c3c",
    "white": "#f3eee0", "black": "#24211e", "yellow": "#e2b83c",
    "eav_blue": "#1f4e79", "eav_light": "#4a8bc2", "red": "#b4473b",
    "brown": "#7c5a3c", "wood": "#a9794f", "skin1": "#e9b98f", "skin2": "#c98d64",
    "skin3": "#8d5b3e", "hair1": "#33251c", "hair2": "#6c4127", "hair3": "#171513",
}


def seeded(key: str) -> random.Random:
    return random.Random(int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16))


def rgba(hex_color: str | tuple, alpha: int = 255) -> tuple[int, int, int, int]:
    if isinstance(hex_color, tuple):
        if len(hex_color) == 4:
            return hex_color
        return (*hex_color[:3], alpha)
    h = hex_color.lstrip("#")
    if len(h) == 8:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def shade(hex_color: str, factor: float) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = max(0, min(1.6, factor))
    return (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)))


def noise(img: Image.Image, rng: random.Random, amount: int = 8, step: int = 2) -> None:
    """Aggiunge una leggera texture a un'immagine RGB evitando superfici piatte."""
    d = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    for _ in range((w * h) // (step * step * 5)):
        x, y = rng.randrange(w), rng.randrange(h)
        v = rng.randint(-amount, amount)
        c = (128 + v, 128 + v, 128 + v, rng.randint(14, 30))
        d.rectangle((x, y, x + step - 1, y + step - 1), fill=c)


def rect(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int,
         fill: str | tuple, outline: str | None = None, width: int = 1) -> None:
    d.rectangle((int(x0), int(y0), int(x1), int(y1)), fill=fill,
                outline=outline, width=width)


def ellipse(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int,
            fill: str | tuple, outline: str | None = None, width: int = 1) -> None:
    d.ellipse((int(x0), int(y0), int(x1), int(y1)), fill=fill,
              outline=outline, width=width)


def line(d: ImageDraw.ImageDraw, pts, fill, width: int = 1, joint: str = "curve") -> None:
    d.line([(int(x), int(y)) for x, y in pts], fill=fill, width=width, joint=joint)


def save_png(img: Image.Image, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img.save(path, "PNG", optimize=True)
