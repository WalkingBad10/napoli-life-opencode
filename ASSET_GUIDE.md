# ASSET_GUIDE.md — standard grafici e proporzioni (v0.6.0)

Il contratto completo è `docs/ART_SPEC.md`. Questa pagina è il riepilogo operativo.

La v0.6.0 **non cambia la metrica**: 1 m = 16 px nel mondo, 48 px/m negli interni,
`engine_scale = 1`, stessa proiezione obliqua a tre quarti. Cambia l'estensione: area
rettangolare `x ∈ [-256, 704]`, `y ∈ [-320, 704]` m (960 × 1024 m) con **240 settori**
da 64 × 64 m, generati direttamente a 16 px/m. Nessun asset copiato da altri giochi.

Novità asset della 0.6: 829 sprite edificio da geometria OSM, 42 sprite (11 nuovi),
11 interni (6 nuove stanze), 20 file audio originali (6 nuovi). Manifest di tile, sprite,
interni e audio con `version = "0.6.0"`; il manifest edifici è l'elenco dei 829 record
rigenerati con ID OSM e metadata aggiornati.

## Standard dimensionale

- Mondo: **1 metro = 16 pixel**. Griglia quadrata allineata agli assi, non isometrica.
- Interni: **48 px/m** in stanze da 12 × 8 m (576 × 384 px).
- Settori suolo: 64 × 64 m generati direttamente a **16 px/m** → **1024 × 1024 px**.
  Il motore applica `engine_scale = 1`: nessun raddoppio dei pixel.
- Proiezione: **obliqua a tre quarti tipo Stardew Valley / cabinet**, con asse di profondità a 45°
  e scala 0,5. Nessun sprite viene ruotato, incluso il treno EAV.
- Pixel art: nessun anti-aliasing, palette ristretta, ombre di contatto minime e **nessuna ombra nera dura**, `pixelArt: true`.
- Font bitmap 3×5 generato dal codice per insegne e targhe: nessuna dipendenza da font di sistema.

## Proporzioni verificate

| Elemento | Dimensione reale | Pixel | Sprite |
|---|---|---|---|
| Personaggio | 1,0 × 2,0 m | 16 × 32 px/frame | sheet 64 × 128 px, 4 direzioni × 4 frame, piedi a y=30 |
| Automobile | 4,5 × 2,5 m | 72 × 40 px | `car_red`, `car_silver`, `car_blue` |
| Motocicletta | 3,25 × 2,1 m | 52 × 34 px | `motorcycle` |
| Autobus | 7,0 × 2,75 m | 112 × 44 px | `bus` |
| Scooter | 3,25 × 2,1 m | 52 × 34 px | `scooter` |
| Treno EAV | 36,0 m (2 casse) × 3,5 m | 576 × 56 px | `train_eav.png` |
| Lampione | 1,5 × 4,75 m | 24 × 76 px | `lamp.png` |
| Panchina | 3,5 × 1,6 m | 56 × 26 px | `bench.png` |
| Albero | chioma 4 m | 64 × 88 px | `tree.png` |
| Macchinetta EAV | 1,25 × 2,5 m | 20 × 40 px | `ticket_machine.png` |
| Fabbricato viaggiatori | 57,6 × 15,2 m (bbox OSM reale) | facciata 921 px, 2 piani | `b_way_503291719.png` (1061 × 228 px) |
| Piano interno | 12 × 8 m | 576 × 384 px | `public/assets/interiors/*.png` |

Nuovi prop 0.6 (dimensioni lette dal manifest, origine ai piedi): `shirt` 24 × 26 px,
`gift` 24 × 24 px, `heart` 20 × 18 px, `newspaper` 24 × 18 px,
`shopping_basket` 28 × 22 px, `toolbox` 30 × 20 px, `tabacco_sign` 32 × 24 px.
Nuovi personaggi `shopkeeper` e `mechanic` usano lo stesso sheet 64 × 128 px,
16 × 32 px/frame, piedi a y=30.

## Edifici

Ogni sprite nasce dal **bbox OSM**, non da un poligono piatto dipinto come facciata. Nella 0.6.0 sono **829 edifici**, tutti con ID OSM reale:

- parete sud rettangolare, larghezza `metri × 16`, altezza `piani × 46`;
- parete est in proiezione cabinet, arretrata di `profondità_m × 8` px;
- tetto architettonico (tegole regolari e colmo; terrazze con bucato sui tetti piani);
- finestre 12 × 16 px su griglia 38 × 46 px, piano terra in basso;
- porta centrale 22 × 38 px al livello strada, balconi solo ai piani superiori;
- manifest con `origin_x/origin_y` calcolati dal centro del bordo sud e `windows`
  (centro-x, top-y delle finestre superiori) per le luci notturne reali,
  oltre a `wall_h_px`, `width_px` e `depth_px`.

Due edifici OSM reali (`way/677094968`, `way/1354461724`) sono entro 8 m dai binari e restano
al loro posto per fedeltà ai dati: non sono stati spostati o sostituiti.

## Interni

Undici PNG 576 × 384 a 48 px/m: i cinque storici (`station`, `bar`, `shop`, `home`, `pizzeria`)
più `supermarket`, `tobacco`, `bookmaker`, `bakery`, `clothing`, `workshop`.
Le porte sono ancorate a POI OSM reali (spawn nel manifest), con l'eccezione dichiarata del
`bookmaker`, che corrisponde alle Scommesse d'oro fittizie e riporta l'interazione
"Attivita fittizia". Anche il tabaccaio usa POI OSM reali; nessuna stanza è stata inventata
senza un ancoraggio.

## Audio

Venti WAV originali a 22050 Hz generati da `tools/generate_audio.py`: ai quattordici storici
si aggiungono `engine`, `scooter`, `traffic`, `market`, `relationship`, `shop_bell`.
Nessun file audio preso da altri giochi.

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
python tools/fetch_osm_expanded.py  # solo se si vuole un nuovo dump OSM (richiede rete)
python tools/convert_osm.py         # aggiorna data/world/ e public/data/world/
python tools/render_reference.py
python tools/generate_world_tiles.py
python tools/generate_buildings.py
python tools/generate_sprites.py
python tools/generate_interiors.py
python tools/generate_audio.py
python tools/validate_world.py
python tools/visual_qa.py
```

Oppure `npm run assets` per la sola catena degli asset (senza rete). I generatori sono
deterministici (seed da chiave OSM/stabile): rieseguirli produce file identici.
Build e verifiche:

```bash
npm run build          # tsc --noEmit && vite build
npm run test:e2e       # Playwright + screenshot in screenshots/
python tools/validate_world.py
```

Su **PowerShell**, se `npm run build` dà problemi, usare `node node_modules/vite/bin/vite.js build`
per il passaggio Vite. Non riportare test su dispositivi fisici o pubblicazioni non eseguite.

La stazione riceve un trattamento dedicato: due piani, tetto piano con aggetto, vetrate,
colonne, insegna "PIANURA", targa "DON GIUSTINO RUSSOLILLO" e due murales originali.
**Nessuna pensilina**: OSM riporta `shelter=no` su entrambe le banchine. Vedere
`docs/reference/station_research.md` per fonti e gradi di certezza.
Non sostituire edifici con rettangoli piatti.
