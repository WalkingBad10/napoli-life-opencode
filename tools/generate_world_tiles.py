#!/usr/bin/env python3
"""Genera i settori del suolo in pixel art dal mondo OSM convertito.

Ogni settore copre 64 x 64 metri e viene disegnato direttamente a 16 px/m
(1024 x 1024 px): il motore NON applica piu' alcuna scala (engine_scale = 1).

Il suolo e' costruito con operazioni vettoriali (ImageDraw) su una texture di
base generata una sola volta e replicata: nessun loop per-pixel sull'intero
settore, nessuna anti-aliasing, risultato deterministico.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw
from artlib import P, rgba, save_png, seeded

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/assets/tiles"
W = json.loads((ROOT / "data/world/pianura_world.json").read_text(encoding="utf-8"))

PPM = 16
SECTOR_M = 64
SECTOR_PX = SECTOR_M * PPM
ORIGINS = range(-192, 192, SECTOR_M)

# Colori locali complementari alla palette di artlib (varianti di luminosita').
GRAVEL = "#8b8577"
GRAVEL_LIGHT = "#a49d8d"
PATH_SAND = "#cabfa9"
STEP_GREY = "#9b9485"
RAIL_DARK = "#3f4343"

CARRIAGEWAYS = {
    "residential", "service", "secondary", "tertiary", "unclassified",
    "primary", "trunk", "living_street",
}
FOOTWAYS = {"footway", "path", "steps", "crossing", "cycleway", "track"}
GREEN_KINDS = {
    "grass", "grassland", "meadow", "forest", "recreation_ground",
    "cemetery", "pitch", "vineyard",
}
LANDCOVER_COLORS = {
    "grass": "#7c995f", "grassland": "#7c995f", "meadow": "#7c995f",
    "forest": "#5c7b49", "recreation_ground": "#88a36a",
    "cemetery": "#93a178", "pitch": "#6f9155", "vineyard": "#7a9457",
    "residential": "#b9b5a6", "industrial": "#b2ada1", "landfill": "#a9a396",
}


# --------------------------------------------------------------------------- #
# Geometria e supporti vettoriali
# --------------------------------------------------------------------------- #

def to_local(pt, ox, oy):
    return ((pt[0] - ox) * PPM, (pt[1] - oy) * PPM)


def bbox_of(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def affected(points, pad_m=3):
    x0, y0, x1, y1 = bbox_of(points)
    out = []
    for ox in ORIGINS:
        for oy in ORIGINS:
            if (ox <= x1 + pad_m and ox + SECTOR_M >= x0 - pad_m
                    and oy <= y1 + pad_m and oy + SECTOR_M >= y0 - pad_m):
                out.append((ox, oy))
    return out


def poly_area(points):
    """Area in pixel quadrati (valore assoluto della formula della scarpa)."""
    total = 0.0
    for i in range(len(points)):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % len(points)]
        total += x0 * y1 - x1 * y0
    return abs(total) * 0.5


def iter_samples(a, b, step_px, include_start=True):
    """Campioni regolari lungo un segmento.

    Restituisce (x, y, tx, ty, nx, ny): punto, versore tangente e versore
    normale. Usato per giunti, traverse, montanti e texture.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 0.001:
        return
    tx, ty = dx / length, dy / length
    nx, ny = -ty, tx
    n = max(1, int(length / step_px))
    step = length / n
    first = 0 if include_start else 1
    for i in range(first, n + 1):
        dist = i * step
        yield (a[0] + tx * dist, a[1] + ty * dist, tx, ty, nx, ny)


def ipair(pt):
    return int(round(pt[0])), int(round(pt[1]))


def ground_base(rng):
    """Texture di base: una mattonella 64x64 ripetuta, piu' poche macchie ampie."""
    tile = Image.new("RGB", (64, 64), "#c8bfab")
    td = ImageDraw.Draw(tile, "RGBA")
    for _ in range(260):
        x, y = rng.randrange(64), rng.randrange(64)
        v = rng.randint(-10, 10)
        td.point((x, y), fill=(128 + v, 128 + v, 128 + v, rng.randint(18, 42)))
    img = Image.new("RGB", (SECTOR_PX, SECTOR_PX))
    for ty in range(0, SECTOR_PX, 64):
        for tx in range(0, SECTOR_PX, 64):
            img.paste(tile, (tx, ty))
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(36):
        cx, cy = rng.randrange(SECTOR_PX), rng.randrange(SECTOR_PX)
        r = rng.randint(24, 88)
        d.ellipse((cx - r, cy - r, cx + r, cy + r),
                  fill=rgba("#b9b09c", rng.randint(6, 14)))
    return img


def clipped_patch(img, pts, painter):
    """Disegna un motivo solo dentro un poligono, tramite maschera e patch locale."""
    x0, y0, x1, y1 = bbox_of(pts)
    ix0 = max(0, int(math.floor(x0)) - 2)
    iy0 = max(0, int(math.floor(y0)) - 2)
    ix1 = min(SECTOR_PX, int(math.ceil(x1)) + 3)
    iy1 = min(SECTOR_PX, int(math.ceil(y1)) + 3)
    if ix1 <= ix0 or iy1 <= iy0:
        return
    w, h = ix1 - ix0, iy1 - iy0
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(x - ix0, y - iy0) for x, y in pts], fill=255)
    if not mask.getbbox():
        return
    patch = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    painter(ImageDraw.Draw(patch, "RGBA"), ix0, iy0, mask, w, h)
    img.paste(patch, (ix0, iy0), mask)


# --------------------------------------------------------------------------- #
# Superfici
# --------------------------------------------------------------------------- #

def draw_landcover(img, sx, sy):
    d = ImageDraw.Draw(img, "RGBA")
    for lc in W["landcover"]:
        footprint = lc["footprint"]
        if len(footprint) < 3:
            continue
        if (sx, sy) not in affected(footprint, pad_m=2):
            continue
        local = [to_local(p, sx, sy) for p in footprint]
        kind = lc["kind"]
        base = LANDCOVER_COLORS.get(kind, "#b9b5a6")
        green = kind in GREEN_KINDS
        key = lc.get("id", kind)

        def painter(pd, ox, oy, mask, w, h):
            poly = [(x - ox, y - oy) for x, y in local]
            pd.polygon(poly, fill=rgba(base, 255))
            minx, miny, maxx, maxy = poly_bounds(poly)
            rng = seeded(f"tuft:{key}:{sx}:{sy}")
            if green:
                count = min(520, max(12, int(poly_area(poly) / PPM ** 2 * 0.45)))
                for _ in range(count):
                    px = rng.uniform(minx, maxx)
                    py = rng.uniform(miny, maxy)
                    mx, my = int(px) - ox, int(py) - oy
                    if not (0 <= mx < w and 0 <= my < h) or mask.getpixel((mx, my)) != 255:
                        continue
                    pd.line((px - 1, py + 1, px, py - 2),
                            fill=rgba(P["green_dark"], rng.randint(70, 110)), width=1)
                    pd.point((px + 1, py - 1),
                             fill=rgba(P["green_light"], rng.randint(110, 160)))
            else:
                for _ in range(min(300, max(8, int(poly_area(poly) / PPM ** 2 * 0.12)))):
                    px = rng.uniform(minx, maxx)
                    py = rng.uniform(miny, maxy)
                    mx, my = int(px) - ox, int(py) - oy
                    if not (0 <= mx < w and 0 <= my < h) or mask.getpixel((mx, my)) != 255:
                        continue
                    pd.point((px, py), fill=rgba(P["ink_soft"], rng.randint(18, 38)))

        clipped_patch(img, local, painter)

    # Reticolato dei vigneti: file regolari, non linee casuali.
    for lc in W["landcover"]:
        if lc["kind"] != "vineyard":
            continue
        footprint = lc["footprint"]
        if (sx, sy) not in affected(footprint, pad_m=2):
            continue
        local = [to_local(p, sx, sy) for p in footprint]
        x0, y0, x1, y1 = bbox_of(local)
        for yy in range(int(y0) + 8, int(y1), 16):
            d.line((x0, yy, x1, yy), fill=rgba(P["green_dark"], 55), width=1)


def poly_bounds(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def draw_parking(img, sx, sy):
    for park in W["parking"]:
        footprint = park["footprint"]
        if len(footprint) < 3 or (sx, sy) not in affected(footprint, pad_m=2):
            continue
        local = [to_local(p, sx, sy) for p in footprint]

        def painter(pd, ox, oy, mask, w, h):
            poly = [(x - ox, y - oy) for x, y in local]
            pd.polygon(poly, fill=rgba(P["asphalt"], 255))
            # Asse principale = lato piu' lungo: gli stalli sono perpendicolari.
            best = None
            for i in range(len(poly)):
                a, b = poly[i], poly[(i + 1) % len(poly)]
                dx, dy = b[0] - a[0], b[1] - a[1]
                ln = math.hypot(dx, dy)
                if best is None or ln > best[0]:
                    best = (ln, dx / ln if ln else 1.0, dy / ln if ln else 0.0)
            _, ux, uy = best
            nx, ny = -uy, ux
            projs_u = [x * ux + y * uy for x, y in poly]
            projs_n = [x * nx + y * ny for x, y in poly]
            umin, umax = min(projs_u), max(projs_u)
            nmin, nmax = min(projs_n), max(projs_n)
            step = 2.5 * PPM  # 2,5 m per stallo
            t = math.ceil(umin / step) * step
            while t < umax:
                cx, cy = ux * t, uy * t
                pd.line((cx + nx * nmin, cy + ny * nmin,
                         cx + nx * nmax, cy + ny * nmax),
                        fill=rgba(P["white"], 145), width=2)
                t += step

        clipped_patch(img, local, painter)


def draw_platforms(img, sx, sy):
    for platform in W["platforms"]:
        footprint = platform["footprint"]
        if len(footprint) < 3 or (sx, sy) not in affected(footprint, pad_m=2):
            continue
        local = [to_local(p, sx, sy) for p in footprint]

        def painter(pd, ox, oy, mask, w, h):
            poly = [(x - ox, y - oy) for x, y in local]
            pd.polygon(poly, fill=rgba(P["concrete_light"], 255))
            minx, miny, maxx, maxy = poly_bounds(poly)
            # Lastricato regolare: giunti ogni 0,5 m, piu' marcati ogni 1 m.
            for gx in range(int(minx // 8) * 8, int(maxx) + 9, 8):
                pd.line((gx, miny - 1, gx, maxy + 1),
                        fill=rgba(P["concrete"], 110), width=1)
            for gy in range(int(miny // 8) * 8, int(maxy) + 9, 8):
                pd.line((minx - 1, gy, maxx + 1, gy),
                        fill=rgba(P["concrete"], 110), width=1)
            for gx in range(int(minx // 16) * 16, int(maxx) + 17, 16):
                pd.line((gx, miny - 1, gx, maxy + 1),
                        fill=rgba(P["ink"], 38), width=1)
            for gy in range(int(miny // 16) * 16, int(maxy) + 17, 16):
                pd.line((minx - 1, gy, maxx + 1, gy),
                        fill=rgba(P["ink"], 38), width=1)
            # Bordo giallo di sicurezza (tagliato dalla maschera sul perimetro).
            for i in range(len(poly)):
                a, b = poly[i], poly[(i + 1) % len(poly)]
                pd.line((a, b), fill=rgba(P["yellow"], 225), width=12)
                pd.line((a, b), fill=rgba(P["ink"], 55), width=1)

        clipped_patch(img, local, painter)


# --------------------------------------------------------------------------- #
# Strade
# --------------------------------------------------------------------------- #

def draw_carriageway(d, road, local, sx, sy):
    width_i = max(16, int(round(road["width_m"] * PPM)))
    half = width_i / 2.0
    sw = 3  # marciapiede di 3 px per lato
    rng = seeded(f"asphalt:{road.get('id', '')}:{sx}:{sy}")

    # Tre passate opache: nessun alone da alpha sovrapposto.
    d.line(local, fill=rgba(P["curb"], 255), width=width_i + 2 * sw, joint="miter")
    d.line(local, fill=rgba(P["concrete"], 255), width=width_i + 2 * sw - 2,
           joint="miter")
    d.line(local, fill=rgba(P["asphalt"], 255), width=width_i, joint="miter")

    for i in range(len(local) - 1):
        a, b = local[i], local[i + 1]
        # Giunti regolari dell'asfalto ogni 2 m.
        for cx, cy, _, _, nx, ny in iter_samples(a, b, 32, include_start=False):
            d.line((cx - nx * (half - 1), cy - ny * (half - 1),
                    cx + nx * (half - 1), cy + ny * (half - 1)),
                   fill=rgba(P["asphalt_dark"], 45), width=1)
        # Texture fine: un granello ogni 6 px, sempre entro la carreggiata.
        for cx, cy, _, _, nx, ny in iter_samples(a, b, 6):
            off = rng.uniform(-half + 2, half - 2)
            px, py = int(cx + nx * off), int(cy + ny * off)
            color = P["asphalt_light"] if rng.random() < 0.5 else P["asphalt_dark"]
            d.point((px, py), fill=rgba(color, rng.randint(35, 70)))
        # Giunti del marciapiede ogni 1 m, sui due lati.
        for cx, cy, _, _, nx, ny in iter_samples(a, b, 16, include_start=False):
            for side in (-1, 1):
                p0 = (cx + nx * (half + 0.4) * side, cy + ny * (half + 0.4) * side)
                p1 = (cx + nx * (half + sw - 0.4) * side,
                      cy + ny * (half + sw - 0.4) * side)
                d.line((p0, p1), fill=rgba(P["ink"], 35), width=1)
        # Strisce pedonali SOLO per highway=crossing: perpendicolari, non una
        # banda chiara longitudinale al centro della strada.
        if road["kind"] == "crossing":
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            for t in range(5):
                cx = a[0] + (b[0] - a[0]) * (0.15 + t * 0.17)
                cy = a[1] + (b[1] - a[1]) * (0.15 + t * 0.17)
                dx, dy = b[0] - a[0], b[1] - a[1]
                nx, ny = -dy / length, dx / length
                d.line((cx - nx * (half - 2), cy - ny * (half - 2),
                        cx + nx * (half - 2), cy + ny * (half - 2)),
                       fill=rgba(P["white"], 215), width=2)


def draw_footway(d, road, local, sx, sy):
    kind = road["kind"]
    width_i = max(12, int(round(road["width_m"] * PPM)))
    base = STEP_GREY if kind == "steps" else PATH_SAND
    d.line(local, fill=rgba(base, 255), width=width_i, joint="miter")
    rng = seeded(f"path:{road.get('id', '')}:{sx}:{sy}")
    half = width_i / 2.0
    for i in range(len(local) - 1):
        a, b = local[i], local[i + 1]
        for cx, cy, _, _, nx, ny in iter_samples(a, b, 5):
            off = rng.uniform(-half + 2, half - 2)
            d.point((int(cx + nx * off), int(cy + ny * off)),
                    fill=rgba(P["ink_soft"], rng.randint(16, 40)))
        if kind == "steps":
            for cx, cy, _, _, nx, ny in iter_samples(a, b, 5, include_start=False):
                d.line((cx - nx * half, cy - ny * half,
                        cx + nx * half, cy + ny * half),
                       fill=rgba(P["ink"], 70), width=1)


def draw_roads(img, sx, sy):
    d = ImageDraw.Draw(img, "RGBA")
    for road in W["roads"]:
        pts = road["points"]
        if len(pts) < 2:
            continue
        pad = 5 if road["kind"] in CARRIAGEWAYS else 2
        if (sx, sy) not in affected(pts, pad_m=pad):
            continue
        local = [to_local(p, sx, sy) for p in pts]
        if road["kind"] in FOOTWAYS:
            draw_footway(d, road, local, sx, sy)
        elif road["kind"] in CARRIAGEWAYS:
            draw_carriageway(d, road, local, sx, sy)
        else:
            d.line(local, fill=rgba(PATH_SAND, 255),
                   width=max(12, int(road["width_m"] * PPM)), joint="miter")


# --------------------------------------------------------------------------- #
# Ferrovia, recinzioni e ancoraggio degli edifici
# --------------------------------------------------------------------------- #

def draw_rails(img, sx, sy):
    d = ImageDraw.Draw(img, "RGBA")
    ballast = int(3.6 * PPM)  # 3,6 m di massicciata
    for rail in W["rails"]:
        pts = rail["points"]
        if len(pts) < 2 or (sx, sy) not in affected(pts, pad_m=6):
            continue
        local = [to_local(p, sx, sy) for p in pts]
        d.line(local, fill=rgba(GRAVEL, 255), width=ballast, joint="miter")

        rng = seeded(f"ballast:{rail.get('id', '')}:{sx}:{sy}")
        for i in range(len(local) - 1):
            a, b = local[i], local[i + 1]
            # Ghiaia fine sulla massicciata.
            for cx, cy, _, _, nx, ny in iter_samples(a, b, 5):
                off = rng.uniform(-ballast / 2 + 3, ballast / 2 - 3)
                d.point((int(cx + nx * off), int(cy + ny * off)),
                        fill=rgba(GRAVEL_LIGHT if rng.random() < 0.5 else P["ink_soft"],
                                  rng.randint(30, 60)))
            # Traverse ogni 0,75 m.
            for cx, cy, _, _, nx, ny in iter_samples(a, b, 12):
                d.line((cx - nx * 22, cy - ny * 22,
                        cx + nx * 22, cy + ny * 22),
                       fill=rgba(P["brown"], 215), width=3)
            # Due rotaie parallele (scartamento 1,435 m) con bordo metallico.
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 0.001:
                continue
            tx, ty = dx / length, dy / length
            nx, ny = -ty, tx
            for offset in (-11.5, 11.5):
                ra = (a[0] + nx * offset, a[1] + ny * offset)
                rb = (b[0] + nx * offset, b[1] + ny * offset)
                d.line((ra, rb), fill=rgba(RAIL_DARK, 255), width=3)
                inner = offset - (1 if offset > 0 else -1)
                d.line((ra[0] + nx * (inner - offset), ra[1] + ny * (inner - offset),
                        rb[0] + nx * (inner - offset), rb[1] + ny * (inner - offset)),
                       fill=rgba(P["metal_light"], 190), width=1)


def draw_barriers(img, sx, sy):
    d = ImageDraw.Draw(img, "RGBA")
    for barrier in W["barriers"]:
        pts = barrier["points"]
        if len(pts) < 2 or (sx, sy) not in affected(pts, pad_m=2):
            continue
        local = [to_local(p, sx, sy) for p in pts]
        for i in range(len(local) - 1):
            a, b = local[i], local[i + 1]
            posts = list(iter_samples(a, b, 24))  # un montante ogni 1,5 m
            for j in range(len(posts) - 1):
                p, q = posts[j], posts[j + 1]
                d.line((ipair(p), ipair(q)), fill=rgba(P["metal"], 205), width=2)
            for cx, cy, _, _, _, _ in posts:
                x, y = ipair((cx, cy))
                d.rectangle((x - 2, y - 2, x + 2, y + 2),
                            fill=rgba(P["metal"], 255))
                d.point((x - 1, y - 1), fill=rgba(P["metal_light"], 255))


def draw_building_contact(img, sx, sy):
    """Solo ombra di contatto leggera sotto il bordo sud: nessun poligono sfalsato."""
    d = ImageDraw.Draw(img, "RGBA")
    for building in W["buildings"]:
        footprint = building["footprint"]
        if len(footprint) < 3 or (sx, sy) not in affected(footprint, pad_m=2):
            continue
        local = [to_local(p, sx, sy) for p in footprint]
        south = max(p[1] for p in local)
        for i in range(len(local)):
            a, b = local[i], local[(i + 1) % len(local)]
            if (a[1] + b[1]) / 2 < south - 6:
                continue
            d.line((a[0], a[1] + 2, b[0], b[1] + 2),
                   fill=rgba(P["ink_soft"], 28), width=12)
            d.line((a[0], a[1] + 1, b[0], b[1] + 1),
                   fill=rgba(P["ink_soft"], 38), width=4)


# --------------------------------------------------------------------------- #
# Settore e manifest
# --------------------------------------------------------------------------- #

def draw_sector(ox, oy):
    rng = seeded(f"ground:{ox}:{oy}")
    img = ground_base(rng)
    draw_landcover(img, ox, oy)
    draw_parking(img, ox, oy)
    draw_roads(img, ox, oy)
    draw_rails(img, ox, oy)
    draw_platforms(img, ox, oy)
    draw_building_contact(img, ox, oy)
    draw_barriers(img, ox, oy)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for ox in ORIGINS:
        for oy in ORIGINS:
            img = draw_sector(ox, oy)
            save_png(img, OUT / f"sector_{ox}_{oy}.png")
            count += 1
    manifest = {
        "sector_m": SECTOR_M,
        "sector_px": SECTOR_PX,
        "source_ppm": PPM,
        "engine_ppm": 16,
        "engine_scale": 1,
        "origins": list(ORIGINS),
        "count": count,
        "naming": "sector_{x}_{y}.png where x,y are metres (origin top-left of sector)",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"OK {count} settori suolo a {PPM} px/m ({SECTOR_PX}x{SECTOR_PX} px)")


if __name__ == "__main__":
    main()
