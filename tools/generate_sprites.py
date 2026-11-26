#!/usr/bin/env python3
"""Genera personaggi, veicoli, treno EAV e oggetti urbani in pixel art originale."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from artlib import P, ellipse, line, rect, rgba, save_png, shade

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/assets/sprites"
FW, FH = 24, 36
try:
    FONT = ImageFont.load_default()
except Exception:
    FONT = None

PALETTES = {
    "player": {"skin": P["skin1"], "hair": P["hair2"], "shirt": "#4d7fa6", "pants": "#404a5c", "shoes": "#2b2622"},
    "resident": {"skin": P["skin2"], "hair": P["hair1"], "shirt": "#c26a55", "pants": "#5f6b68", "shoes": "#332b26"},
    "worker": {"skin": P["skin3"], "hair": P["hair3"], "shirt": "#e0b23f", "pants": "#4a5058", "shoes": "#282523"},
    "elderly": {"skin": P["skin1"], "hair": "#d6d2c8", "shirt": "#7a8f70", "pants": "#4a443d", "shoes": "#2d2823"},
    "teen": {"skin": P["skin2"], "hair": P["hair1"], "shirt": "#8f6fa8", "pants": "#2f3e52", "shoes": "#1f1d1c"},
    "railway": {"skin": P["skin1"], "hair": P["hair1"], "shirt": P["eav_blue"], "pants": "#263241", "shoes": "#1d1b19"},
    "vendor": {"skin": P["skin2"], "hair": P["hair3"], "shirt": "#f0e6d2", "pants": "#6b5b49", "shoes": "#302a24"},
}


def person_cell(pal: dict, direction: int, frame: int, accessory: str = "") -> Image.Image:
    img = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    swing = [0, 2, 0, -2][frame]
    bounce = [0, -1, 0, -1][frame]
    ellipse(d, 6, 32, 18, 35, rgba(P["shadow"], 170))
    # gambe
    rect(d, 9 + swing, 24 + bounce, 12 + swing, 33, pal["pants"])
    rect(d, 13 - swing, 24 + bounce, 16 - swing, 33, shade(pal["pants"], 0.85))
    rect(d, 8 + swing, 32 + bounce, 12 + swing, 34, pal["shoes"])
    rect(d, 13 - swing, 32 + bounce, 17 - swing, 34, pal["shoes"])
    # busto
    rect(d, 8, 14 + bounce, 17, 25 + bounce, pal["shirt"])
    rect(d, 15, 14 + bounce, 17, 25 + bounce, shade(pal["shirt"], 0.78))
    rect(d, 8, 14 + bounce, 10, 25 + bounce, shade(pal["shirt"], 1.12))
    # braccia
    rect(d, 5, 16 + bounce + swing, 8, 24 + bounce + swing, shade(pal["shirt"], 0.92))
    rect(d, 18, 16 + bounce - swing, 20, 24 + bounce - swing, shade(pal["shirt"], 0.82))
    rect(d, 5, 23 + bounce + swing, 8, 25 + bounce + swing, pal["skin"])
    rect(d, 18, 23 + bounce - swing, 20, 25 + bounce - swing, pal["skin"])
    # testa
    rect(d, 8, 5 + bounce, 17, 14 + bounce, pal["skin"])
    rect(d, 7, 4 + bounce, 18, 8 + bounce, pal["hair"])
    rect(d, 8, 3 + bounce, 17, 5 + bounce, shade(pal["hair"], 1.15))
    if direction in (0, 3):  # fronte / fronte in alto
        rect(d, 10, 9 + bounce, 11, 10 + bounce, P["ink"])
        rect(d, 15, 9 + bounce, 16, 10 + bounce, P["ink"])
        if direction == 0:
            rect(d, 12, 12 + bounce, 14, 12 + bounce, shade(pal["skin"], 0.7))
    elif direction == 1:  # sinistra
        rect(d, 8, 9 + bounce, 9, 10 + bounce, P["ink"])
        rect(d, 6, 11 + bounce, 8, 11 + bounce, shade(pal["skin"], 0.8))
    else:  # destra
        rect(d, 16, 9 + bounce, 17, 10 + bounce, P["ink"])
        rect(d, 17, 11 + bounce, 19, 11 + bounce, shade(pal["skin"], 0.8))
    if accessory == "hat":
        rect(d, 6, 3 + bounce, 19, 5 + bounce, shade(pal["shirt"], 0.65))
        rect(d, 8, 1 + bounce, 17, 3 + bounce, shade(pal["shirt"], 0.8))
    elif accessory == "cap":
        rect(d, 7, 2 + bounce, 18, 5 + bounce, P["red"])
        rect(d, 5, 5 + bounce, 12, 6 + bounce, shade(P["red"], 0.8))
    elif accessory == "bag":
        rect(d, 6, 20 + bounce, 10, 27 + bounce, P["brown"])
        line(d, [(7, 16 + bounce), (9, 20 + bounce)], P["brown"], 1)
    elif accessory == "cane":
        line(d, [(2, 21), (4, 33)], P["wood"], 2)
    elif accessory == "vest":
        rect(d, 10, 15 + bounce, 15, 24 + bounce, rgba(P["yellow"], 190))
    return img


def make_character_sheet(name: str, pal: dict, accessory: str = "") -> None:
    sheet = Image.new("RGBA", (FW * 4, FH * 4), (0, 0, 0, 0))
    for direction in range(4):
        for frame in range(4):
            cell = person_cell(pal, direction, frame, accessory)
            sheet.paste(cell, (frame * FW, direction * FH))
    save_png(sheet, OUT / f"{name}.png")


def prop_canvas(w, h) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img, "RGBA")


def make_props() -> None:
    # Lampione
    img, d = prop_canvas(28, 76)
    ellipse(d, 6, 71, 22, 75, rgba(P["shadow"], 160))
    rect(d, 12, 12, 16, 72, P["metal"])
    rect(d, 12, 12, 13, 72, P["metal_light"])
    line(d, [(14, 14), (14, 6), (23, 6)], P["metal"], 3)
    rect(d, 19, 5, 27, 10, P["ink_soft"])
    rect(d, 21, 7, 25, 9, rgba(P["yellow"], 230))
    save_png(img, OUT / "lamp.png")

    # Cassonetto
    img, d = prop_canvas(22, 30)
    ellipse(d, 1, 25, 21, 29, rgba(P["shadow"], 150))
    rect(d, 3, 8, 19, 27, P["green_dark"])
    rect(d, 3, 8, 19, 11, shade(P["green"], 1.1))
    rect(d, 2, 6, 20, 9, P["ink_soft"])
    rect(d, 9, 12, 13, 13, P["white"])
    save_png(img, OUT / "bin.png")

    # Scooter
    img, d = prop_canvas(52, 34)
    ellipse(d, 2, 25, 50, 32, rgba(P["shadow"], 150))
    ellipse(d, 5, 22, 17, 33, P["ink"])
    ellipse(d, 35, 22, 47, 33, P["ink"])
    ellipse(d, 8, 25, 14, 30, P["metal_light"])
    ellipse(d, 38, 25, 44, 30, P["metal_light"])
    rect(d, 14, 17, 39, 25, "#d8d2c4")
    rect(d, 20, 12, 34, 20, P["white"])
    rect(d, 22, 14, 32, 18, P["glass"])
    rect(d, 38, 18, 45, 21, P["red"])
    line(d, [(15, 19), (10, 10)], P["metal"], 2)
    save_png(img, OUT / "scooter.png")

    # Automobile parcheggiata (proporzioni ~4.2 x 1.8 m a 16 px/m)
    img, d = prop_canvas(72, 40)
    ellipse(d, 3, 27, 69, 38, rgba(P["shadow"], 160))
    rect(d, 5, 10, 67, 32, shade(P["red"], 0.8))
    rect(d, 8, 6, 64, 29, P["red"])
    rect(d, 16, 4, 54, 10, shade(P["red"], 1.1))
    rect(d, 18, 8, 37, 15, P["glass"])
    rect(d, 39, 8, 53, 15, P["glass"])
    rect(d, 8, 24, 13, 28, P["white"])
    rect(d, 59, 24, 64, 28, P["yellow"])
    rect(d, 12, 28, 22, 33, P["ink"])
    rect(d, 50, 28, 60, 33, P["ink"])
    save_png(img, OUT / "car_red.png")
    img, d = prop_canvas(72, 40)
    ellipse(d, 3, 27, 69, 38, rgba(P["shadow"], 160))
    rect(d, 5, 10, 67, 32, "#9aa3a8")
    rect(d, 8, 6, 64, 29, "#c6ccce")
    rect(d, 16, 4, 54, 10, "#dde1e2")
    rect(d, 18, 8, 37, 15, P["glass"])
    rect(d, 39, 8, 53, 15, P["glass"])
    rect(d, 8, 24, 13, 28, P["white"])
    rect(d, 59, 24, 64, 28, P["yellow"])
    save_png(img, OUT / "car_silver.png")

    # Autobus urbano (ANM)
    img, d = prop_canvas(240, 52)
    ellipse(d, 4, 40, 236, 50, rgba(P["shadow"], 150))
    rect(d, 6, 8, 234, 43, "#2e7d5b")
    rect(d, 10, 5, 230, 39, "#3f986f")
    for x in range(20, 220, 30):
        rect(d, x, 10, x + 22, 22, P["glass"])
        rect(d, x, 25, x + 22, 35, shade(P["glass"], 1.1))
    rect(d, 8, 37, 14, 42, P["white"])
    rect(d, 226, 37, 232, 42, P["yellow"])
    if FONT:
        d.text((100, 2), "ANM", fill=P["white"], font=FONT)
    save_png(img, OUT / "bus.png")

    # Albero mediterraneo
    img, d = prop_canvas(60, 76)
    ellipse(d, 8, 70, 52, 75, rgba(P["shadow"], 150))
    rect(d, 27, 40, 33, 71, P["brown"])
    for x, y, r in [(30, 32, 18), (20, 40, 12), (41, 39, 13), (30, 20, 12)]:
        ellipse(d, x - r, y - r, x + r, y + r, P["green_dark"])
        ellipse(d, x - r + 3, y - r + 2, x + r - 2, y + r - 4, P["green"])
        ellipse(d, x - r + 7, y - r + 6, x + r - 8, y + 2, P["green_light"])
    save_png(img, OUT / "tree.png")

    # Fioriera
    img, d = prop_canvas(30, 24)
    ellipse(d, 3, 20, 27, 23, rgba(P["shadow"], 140))
    rect(d, 5, 12, 25, 21, P["terra"])
    rect(d, 4, 10, 26, 13, P["terra_light"])
    for x, c in [(9, P["red"]), (14, P["yellow"]), (20, P["white"])]:
        rect(d, x, 6, x + 2, 11, P["green"])
        ellipse(d, x - 2, 3, x + 4, 8, c)
    save_png(img, OUT / "planter.png")

    # Panchina
    img, d = prop_canvas(52, 30)
    ellipse(d, 3, 25, 49, 29, rgba(P["shadow"], 140))
    rect(d, 5, 10, 47, 13, P["wood"])
    rect(d, 5, 14, 47, 17, shade(P["wood"], 0.85))
    rect(d, 6, 17, 46, 23, P["wood"])
    rect(d, 9, 23, 12, 28, P["metal"])
    rect(d, 40, 23, 43, 28, P["metal"])
    save_png(img, OUT / "bench.png")

    # Segnale stradale italiano (cerchio blu con bordo bianco)
    img, d = prop_canvas(24, 52)
    ellipse(d, 2, 45, 22, 50, rgba(P["shadow"], 140))
    rect(d, 11, 20, 13, 46, P["metal"])
    ellipse(d, 2, 3, 22, 23, P["white"])
    ellipse(d, 4, 5, 20, 21, P["eav_blue"])
    line(d, [(7, 17), (17, 9)], P["white"], 3)
    save_png(img, OUT / "sign.png")

    # Semaforo
    img, d = prop_canvas(22, 60)
    ellipse(d, 3, 55, 19, 59, rgba(P["shadow"], 140))
    rect(d, 9, 12, 13, 56, P["ink_soft"])
    rect(d, 4, 4, 18, 28, P["ink"])
    for y, c in [(8, P["red"]), (14, P["yellow"]), (21, P["green"])]:
        ellipse(d, 8, y, 14, y + 5, c)
    save_png(img, OUT / "traffic_light.png")

    # Macchinetta biglietti EAV
    img, d = prop_canvas(26, 44)
    ellipse(d, 2, 39, 24, 43, rgba(P["shadow"], 150))
    rect(d, 4, 4, 22, 41, P["eav_blue"])
    rect(d, 6, 6, 20, 18, P["white"])
    rect(d, 8, 8, 18, 14, P["glass"])
    rect(d, 7, 22, 19, 25, P["yellow"])
    rect(d, 7, 29, 19, 32, P["ink"])
    if FONT:
        d.text((6, 34), "EAV", fill=P["white"], font=FONT)
    save_png(img, OUT / "ticket_machine.png")

    # Cane e gatto
    img, d = prop_canvas(26, 22)
    ellipse(d, 2, 18, 24, 21, rgba(P["shadow"], 140))
    rect(d, 6, 8, 19, 18, "#a97b4d")
    ellipse(d, 16, 4, 24, 12, "#b98a59")
    rect(d, 19, 3, 21, 6, "#8a623e")
    rect(d, 7, 17, 9, 20, "#8a623e")
    rect(d, 16, 17, 18, 20, "#8a623e")
    ellipse(d, 19, 7, 20, 8, P["ink"])
    save_png(img, OUT / "dog.png")
    img, d = prop_canvas(22, 18)
    ellipse(d, 2, 15, 20, 17, rgba(P["shadow"], 140))
    ellipse(d, 5, 6, 18, 15, P["ink_soft"])
    ellipse(d, 14, 3, 20, 9, P["ink_soft"])
    rect(d, 15, 1, 17, 3, P["ink_soft"])
    rect(d, 19, 2, 21, 4, P["ink_soft"])
    ellipse(d, 16, 5, 17, 6, P["yellow"])
    save_png(img, OUT / "cat.png")

    # Oggetti di missione
    img, d = prop_canvas(20, 18)
    rect(d, 2, 4, 18, 16, P["brown"])
    rect(d, 2, 4, 18, 6, shade(P["brown"], 1.2))
    rect(d, 9, 4, 12, 16, P["concrete_light"])
    save_png(img, OUT / "parcel.png")
    img, d = prop_canvas(18, 12)
    ellipse(d, 2, 5, 6, 9, P["yellow"])
    rect(d, 6, 5, 15, 7, P["metal_light"])
    rect(d, 13, 7, 15, 10, P["yellow"])
    save_png(img, OUT / "keys.png")
    img, d = prop_canvas(16, 18)
    rect(d, 6, 8, 10, 16, P["white"])
    ellipse(d, 3, 3, 13, 10, P["white"])
    rect(d, 4, 5, 12, 7, "#7b3b25")
    save_png(img, OUT / "coffee.png")
    img, d = prop_canvas(16, 14)
    rect(d, 5, 4, 11, 12, P["eav_blue"])
    rect(d, 4, 2, 12, 4, P["white"])
    save_png(img, OUT / "ticket.png")


def make_train() -> None:
    """Treno EAV Circumflegrea: 2 casse, proporzioni ~36 m x 2.9 m (16 px/m)."""
    car_w = 280
    img = Image.new("RGBA", (car_w * 2 + 8, 68), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    for ci in range(2):
        x0 = ci * (car_w + 8)
        ellipse(d, x0 + 6, 48, x0 + car_w - 6, 60, rgba(P["shadow"], 170))
        rect(d, x0 + 2, 12, x0 + car_w - 2, 50, P["ink"])
        rect(d, x0 + 4, 14, x0 + car_w - 4, 48, P["eav_blue"])
        rect(d, x0 + 4, 33, x0 + car_w - 4, 39, P["white"])
        rect(d, x0 + 4, 41, x0 + car_w - 4, 44, P["eav_light"])
        for k in range(6):
            wx = x0 + 16 + k * 44
            rect(d, wx, 19, wx + 30, 31, P["glass"])
            rect(d, wx, 19, wx + 13, 24, rgba(P["glass_light"], 170))
        for dx in (x0 + 6, x0 + car_w - 38):
            rect(d, dx, 17, dx + 26, 47, shade(P["eav_blue"], 0.75))
            rect(d, dx + 3, 20, dx + 23, 32, P["glass"])
            rect(d, dx + 3, 20, dx + 11, 25, rgba(P["glass_light"], 150))
        for bx in (x0 + 40, x0 + car_w - 65):
            rect(d, bx, 48, bx + 45, 53, P["ink_soft"])
        if ci == 0:
            rect(d, x0 + 2, 20, x0 + 7, 27, P["yellow"])
            line(d, [(x0 + 120, 14), (x0 + 132, 5), (x0 + 148, 14)], P["metal_light"], 2)
        if FONT:
            d.text((x0 + 110, 42), "EAV", fill=P["eav_blue"], font=FONT)
    save_png(img, OUT / "train_eav.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, pal in PALETTES.items():
        acc = ""
        if name == "worker":
            acc = "hat"
        elif name == "railway":
            acc = "vest"
        elif name == "elderly":
            acc = "cane"
        elif name == "vendor":
            acc = "apron" if False else "bag"
        make_character_sheet(name, pal, acc)
    make_props()
    make_train()
    manifest = {
        "frame_w": FW, "frame_h": FH,
        "directions": ["down", "left", "right", "up"],
        "characters": list(PALETTES),
        "train_pixels_per_car": 280,
        "scale": "16 px = 1 m; character feet at frame bottom - 2 px",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.glob("*.png"))
    print(f"OK sprite: {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
