# ASSET_GUIDE.md — standard grafici e proporzioni (v0.4.0)

Il contratto completo è `docs/ART_SPEC.md`. Questa pagina è il riepilogo operativo.
La v0.4.0 NON usa la scala 2× del suolo né sprite a 24 × 36 px e non amplia la mappa.

## Standard dimensionale

- Mondo: **1 metro = 16 pixel**. Griglia quadrata allineata agli assi, non isometrica.
- Interni: **48 px/m** in stanze da 12 × 8 m (576 × 384 px).
- Settori suolo: 64 × 64 m generati direttamente a **16 px/m** → **1024 × 1024 px**.
  Il motore applica `engine_scale = 1`: nessun raddoppio dei pixel.
- Proiezione: **obliqua a tre quarti tipo Stardew Valley / cabinet**, con asse di profondità a 45°
  e scala 0,5. Nessun sprite viene ruotato, incluso il treno EAV.
- Pixel art: nessun anti-aliasing, palette ristretta, ombre di contatto minime, `pixelArt: true`.
- Font bitmap 3×5 generato dal codice per insegne e targhe: nessuna dipendenza da font di sistema.

## Proporzioni verificate

| Elemento | Dimensione reale | Pixel | Sprite |
|---|---|---|---|
| Personaggio | 1,0 × 2,0 m | 16 × 32 px/frame | sheet 64 × 128 px, 4 direzioni × 4 frame, piedi a y=30 |
| Automobile | 4,5 × 2,5 m | 72 × 40 px | `car_red`, `car_silver` |
| Autobus | 7,0 × 2,75 m | 112 × 44 px | `bus` |
| Scooter | 3,25 × 2,1 m | 52 × 34 px | `scooter` |
| Treno EAV | 36,0 m (2 casse) × 3,5 m | 576 × 56 px | `train_eav.png` |
| Lampione | 1,5 × 4,75 m | 24 × 76 px | `lamp.png` |
| Panchina | 3,5 × 1,6 m | 56 × 26 px | `bench.png` |
| Albero | chioma 4 m | 64 × 88 px | `tree.png` |
| Macchinetta EAV | 1,25 × 2,5 m | 20 × 40 px | `ticket_machine.png` |
| Fabbricato viaggiatori | 57,6 × 15,2 m (bbox OSM reale) | facciata 921 px, 2 piani | `b_way_503291719.png` (1061 × 228 px) |
| Piano interno | 12 × 8 m | 576 × 384 px | `public/assets/interiors/*.png` |

## Edifici

Ogni sprite nasce dal **bbox OSM**, non da un poligono piatto dipinto come facciata:

- parete sud rettangolare, larghezza `metri × 16`, altezza `piani × 46`;
- parete est in proiezione cabinet, arretrata di `profondità_m × 8` px;
- tetto architettonico (tegole regolari e colmo; terrazze con bucato sui tetti piani);
- finestre 12 × 16 px su griglia 38 × 46 px, piano terra in basso;
- porta centrale 22 × 38 px al livello strada, balconi solo ai piani superiori;
- manifest con `origin_x/origin_y` calcolati dal centro del bordo sud e `windows`
  (centro-x, top-y delle finestre superiori) per le luci notturne reali.

## Profondità

- Personaggi/arredi/veicoli: `depth = y_pixel` del piede.
- Edifici: `depth = anchor_y × 16 + 1` (bordo sud). Il giocatore passa davanti se la sua y è maggiore.
- Suolo `-1000`, luci notturne `900`, overlay `950`, hint `10000`.
- Il treno è disegnato di lato e **non viene ruotato**; i veicoli visti dall'alto sì.

## Palette

Intonaci crema/ocra/rosa, tetti in cotto, asfalto grigio caldo, verde mediterraneo,
blu EAV `#1f4e79`, oro `#e2b83c`. Tutti i colori derivano da `tools/artlib.py`.
Nessun asset copiato da altri giochi.

## Rigenerazione

```bash
python tools/generate_world_tiles.py
python tools/generate_buildings.py
python tools/generate_sprites.py
python tools/generate_interiors.py
python tools/generate_audio.py
python tools/validate_world.py
```

I generatori sono deterministici (seed da chiave OSM/stabile): rieseguirli produce file identici.
La stazione riceve un trattamento dedicato: due piani, tetto piano con aggetto, vetrate,
colonne, insegna "PIANURA", targa "DON GIUSTINO RUSSOLILLO" e due murales originali.
**Nessuna pensilina**: OSM riporta `shelter=no` su entrambe le banchine. Vedere
`docs/reference/station_research.md` per fonti e gradi di certezza.
Non sostituire edifici con rettangoli piatti.
