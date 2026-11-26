#!/usr/bin/env python3
"""Genera i settori del suolo in pixel art dal mondo OSM convertito.

Ogni settore copre 64 x 64 metri e viene disegnato direttamente a 16 px/m
(1024 x 1024 px): il motore NON applica piu' alcuna scala (engine_scale = 1).

La geometria (strade, binari, banchine, parcheggi, recinzioni e perimetri)
arriva soltanto da data/world/pianura_world.json. Qui vengono aggiunti solo
rivestimenti e dettagli regolari, tutti deterministici e senza anti-aliasing.
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

# Marciapiedi: 1 m = 16 px. Le carreggiate restano esattamente quelle OSM:
# il marciapiede viene aggiunto ALL'ESTERNO della larghezza carrabile.
SIDEWALK_PX = {
    "residential": 24,     # 1,5 m
    "unclassified": 24,    # 1,5 m
    "service": 24,         # 1,5 m
    "living_street": 24,   # 1,5 m
    "tertiary": 32,        # 2,0 m
    "secondary": 32,       # 2,0 m
    "primary": 32,         # 2,0 m
    "trunk": 32,           # 2,0 m
}
DEFAULT_SIDEWALK_PX = 24
CENTERLINE_KINDS = {"secondary", "primary", "tertiary"}
CENTERLINE_COLORS = {
    "secondary": P["white"],
    "primary": P["yellow"],
    "tertiary": P["yellow"],
}

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


def poly_bounds(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


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


def shifted(a, b, nx, ny, offset):
    """Segmento parallelo, spostato di offset pixel lungo la normale."""
    return ((a[0] + nx * offset, a[1] + ny * offset),
            (b[0] + nx * offset, b[1] + ny * offset))


def side_offset(kind):
    return SIDEWALK_PX.get(kind, DEFAULT_SIDEWALK_PX)


def longest_edge_unit(poly):
    """Direzione del lato piu' lungo: asse di marciapiedi/stalli/banchine."""
    best = (0.0, 1.0, 0.0)
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        if ln > best[0]:
            best = (ln, dx / ln, dy / ln)
    return best[1], best[2]


def inside_poly(poly, x, y):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def inward_normal(a, b, poly):
    """Normale del lato che punta dentro il poligono."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy)
    if ln < 0.001:
        return 0.0, 0.0
    nx, ny = -dy / ln, dx / ln
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if inside_poly(poly, mx + nx * 2, my + ny * 2):
        return nx, ny
    return -nx, -ny


def near_any(points, x, y, radius_px):
    limit = radius_px * radius_px
    return any((px - x) ** 2 + (py - y) ** 2 <= limit for px, py in points)


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
        phase = seeded(f"cover-phase:{key}:{sx}:{sy}").randrange(9)
        ux, uy = longest_edge_unit(local)
        nx, ny = -uy, ux

        def painter(pd, ox, oy, mask, w, h):
            poly = [(x - ox, y - oy) for x, y in local]
            pd.polygon(poly, fill=rgba(base, 255))
            minx, miny, maxx, maxy = poly_bounds(poly)

            # Vigneti: file regolari parallele al lato lungo, ritagliate.
            if kind == "vineyard":
                us = [x * ux + y * uy for x, y in poly]
                ns = [x * nx + y * ny for x, y in poly]
                umin, umax = min(us), max(us)
                nmin, nmax = min(ns), max(ns)
                n = math.ceil(nmin / 16) * 16
                while n < nmax:
                    pd.line((ux * umin + nx * n, uy * umin + ny * n,
                             ux * umax + nx * n, uy * umax + ny * n),
                            fill=rgba(P["green_dark"], 65), width=1)
                    n += 16

            # Ciuffi e granelli su griglia sfalsata: posizioni ordinate,
            # selezione deterministica, nessuna sparsita' casuale.
            step = 12 if green else 16
            x_start = int(minx // step) * step
            y_start = int(miny // step) * step
            for row, gy in enumerate(range(y_start, int(maxy) + step, step)):
                for col, gx in enumerate(range(x_start, int(maxx) + step, step)):
                    if green:
                        if (row * 13 + col * 7 + phase) % 9 >= 5:
                            continue
                    elif (row * 5 + col * 3 + phase) % 11 != 0:
                        continue
                    px = gx + (row % 2) * (step // 2)
                    py = gy + ((col % 3) - 1)
                    mx, my = int(px) - ox, int(py) - oy
                    if not (0 <= mx < w and 0 <= my < h) or mask.getpixel((mx, my)) != 255:
                        continue
                    if green:
                        variant = (row + col * 2 + phase) % 3
                        if variant == 0:
                            pd.line((px - 2, py + 2, px, py - 3),
                                    fill=rgba(P["green_dark"], 105), width=1)
                            pd.line((px, py + 2, px + 2, py - 2),
                                    fill=rgba(P["green_dark"], 90), width=1)
                        elif variant == 1:
                            pd.line((px - 1, py + 2, px + 1, py - 3),
                                    fill=rgba(P["green_dark"], 95), width=1)
                        else:
                            pd.line((px, py + 2, px, py - 2),
                                    fill=rgba(P["green_dark"], 85), width=1)
                            pd.point((px + 2, py - 1),
                                     fill=rgba(P["green_light"], 120))
                        pd.point((px, py - 1), fill=rgba(P["green_light"], 140))
                    else:
                        pd.point((px, py), fill=rgba(P["ink_soft"], 26))

        clipped_patch(img, local, painter)


def draw_parking(img, sx, sy):
    for park in W["parking"]:
        footprint = park["footprint"]
        if len(footprint) < 3 or (sx, sy) not in affected(footprint, pad_m=2):
            continue
        local = [to_local(p, sx, sy) for p in footprint]

        def painter(pd, ox, oy, mask, w, h):
            poly = [(x - ox, y - oy) for x, y in local]
            pd.polygon(poly, fill=rgba(P["asphalt"], 255))
            ux, uy = longest_edge_unit(poly)
            nx, ny = -uy, ux
            projs_u = [x * ux + y * uy for x, y in poly]
            projs_n = [x * nx + y * ny for x, y in poly]
            umin, umax = min(projs_u), max(projs_u)
            nmin, nmax = min(projs_n), max(projs_n)
            # Griglia di giunti regolare, poi stalli perpendicolari all'asse.
            for step, color, alpha in ((32, P["asphalt_dark"], 35),
                                       (16, P["asphalt_light"], 22)):
                t = math.ceil(umin / step) * step
                while t < umax:
                    pd.line((ux * t + nx * nmin, uy * t + ny * nmin,
                             ux * t + nx * nmax, uy * t + ny * nmax),
                            fill=rgba(color, alpha), width=1)
                    t += step
            step = 2.5 * PPM
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
            ux, uy = longest_edge_unit(poly)
            nx, ny = -uy, ux
            us = [x * ux + y * uy for x, y in poly]
            ns = [x * nx + y * ny for x, y in poly]
            umin, umax = min(us), max(us)
            nmin, nmax = min(ns), max(ns)

            # Lastricato regolare allineato alla banchina: 0,5 m e 1 m.
            for step, color, alpha in ((8, P["concrete"], 110),
                                       (16, P["ink"], 38)):
                t = math.ceil(umin / step) * step
                while t < umax:
                    pd.line((ux * t + nx * (nmin - 2), uy * t + ny * (nmin - 2),
                             ux * t + nx * (nmax + 2), uy * t + ny * (nmax + 2)),
                            fill=rgba(color, alpha), width=1)
                    t += step
                s = math.ceil(nmin / step) * step
                while s < nmax:
                    pd.line((ux * (umin - 2) + nx * s, uy * (umin - 2) + ny * s,
                             ux * (umax + 2) + nx * s, uy * (umax + 2) + ny * s),
                            fill=rgba(color, alpha), width=1)
                    s += step

            # Bordo giallo con contorno scuro e pallini tattili SOLO sul bordo.
            for i in range(len(poly)):
                a, b = poly[i], poly[(i + 1) % len(poly)]
                pd.line((a, b), fill=rgba(P["ink"], 65), width=14)
                pd.line((a, b), fill=rgba(P["yellow"], 235), width=10)
                dx, dy = b[0] - a[0], b[1] - a[1]
                ln = math.hypot(dx, dy)
                if ln < 12:
                    continue
                tx, ty = dx / ln, dy / ln
                inx, iny = inward_normal(a, b, poly)
                for dist in range(6, int(ln) - 5, 8):
                    for inset in (2, 4):
                        x = a[0] + tx * dist + inx * inset
                        y = a[1] + ty * dist + iny * inset
                        pd.ellipse((x - 1, y - 1, x + 1, y + 1),
                                   fill=rgba(P["white"], 190))

        clipped_patch(img, local, painter)


# --------------------------------------------------------------------------- #
# Strade
# --------------------------------------------------------------------------- #

def draw_footway(d, road, local, sx, sy):
    kind = road["kind"]
    width_i = max(12, int(round(road["width_m"] * PPM)))
    base = STEP_GREY if kind == "steps" else PATH_SAND
    d.line(local, fill=rgba(base, 255), width=width_i, joint="miter")
    half = width_i / 2.0
    for i in range(len(local) - 1):
        a, b = local[i], local[i + 1]
        for j, (cx, cy, _, _, nx, ny) in enumerate(iter_samples(a, b, 6)):
            off = ((j % 5) - 2) * 2.5
            if abs(off) < half - 2:
                d.point((int(cx + nx * off), int(cy + ny * off)),
                        fill=rgba(P["ink_soft"], 22))
        if kind == "steps":
            for cx, cy, _, _, nx, ny in iter_samples(a, b, 5, include_start=False):
                d.line((cx - nx * half, cy - ny * half,
                        cx + nx * half, cy + ny * half),
                       fill=rgba(P["ink"], 70), width=1)


def collect_tactile_sources(sx, sy):
    """Punti OSM (banchine e crossing) presso cui mettere la segnalazione tattile."""
    sources = []
    for platform in W["platforms"]:
        footprint = platform["footprint"]
        if len(footprint) < 3 or (sx, sy) not in affected(footprint, pad_m=3):
            continue
        poly = [to_local(p, sx, sy) for p in footprint]
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            for cx, cy, _, _, _, _ in iter_samples(a, b, 12):
                sources.append((cx, cy))
    for road in W["roads"]:
        if road["kind"] == "crossing":
            pts = road["points"]
            if pts and (sx, sy) in affected(pts, pad_m=3):
                sources.extend(to_local(p, sx, sy) for p in pts)
    return sources


def draw_tactile_strip(d, cx, cy, tx, ty, nx, ny, half, sw, side):
    """Striscia tattile gialla con pallini, dentro il marciapiede."""
    if sw < 16:
        return
    center = side * (half + 5)
    a = (cx - tx * 6 + nx * center, cy - ty * 6 + ny * center)
    b = (cx + tx * 6 + nx * center, cy + ty * 6 + ny * center)
    d.line((a, b), fill=rgba(P["yellow"], 140), width=8)
    for along in (-4, 0, 4):
        for depth in (3, 7):
            if depth + 1 >= sw:
                continue
            off = side * (half + depth)
            x = int(round(cx + tx * along + nx * off))
            y = int(round(cy + ty * along + ny * off))
            d.ellipse((x - 1, y - 1, x + 1, y + 1),
                      fill=rgba(P["white"], 195))


def draw_sidewalk_bases(img, sx, sy):
    """Prima passata: cordoli e superficie, senza toccare la carreggiata OSM."""
    d = ImageDraw.Draw(img, "RGBA")
    for road in W["roads"]:
        if road["kind"] not in CARRIAGEWAYS:
            continue
        pts = road["points"]
        if len(pts) < 2 or (sx, sy) not in affected(pts, pad_m=6):
            continue
        local = [to_local(p, sx, sy) for p in pts]
        width_i = max(16, int(round(road["width_m"] * PPM)))
        sw = side_offset(road["kind"])
        d.line(local, fill=rgba(P["ink_soft"], 110),
               width=width_i + 2 * sw + 2, joint="miter")
        d.line(local, fill=rgba(P["curb"], 255),
               width=width_i + 2 * sw, joint="miter")
        d.line(local, fill=rgba(P["concrete_light"], 255),
               width=width_i + 2 * sw - 4, joint="miter")
        d.line(local, fill=rgba(P["curb"], 255),
               width=width_i + 4, joint="miter")


def draw_sidewalk_details(img, sx, sy, tactile_sources):
    """Seconda passata: giunti ogni 1 m e tattili presso banchine/crossing."""
    d = ImageDraw.Draw(img, "RGBA")
    for road in W["roads"]:
        kind = road["kind"]
        if kind not in CARRIAGEWAYS:
            continue
        pts = road["points"]
        if len(pts) < 2 or (sx, sy) not in affected(pts, pad_m=6):
            continue
        local = [to_local(p, sx, sy) for p in pts]
        width_i = max(16, int(round(road["width_m"] * PPM)))
        sw = side_offset(kind)
        half = width_i / 2.0
        phase = seeded(f"tactile:{road.get('id', '')}:{sx}:{sy}").randrange(2)
        for i in range(len(local) - 1):
            a, b = local[i], local[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 0.001:
                continue
            nx, ny = -dy / length, dx / length
            for side in (-1, 1):
                mid = side * (half + sw * 0.55)
                sa, sb = shifted(a, b, nx, ny, mid)
                d.line((sa, sb), fill=rgba(P["concrete"], 105), width=1)
            for j, (cx, cy, tx, ty, nx, ny) in enumerate(
                    iter_samples(a, b, 16, include_start=False)):
                for side in (-1, 1):
                    p0 = (cx + nx * (half + 2) * side,
                          cy + ny * (half + 2) * side)
                    p1 = (cx + nx * (half + sw - 2) * side,
                          cy + ny * (half + sw - 2) * side)
                    d.line((p0, p1), fill=rgba(P["ink"], 48), width=1)
                if tactile_sources and near_any(tactile_sources, cx, cy, 24):
                    if (i + j + phase) % 2 == 0:
                        for side in (-1, 1):
                            draw_tactile_strip(d, cx, cy, tx, ty, nx, ny,
                                               half, sw, side)


def draw_carriageway(d, road, local, sx, sy):
    """Asfalto OSM: texture a griglia, giunti, rattoppi e tombini regolari."""
    width_i = max(16, int(round(road["width_m"] * PPM)))
    half = width_i / 2.0
    kind = road["kind"]
    phase = seeded(f"asphalt:{road.get('id', '')}:{sx}:{sy}").randrange(3)

    d.line(local, fill=rgba(P["asphalt"], 255), width=width_i, joint="miter")

    for i in range(len(local) - 1):
        a, b = local[i], local[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length < 0.001:
            continue
        tx, ty = dx / length, dy / length
        nx, ny = -ty, tx

        # Rattoppi ogni 16 m, allineati alla strada e sempre dentro l'asfalto.
        hpatch_w = min(24.0, half - 6)
        if hpatch_w > 6:
            for k, dist in enumerate(range(96, int(length), 256)):
                hlen = 32
                if dist - hlen < 4 or dist + hlen > length - 4:
                    continue
                cx, cy = a[0] + tx * dist, a[1] + ty * dist
                poly = [
                    (cx - tx * hlen - nx * hpatch_w, cy - ty * hlen - ny * hpatch_w),
                    (cx + tx * hlen - nx * hpatch_w, cy + ty * hlen - ny * hpatch_w),
                    (cx + tx * hlen + nx * hpatch_w, cy + ty * hlen + ny * hpatch_w),
                    (cx - tx * hlen + nx * hpatch_w, cy - ty * hlen + ny * hpatch_w),
                ]
                fill = P["asphalt_light"] if (i + k + phase) % 2 == 0 else P["asphalt_dark"]
                d.polygon(poly, fill=rgba(fill, 60))
                d.line(poly + [poly[0]], fill=rgba(P["ink_soft"], 30), width=1)

        # Texture fine su griglia regolare, non dispersione casuale.
        for j, (cx, cy, _, _, nx, ny) in enumerate(iter_samples(a, b, 8)):
            for lane in range(-3, 4):
                off = lane * 6 + (j % 2) * 3
                if abs(off) > half - 3:
                    continue
                color = (P["asphalt_light"] if (j + lane + phase) % 3 == 0
                         else P["asphalt_dark"])
                d.point((int(cx + nx * off), int(cy + ny * off)),
                        fill=rgba(color, 38))

        # Giunti trasversali ogni 2 m.
        for cx, cy, _, _, nx, ny in iter_samples(a, b, 32, include_start=False):
            d.line((cx - nx * (half - 1), cy - ny * (half - 1),
                    cx + nx * (half - 1), cy + ny * (half - 1)),
                   fill=rgba(P["asphalt_dark"], 55), width=1)

    # Linea centrale tratteggiata solo sulle strade gerarchiche: 1,5 m di
    # tratto ogni 4,5 m, 2 px di spessore. Mai su residential/service.
    if kind in CENTERLINE_KINDS:
        color = CENTERLINE_COLORS[kind]
        for i in range(len(local) - 1):
            a, b = local[i], local[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 0.001:
                continue
            tx, ty = dx / length, dy / length
            dist = 0
            while dist < length:
                end = min(dist + 24, length)
                d.line((a[0] + tx * dist, a[1] + ty * dist,
                        a[0] + tx * end, a[1] + ty * end),
                       fill=rgba(color, 180), width=2)
                dist += 72

    # Tombini ogni 24 m, sfalsati sui due lati e fuori dalla linea centrale.
    if half >= 12:
        for i in range(len(local) - 1):
            a, b = local[i], local[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 0.001:
                continue
            tx, ty = dx / length, dy / length
            nx, ny = -ty, tx
            for k, dist in enumerate(range(160, int(length), 384)):
                if dist < 12 or dist > length - 12:
                    continue
                side = -1 if (i + k + phase) % 2 == 0 else 1
                off = side * min(half * 0.5, half - 8)
                cx = a[0] + tx * dist + nx * off
                cy = a[1] + ty * dist + ny * off
                d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5),
                          fill=rgba(P["metal"], 215),
                          outline=rgba(P["ink"], 120), width=1)
                d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3),
                          fill=rgba(P["metal_light"], 175))
                d.line((cx - 2, cy, cx + 2, cy),
                       fill=rgba(P["ink_soft"], 90), width=1)


def draw_crossings(img, sx, sy):
    """Strisce pedonali solo se OSM ha esplicitamente highway=crossing."""
    d = ImageDraw.Draw(img, "RGBA")
    for road in W["roads"]:
        if road["kind"] != "crossing":
            continue
        pts = road["points"]
        if len(pts) < 2 or (sx, sy) not in affected(pts, pad_m=3):
            continue
        local = [to_local(p, sx, sy) for p in pts]
        width_i = max(24, int(round(road["width_m"] * PPM)))
        half = width_i / 2.0
        for i in range(len(local) - 1):
            a, b = local[i], local[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 0.001:
                continue
            nx, ny = -dy / length, dx / length
            for k in range(5):
                dist = length * (0.15 + k * 0.17)
                cx = a[0] + dx * dist / length
                cy = a[1] + dy * dist / length
                d.line((cx - nx * (half - 2), cy - ny * (half - 2),
                        cx + nx * (half - 2), cy + ny * (half - 2)),
                       fill=rgba(P["white"], 220), width=3)


def draw_footways(img, sx, sy):
    """Sentieri e gradini: vanno sotto marciapiedi e carreggiate."""
    d = ImageDraw.Draw(img, "RGBA")
    for road in W["roads"]:
        if road["kind"] not in FOOTWAYS:
            continue
        pts = road["points"]
        if len(pts) < 2 or (sx, sy) not in affected(pts, pad_m=2):
            continue
        local = [to_local(p, sx, sy) for p in pts]
        draw_footway(d, road, local, sx, sy)


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

        for i in range(len(local) - 1):
            a, b = local[i], local[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 0.001:
                continue
            nx, ny = -dy / length, dx / length
            for side in (-1, 1):
                sa, sb = shifted(a, b, nx, ny, side * (ballast / 2 - 2))
                d.line((sa, sb), fill=rgba(P["ink_soft"], 75), width=2)

        for i in range(len(local) - 1):
            a, b = local[i], local[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 0.001:
                continue
            tx, ty = dx / length, dy / length
            nx, ny = -ty, tx

            # Ghiaia su griglia regolare: nessun punto sparso a caso.
            for j, (cx, cy, _, _, gnx, gny) in enumerate(iter_samples(a, b, 8)):
                for lane in range(-3, 4):
                    off = lane * 8 + (j % 2) * 4
                    if abs(off) > ballast / 2 - 4:
                        continue
                    color = GRAVEL_LIGHT if (j + lane) % 3 else P["ink_soft"]
                    d.point((int(cx + gnx * off), int(cy + gny * off)),
                            fill=rgba(color, 45))

            # Drenaggio sui due lati della massicciata, con scarichi regolari.
            for side in (-1, 1):
                ditch = side * (ballast / 2 + 3)
                bank = side * (ballast / 2 + 6)
                da, db = shifted(a, b, nx, ny, ditch)
                ba, bb = shifted(a, b, nx, ny, bank)
                d.line((da, db), fill=rgba(P["ink_soft"], 110), width=3)
                d.line((ba, bb), fill=rgba(GRAVEL_LIGHT, 90), width=1)
                for dist in range(32, int(length), 64):
                    cx, cy = a[0] + tx * dist + nx * ditch, a[1] + ty * dist + ny * ditch
                    d.line((cx - tx * 3, cy - ty * 3, cx + tx * 3, cy + ty * 3),
                           fill=rgba(P["metal"], 120), width=1)

            # Traverse ogni 0,75 m.
            for cx, cy, _, _, snx, sny in iter_samples(a, b, 12):
                d.line((cx - snx * 22, cy - sny * 22,
                        cx + snx * 22, cy + sny * 22),
                       fill=rgba(P["brown"], 220), width=3)

            # Due rotaie (scartamento 1,435 m) con anima scura e luce metallica.
            for offset in (-11.5, 11.5):
                ra, rb = shifted(a, b, nx, ny, offset)
                d.line((ra, rb), fill=rgba(RAIL_DARK, 255), width=3)
                hi = offset - 1 if offset > 0 else offset + 1
                ha, hb = shifted(a, b, nx, ny, hi)
                d.line((ha, hb), fill=rgba(P["metal_light"], 210), width=1)
                for dist in range(24, int(length) - 8, 48):
                    p0 = (ha[0] + tx * dist, ha[1] + ty * dist)
                    p1 = (ha[0] + tx * (dist + 8), ha[1] + ty * (dist + 8))
                    d.line((p0, p1), fill=rgba(P["white"], 110), width=1)


def draw_barriers(img, sx, sy):
    d = ImageDraw.Draw(img, "RGBA")
    for barrier in W["barriers"]:
        pts = barrier["points"]
        if len(pts) < 2 or (sx, sy) not in affected(pts, pad_m=2):
            continue
        local = [to_local(p, sx, sy) for p in pts]
        wall = barrier.get("kind") == "retaining_wall"
        for i in range(len(local) - 1):
            a, b = local[i], local[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length < 0.001:
                continue
            tx, ty = dx / length, dy / length
            nx, ny = -ty, tx

            if wall:
                d.line((a, b), fill=rgba(P["ink_soft"], 140), width=10)
                d.line((a, b), fill=rgba(P["concrete"], 255), width=8)
                for cx, cy, _, _, wnx, wny in iter_samples(a, b, 16,
                                                           include_start=False):
                    d.line((cx - wnx * 4, cy - wny * 4,
                            cx + wnx * 4, cy + wny * 4),
                           fill=rgba(P["ink"], 65), width=1)
                cap_a, cap_b = shifted(a, b, nx, ny, -2)
                d.line((cap_a, cap_b), fill=rgba(P["concrete_light"], 120), width=1)
                continue

            # Recinzione: due correnti orizzontali e montanti ogni 1,5 m.
            posts = list(iter_samples(a, b, 24))
            for offset in (-3, 3):
                for p, q in zip(posts, posts[1:]):
                    pa, qa = shifted(p, q, nx, ny, offset)
                    d.line((ipair(pa), ipair(qa)),
                           fill=rgba(P["metal"], 205), width=1)
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
    draw_footways(img, ox, oy)
    tactile_sources = collect_tactile_sources(ox, oy)
    draw_sidewalk_bases(img, ox, oy)
    draw_sidewalk_details(img, ox, oy, tactile_sources)
    draw_carriageways(img, ox, oy)
    draw_crossings(img, ox, oy)
    draw_rails(img, ox, oy)
    draw_platforms(img, ox, oy)
    draw_building_contact(img, ox, oy)
    draw_barriers(img, ox, oy)
    return img


def draw_carriageways(img, sx, sy):
    d = ImageDraw.Draw(img, "RGBA")
    for road in W["roads"]:
        kind = road["kind"]
        if kind not in CARRIAGEWAYS:
            continue
        pts = road["points"]
        if len(pts) < 2 or (sx, sy) not in affected(pts, pad_m=6):
            continue
        local = [to_local(p, sx, sy) for p in pts]
        draw_carriageway(d, road, local, sx, sy)


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
