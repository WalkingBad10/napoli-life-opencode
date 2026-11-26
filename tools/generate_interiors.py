#!/usr/bin/env python3
"""Genera gli interni accessibili: stazione, bar napoletano, negozio, abitazione.

Ogni scena è disegnata a 48 px/m con prospettiva a tre quarti e comprende
arredi proporzionati, illuminazione e personaggi. Nessuna stanza vuota.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from artlib import P, ellipse, line, rect, rgba, save_png, seeded, shade

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/assets/interiors"
W, H = 576, 384
try:
    FONT = ImageFont.load_default()
    FONT_BIG = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 18)
except Exception:
    FONT = FONT_BIG = None


def base(seed, wall_color="#e8dcc3", floor_color="#c3b7a2") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), wall_color)
    d = ImageDraw.Draw(img, "RGBA")
    rect(d, 0, 92, W, H, floor_color)
    for y in range(92, H, 24):
        line(d, [(0, y), (W, y)], rgba(P["ink"], 22), 1)
    for x in range(0, W, 48):
        line(d, [(x, 92), (x - 20, H)], rgba(P["ink"], 18), 1)
    rect(d, 0, 88, W, 94, shade(wall_color, 0.75))
    # illuminazione soffice dall'alto
    for yy in range(96, H, 6):
        d.rectangle((0, yy, W, yy + 2), fill=rgba(P["white"], max(0, 34 - (yy - 96) // 8)))
    rng = seeded(seed)
    for _ in range(240):
        x, y = rng.randrange(W), rng.randrange(96, H)
        d.point((x, y), fill=rgba(P["ink"], rng.randint(8, 24)))
    return img, d


def sign(d, x, y, w, text, color=P["eav_blue"]):
    rect(d, x, y, x + w, y + 26, P["ink"])
    rect(d, x + 2, y + 2, x + w - 2, y + 24, color)
    if FONT:
        d.text((x + 8, y + 7), text, fill=P["white"], font=FONT)


def table(d, x, y):
    ellipse(d, x - 26, y + 14, x + 26, y + 26, rgba(P["shadow"], 140))
    ellipse(d, x - 24, y - 4, x + 24, y + 14, P["wood"])
    ellipse(d, x - 20, y - 7, x + 20, y + 11, shade(P["wood"], 1.14))
    rect(d, x - 3, y + 8, x + 3, y + 20, P["brown"])


def chair(d, x, y):
    rect(d, x - 10, y - 6, x + 10, y + 8, P["brown"])
    rect(d, x - 10, y + 8, x - 8, y + 18, P["ink_soft"])
    rect(d, x + 8, y + 8, x + 10, y + 18, P["ink_soft"])


def person(d, x, y, shirt, skin=P["skin2"], hair=P["hair1"]):
    ellipse(d, x - 9, y + 20, x + 9, y + 25, rgba(P["shadow"], 140))
    rect(d, x - 7, y - 2, x + 7, y + 18, shirt)
    rect(d, x - 10, y + 2, x - 6, y + 14, shade(shirt, 0.85))
    rect(d, x + 6, y + 2, x + 10, y + 14, shade(shirt, 0.8))
    rect(d, x - 6, y + 16, x - 2, y + 21, P["ink_soft"])
    rect(d, x + 2, y + 16, x + 6, y + 21, P["ink_soft"])
    rect(d, x - 6, y - 16, x + 6, y - 3, skin)
    rect(d, x - 7, y - 19, x + 7, y - 14, hair)
    rect(d, x - 3, y - 11, x - 2, y - 10, P["ink"])
    rect(d, x + 2, y - 11, x + 3, y - 10, P["ink"])


def station() -> dict:
    img, d = base("station", "#ded7c6", "#b6b1a5")
    # vetrate e ingresso
    for x in (24, 132, 420):
        rect(d, x, 14, x + 120, 84, P["ink"])
        rect(d, x + 3, 17, x + 117, 81, P["glass"])
        rect(d, x + 3, 17, x + 60, 48, rgba(P["glass_light"], 150))
        for k in range(0, 120, 30):
            rect(d, x + k, 17, x + k + 4, 81, P["white"])
    rect(d, 268, 20, 404, 88, "#8b8679")
    sign(d, 284, 32, 104, "EAV  Biglietti")
    rect(d, 282, 68, 338, 88, P["ink"])
    rect(d, 286, 70, 334, 86, P["glass"])
    person(d, 348, 76, P["eav_blue"], P["skin1"])
    # tabellone orari
    rect(d, 150, 108, 262, 172, P["ink"])
    rect(d, 154, 112, 258, 168, "#1c3330")
    if FONT:
        d.text((166, 118), "PARTENZE", fill=P["yellow"], font=FONT)
        for i, t in enumerate(["06:12  TORREGAVETA", "06:40  NAPOLI", "07:05  TORREGAVETA"]):
            d.text((162, 134 + i * 11), t, fill=P["white"], font=FONT)
    # panchine e tetrapak
    for x in (64, 156):
        rect(d, x, 250, x + 110, 258, P["wood"])
        rect(d, x, 258, x + 110, 264, shade(P["wood"], 0.8))
        rect(d, x + 8, 264, x + 14, 282, P["metal"])
        rect(d, x + 90, 264, x + 96, 282, P["metal"])
    rect(d, 396, 226, 428, 278, P["metal"])
    rect(d, 400, 230, 424, 248, P["glass"])
    line(d, [(412, 248), (412, 270)], P["yellow"], 2)
    person(d, 470, 252, "#a26750", P["skin3"])
    # indicazioni
    sign(d, 320, 196, 120, "Uscita -> Binari")
    save_png(img, OUT / "station.png")
    return {
        "file": "assets/interiors/station.png",
        "door": {"x": 288, "y": 370, "target": "world", "spawn": [0, -12]},
        "interactables": [
            {"id": "ticket_clerk", "name": "Addetto EAV", "x": 348, "y": 76, "kind": "ticket"},
            {"id": "timetable", "name": "Tabellone partenze", "x": 206, "y": 140, "kind": "read"},
            {"id": "station_exit", "name": "Uscita", "x": 288, "y": 370, "kind": "exit"},
        ],
        "colliders": [[270, 20, 406, 92], [150, 108, 262, 172]],
    }


def bar() -> dict:
    img, d = base("bar", "#e7d8b9", "#b9ad97")
    sign(d, 40, 18, 150, "BAR  Pianura", "#8c3f32")
    # bancone
    rect(d, 24, 170, 300, 218, P["brown"])
    rect(d, 20, 162, 304, 176, shade(P["wood"], 1.12))
    rect(d, 28, 218, 296, 260, shade(P["brown"], 0.85))
    for x in range(40, 290, 36):
        rect(d, x, 222, x + 2, 256, rgba(P["ink"], 70))
    # macchina espresso professionale
    rect(d, 130, 132, 194, 164, P["metal_light"])
    rect(d, 134, 136, 190, 152, P["ink"])
    for x in (140, 158, 176):
        rect(d, x, 144, x + 6, 150, P["yellow"])
        rect(d, x + 1, 152, x + 5, 160, P["white"])
    rect(d, 196, 138, 210, 162, P["ink_soft"])
    person(d, 164, 120, P["white"], P["skin2"], P["hair1"])
    # tazzine
    for x in (50, 78, 232, 260):
        rect(d, x, 152, x + 14, 158, P["white"])
        rect(d, x + 3, 148, x + 11, 152, "#7b3b25")
    # vetrina dolci
    rect(d, 318, 158, 466, 242, P["ink"])
    rect(d, 322, 162, 462, 238, rgba(P["glass_light"], 190))
    for x, y, c in [(340, 194, P["terra"]), (374, 196, P["yellow"]),
                    (408, 194, P["white"]), (440, 198, P["brown"])]:
        ellipse(d, x, y, x + 20, y + 14, c)
        ellipse(d, x + 4, y - 4, x + 16, y + 6, shade(c, 1.1))
    # frigo e scaffali
    rect(d, 476, 122, 552, 260, P["white"])
    rect(d, 482, 128, 546, 180, rgba(P["glass"], 200))
    rect(d, 482, 186, 546, 254, rgba(P["glass_light"], 150))
    for y in (146, 204, 226):
        for x in (490, 510, 530):
            rect(d, x, y, x + 10, y + 14, P["red"] if x % 2 else P["green"])
    sign(d, 24, 286, 100, "ESPRESSO", "#8c3f32")
    # tavolini e clienti
    table(d, 110, 320)
    chair(d, 68, 330)
    chair(d, 156, 332)
    person(d, 72, 316, "#4f7f91", P["skin1"])
    table(d, 350, 322)
    chair(d, 310, 334)
    chair(d, 396, 334)
    person(d, 398, 318, "#a8634b", P["skin3"], P["hair3"])
    save_png(img, OUT / "bar.png")
    return {
        "file": "assets/interiors/bar.png",
        "door": {"x": 288, "y": 374, "target": "world", "spawn": [17, -13]},
        "interactables": [
            {"id": "barista", "name": "Barista", "x": 164, "y": 120, "kind": "barista"},
            {"id": "pastries", "name": "Vetrina dolci", "x": 394, "y": 200, "kind": "buy_food"},
            {"id": "bar_exit", "name": "Esci dal bar", "x": 288, "y": 374, "kind": "exit"},
        ],
        "colliders": [[20, 162, 304, 260], [318, 158, 466, 242], [476, 122, 552, 260]],
    }


def shop() -> dict:
    img, d = base("shop", "#dfdccb", "#bcb5a5")
    sign(d, 30, 20, 160, "NEGOZIO", "#2f6c57")
    # scaffali
    for sy in (120, 220):
        rect(d, 30, sy, 210, sy + 22, P["wood"])
        for x in range(40, 205, 18):
            rect(d, x, sy - 12, x + 10, sy, [P["red"], P["green"], P["yellow"], P["eav_blue"]][(x // 18) % 4])
    rect(d, 250, 120, 300, 260, shade(P["wood"], 0.9))
    for y in range(130, 250, 20):
        for x in (258, 276):
            rect(d, x, y, x + 10, y + 13, [P["red"], P["white"], P["yellow"]][(y // 20) % 3])
    # banco cassa
    rect(d, 330, 210, 470, 264, P["wood"])
    rect(d, 336, 188, 392, 214, P["ink_soft"])
    rect(d, 340, 192, 388, 208, P["glass"])
    person(d, 400, 186, "#c2a25a", P["skin2"])
    # frigo
    rect(d, 486, 140, 550, 268, P["white"])
    rect(d, 492, 148, 544, 200, rgba(P["glass"], 210))
    rect(d, 492, 208, 544, 262, rgba(P["glass_light"], 160))
    save_png(img, OUT / "shop.png")
    return {
        "file": "assets/interiors/shop.png",
        "door": {"x": 288, "y": 374, "target": "world", "spawn": [34, -11]},
        "interactables": [
            {"id": "shopkeeper", "name": "Commerciante", "x": 400, "y": 186, "kind": "shop"},
            {"id": "shop_exit", "name": "Esci dal negozio", "x": 288, "y": 374, "kind": "exit"},
        ],
        "colliders": [[30, 108, 210, 242], [250, 120, 300, 260], [330, 188, 470, 264], [486, 140, 550, 268]],
    }


def home() -> dict:
    img, d = base("home", "#efe4cf", "#c8b99f")
    # finestra con tende
    rect(d, 40, 18, 176, 112, P["ink"])
    rect(d, 44, 22, 172, 108, "#8fb9c7")
    rect(d, 44, 22, 172, 60, "#b9d8e0")
    rect(d, 104, 22, 110, 108, P["white"])
    rect(d, 44, 62, 172, 68, P["white"])
    rect(d, 40, 18, 62, 112, P["white"])
    rect(d, 154, 18, 176, 112, P["white"])
    # letto
    rect(d, 30, 226, 170, 330, P["wood"])
    rect(d, 36, 232, 164, 300, P["white"])
    rect(d, 36, 232, 164, 250, "#e7e1d0")
    rect(d, 42, 252, 92, 276, "#7b93a0")
    rect(d, 98, 252, 158, 276, "#7b93a0")
    # cucina
    rect(d, 230, 150, 420, 200, shade(P["wood"], 0.9))
    rect(d, 236, 156, 414, 194, P["concrete_light"])
    rect(d, 250, 162, 286, 188, P["metal"])
    rect(d, 292, 162, 310, 188, P["white"])
    rect(d, 330, 158, 380, 190, P["terra"])
    rect(d, 230, 200, 420, 268, shade(P["brown"], 0.9))
    # tavolo e sedia
    table(d, 300, 310)
    chair(d, 248, 322)
    # TV, piante, tappeto
    rect(d, 470, 180, 552, 226, P["ink"])
    rect(d, 476, 186, 546, 220, P["glass"])
    rect(d, 508, 226, 514, 246, P["ink"])
    ellipse(d, 450, 300, 548, 344, "#a46752")
    ellipse(d, 458, 306, 540, 338, "#bb7a5f")
    rect(d, 62, 150, 82, 220, P["terra"])
    for x, y in [(72, 146), (60, 156), (84, 158)]:
        ellipse(d, x - 12, y - 12, x + 12, y + 12, P["green"])
    save_png(img, OUT / "home.png")
    return {
        "file": "assets/interiors/home.png",
        "door": {"x": 288, "y": 374, "target": "world", "spawn": [-6, 22]},
        "interactables": [
            {"id": "bed", "name": "Letto (riposa)", "x": 100, "y": 280, "kind": "sleep"},
            {"id": "home_exit", "name": "Esci di casa", "x": 288, "y": 374, "kind": "exit"},
        ],
        "colliders": [[30, 226, 170, 330], [230, 150, 420, 268], [470, 180, 552, 246]],
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rooms = {"station": station(), "bar": bar(), "shop": shop(), "home": home()}
    for name, data in rooms.items():
        data["name"] = name
        data["size_px"] = [W, H]
        data["scale_ppm"] = 48
    (OUT / "manifest.json").write_text(json.dumps(rooms, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OK 4 interni")


if __name__ == "__main__":
    main()
