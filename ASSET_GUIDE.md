# ASSET_GUIDE.md — standard grafici e proporzioni

## Standard dimensionale

- Mondo: **1 metro = 16 pixel**. Griglia indicativa 16 × 16 px; 1 tile = 1 m.
- Interni: **48 px/m** per maggiore dettaglio in stanze da 8–12 m.
- Settori suolo: 64 × 64 m disegnati a 8 px/m (512 × 512 px) e scalati 2× nel motore con filtro nearest-neighbor.
- Pixel art: nessun anti-aliasing, colori informativi, ombre con alpha, `pixelArt: true`.

## Proporzioni verificate

| Elemento | Dimensione reale | Pixel | Sprite |
|---|---|---|---|
| Personaggio | 1,7 m alto, spalle ~0,45 m | 24 × 36 px/frame | `public/assets/sprites/*.png` (4 direzioni × 4 frame) |
| Automobile | 4,5 × 2,5 m | 72 × 40 px | `car_red`, `car_silver` |
| Scooter | 3,25 × 2,1 m | 52 × 34 px | `scooter` |
| Treno EAV | 35,5 m (2 casse) × ~3,5 m | 568 × 68 px | `train_eav.png` |
| Lampione | ~4,7 m | 28 × 76 px | `lamp.png` |
| Fabbricato viaggiatori | 57,6 × 15,2 m (perimetro OSM reale) | ~920 × 240 px | `b_way_503291719.png` |
| Piano interno | 12 × 8 m | 576 × 384 px | `public/assets/interiors/*.png` |

## Profondità

- Ogni sprite ha origine ai piedi (`setOrigin(0.5, 0.94)` per i personaggi, `(0.5, 1)` per gli edifici).
- `depth = y_pixel` del punto di contatto con il terreno: il giocatore passa davanti o dietro gli edifici in base alla posizione reale.
- Il suolo è a `depth = -1000`, i livelli notturni a 900/950, gli hint contestuali a 10000.

## Palette

Naturali e mediterranee: intonaci crema/ocra/rosa, tetti in cotto, asfalto grigio caldo,
verde mediterraneo, blu EAV `#1f4e79`, oro `#e2b83c`. Nessun asset copiato da altro gioco.

## Rigenerazione

```bash
python tools/generate_world_tiles.py
python tools/generate_buildings.py
python tools/generate_sprites.py
python tools/generate_interiors.py
python tools/generate_audio.py
python tools/validate_world.py
```

Ogni edificio viene generato dal proprio perimetro OSM: facciate sud, tetti, persiane,
balconi, condizionatori, antenne, panni stesi e insegne. Il fabbricato viaggiatori ha un
trattamento dedicato con insegna EAV. Non sostituire edifici con rettangoli piatti.
