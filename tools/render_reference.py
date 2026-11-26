#!/usr/bin/env python3
"""Renderizza una mappa di riferimento 2D del mondo convertito (controllo cartografico)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W = json.loads((ROOT / "data/world/pianura_world.json").read_text(encoding="utf-8"))
OUT = ROOT / "data/reference/pianura_overview.png"
PPM = 4
SIZE = 340
img = Image.new("RGB", (SIZE * 2 * PPM, SIZE * 2 * PPM), "#d9d3c4")
draw = ImageDraw.Draw(img)


def px(x: float, y: float) -> tuple[int, int]:
    return (int((x + SIZE) * PPM), int((y + SIZE) * PPM))


try:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
except OSError:
    font = ImageFont.load_default()

for lc in W["landcover"]:
    if len(lc["footprint"]) >= 3:
        color = {"grass": "#8aa56b", "meadow": "#8aa56b", "forest": "#597b4a",
                 "residential": "#cfc9bb", "industrial": "#b9b6ad"}.get(lc["kind"], "#b4bf9d")
        draw.polygon([px(*p) for p in lc["footprint"]], fill=color)
for r in W["roads"]:
    pts = [px(*p) for p in r["points"]]
    if len(pts) < 2:
        continue
    width = max(1, int(r["width_m"] * PPM))
    color = "#efe9db" if r["kind"] in ("footway", "path", "steps", "crossing") else "#777b78"
    draw.line(pts, fill=color, width=width, joint="curve")
for p in W["parking"]:
    if len(p["footprint"]) >= 3:
        draw.polygon([px(*p) for p in p["footprint"]], fill="#62666a")
for rail in W["rails"]:
    pts = [px(*p) for p in rail["points"]]
    if len(pts) >= 2:
        draw.line(pts, fill="#3d3c3a", width=max(2, int(1.4 * PPM)))
for platform in W["platforms"]:
    draw.polygon([px(*p) for p in platform["footprint"]], fill="#a9a39a", outline="#6c685f")
for b in W["buildings"]:
    pts = [px(*p) for p in b["footprint"]]
    if len(pts) >= 3:
        color = "#d38b6f" if b["kind"] == "train_station" else "#a8998a"
        draw.polygon(pts, fill=color, outline="#5a5149", width=2)
        if b["name"]:
            draw.text(px(*b["center"]), b["name"], fill="#202020", font=font)
for poi in W["pois"]:
    x, y = px(poi["x"], poi["y"])
    draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="#c0392b")
    if poi["name"]:
        draw.text((x + 5, y - 7), poi["name"], fill="#202020", font=font)
draw.ellipse((px(0, 0)[0] - 6, px(0, 0)[1] - 6, px(0, 0)[0] + 6, px(0, 0)[1] + 6), outline="#0055ff", width=3)
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print("OK", OUT)
