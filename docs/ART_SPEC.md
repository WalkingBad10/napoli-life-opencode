# ART_SPEC.md — standard dimensionale definitivo e vincolante (v0.6.0)

Questo documento è il contratto tra generatori di asset e motore di gioco.
Ogni asset deve rispettarlo; se non lo rispetta è un difetto e va rigenerato.
La 0.6.0 **espande l'area** a un rettangolo giocabile `x ∈ [-256, 704]`,
`y ∈ [-320, 704]` m (960 × 1024 m) senza cambiare la metrica: 240 settori da 64 m.
La geometria OSM resta l'unica fonte di posizioni e perimetri; l'interpretazione
artistica è originale e generata dal codice in `tools/`.

## 1. Metrica e proiezione (obbligatorie per ogni mappa futura)

- **Proiezione obliqua a tre quarti** ("cabinet", come logica prospettica di Stardew Valley),
  **non isometrica**. Nessun asset di un altro gioco viene copiato.
- Metrica universale: **1 m = 16 px** nel mondo; **48 px/m** negli interni;
  `engine_scale = 1`; griglia quadrata allineata agli assi.
  Un settore copre 64×64 m = **1024×1024 px** (240 settori nella 0.6.0).
- Personaggi e arredi sono sprite eretti, con origine ai piedi e **nessuna rotazione**
  (incluso il treno, asse-aligned). Il motore non applica alcuna scala.
- Edifici: parete sud rettangolare (`W = larghezza_m × 16`, `H = piani × 46 px`),
  parete est parallelogramma che arretra di `D × 8` px verso destra e verso l'alto,
  tetto compatibile con overhang di 2 px. Il footprint OSM non viene dipinto come poligono piatto.
- Le coordinate di ancoraggio del manifest (`anchor_x`, `anchor_y`) e le frazioni
  `origin_x`, `origin_y` sono obbligatorie: il motore usa `setOrigin(origin_x, origin_y)`.
- Niente ombre nere dure: solo contatto leggero e alpha basso, come specificato al punto 3.

## 2. Tabella dimensionale definitiva

| Elemento | Dimensione | Metrica | Note |
|---|---|---|---|
| Personaggio | 16×32 px/frame | 1,0×2,0 m | 4 direzioni × 4 frame, sheet 64×128, piedi ancorati a y=30 |
| Automobile | 72×40 px | 4,5×2,5 m | origine (36, 30); `car_red`, `car_silver`, `car_blue` |
| Motocicletta | 52×34 px | 3,25×2,1 m | origine (26, 30); `motorcycle` |
| Autobus | 112×44 px | 7,0×2,75 m | origine (56, 34) |
| Scooter | 52×34 px | 3,25×2,1 m | origine ai piedi |
| Treno EAV | 576×56 px | 36×3,5 m | due casse, pantografo, nessuna rotazione |
| Lampione | 24×76 px | 1,5×4,75 m | origine ai piedi |
| Panchina | 56×26 px | 3,5×1,6 m | origine ai piedi |
| Bidone | 20×26 px | 1,25×1,6 m | origine ai piedi |
| Albero | 64×88 px | chioma 4 m, tronco 1,5 m | origine ai piedi |
| Fioriera | 32×20 px | 2×1,25 m | origine ai piedi |
| Macchinetta EAV | 20×40 px | 1,25×2,5 m | origine ai piedi |
| Pizza al taglio | 24×20 px | 1,5×1,25 m | prop da banco |
| Tazzina caffè | 12×14 px | 0,75×0,875 m | prop da banco |
| Libreria | 48×64 px | 1×1,33 m | arredo interno (48 px/m) |
| Pianta in vaso | 24×48 px | 0,5×1 m | arredo interno (48 px/m) |
| Interni | 576×384 px | 12×8 m | 48 px/m; **undici** stanze |
| Marciapiede | 24 px (1,5 m) | 1,5 m | strade minori; 32 px (2 m) su tertiary/secondary e superiori |
| Finestre | 12×16 px | 0,75×1 m | passo 38×46 px |
| Porta | 22×38 px | 1,375×2,375 m | livello strada |
| Piano | 46 px | 2,875 m | multiplo obbligatorio per `wall_h_px` |
| Traverse ferroviarie | ogni 12 px | 0,75 m | — |

Prop 0.6 aggiunti (dimensioni dal manifest, origine ai piedi): `shirt` 24×26 px,
`gift` 24×24 px, `heart` 20×18 px, `newspaper` 24×18 px,
`shopping_basket` 28×22 px, `toolbox` 30×20 px, `tabacco_sign` 32×24 px.

## 3. Edifici e facciate

1. Usare il **bbox OSM**: `anchor_x = (minx+maxx)/2`, `anchor_y = maxy`. Nessun edificio inventato. Nella 0.6.0 gli edifici sono **829**, tutti con ID OSM reale.
2. Il manifest deve contenere `origin_x`, `origin_y`, `wall_h_px`, `width_px`, `depth_px`.
   Aggiungere `windows`: coppie `[centro-x locale, top-y locale]` delle finestre dei piani superiori.
   Il motore disegna le luci notturne **solo** su queste coordinate: niente griglia approssimata.
3. Finestre incassate con cornice in pietra, cassonetto, davanzale, telai e riflessi obliqui;
   persiane a listelli nelle case, serranda nei negozi, vetrate blu alla stazione.
4. Portale napoletano: cornice a gradoni, transom, ante con pannelli, maniglie ottonate,
   targhetta civico e gradino in pietra. Le porte interattive restano ancorate ai POI convertiti.
5. **Varianti deterministiche**: un RNG separato con chiave
   `seeded("facade-detail:" + id)` non consuma quello che decide finestre/porta/tetto.
   Palazzi con pilastri e frontoni/archetti, case con persiane e balconi in ferro battuto
   differenti, botteghe con serrande e insegne, gronde, pluviali, condizionatori,
   terrazze con bucato e serbatoi. Ogni variante resta ancorata al passo 38×46 px.
6. Balconi solo ai piani superiori; marcapiani e plinti seguono il passo verticale di 46 px.
7. Tetti: tegole in file regolari, comignoli e antenne ancorati al colmo; terrazze piane con
   parapetto, botole, serbatoio e bucato solo dove la larghezza lo consente.
8. Insegne commerciali derivano da tag/nome OSM o da categoria generica; mai nomi inventati
   attribuiti a un edificio specifico. `POI.opening_hours` viene esportato solo se presente in OSM.
   L'unica eccezione dichiarata è "Scommesse d'oro", POI fittizio con orario esplicito nei dati.
9. Stazione (`way/503291719`): **due piani** (`wall_h_px = 92`), tetto piano con aggetto
   sull'ingresso, insegna `PIANURA` e targa `DON GIUSTINO RUSSOLILLO`.
   **Nessuna pensilina lato binari**: OSM riporta `shelter=no` su entrambe le banchine.
   I due pannelli murali sono illustrazioni originali, non copie.
10. Ombre: solo contatto leggero centrato sotto la parete sud, raggio ≤ 1 m, alpha ≤ 45.
    Vietate le ombre poligonali sfalsate e le ombre nere dure della 0.2.0.
11. Due edifici OSM reali (`way/677094968`, `way/1354461724`) distano meno di 8 m dai binari:
    vanno mantenuti per fedeltà ai dati, non rimossi né riposizionati.

## 4. Suolo, strade e ferrovia

- Il dump grezzo copre way intere che attraversano la bbox Overpass (circa
  `x = -2166 … 1848`, `y = -1591 … 2021` m); la conversione seleziona gli elementi nel
  rettangolo giocabile più 48 m di contesto e i settori sono disegnati dentro i bounds.
- Nessuna scala nel motore; asfalto con texture fine su griglia, giunti ogni 2 m,
  rattoppi regolari e tombini; nessuna banda chiara continua al centro.
- Linea centrale **tratteggiata sottile (2 px)** solo su secondary/primary/tertiary;
  mai su residential o service.
- Marciapiedi con cordolo chiaro, lastricato regolare e giunti ogni 1 m; piastrelle tattili
  presso banchine e `highway=crossing`; zebrature solo dove OSM riporta `crossing`.
- Elementi viari: **389 way stradali OSM + 21 nodi OSM** (18 bus_stop, 2 stop,
  1 traffic_signals) = 410 record. I nodi restano puntuali, senza tracciati inventati.
- Binari: 14 way Circumflegrea (11 `railway=rail` + 3 `railway=construction`) + 2 banchine; `rail_route` usa **12 way OSM complete**
  con operator EAV e geometria integrale. Connessioni solo dove i dati OSM le definiscono:
  nessun tracciato inventato. Massicciata ordinata, traverse ogni 0,75 m, rotaie con anima
  scura e luce metallica, drenaggio laterale. Banchine con bordo giallo tattile.
- Recinzioni con montanti ogni 1,5 m e due correnti orizzontali; muri di sostegno a blocchi.
- Aree verdi con ciuffi su griglia sfalsata e seed stabile; alberi restano sprite a parte.
- Nessun parcheggio è mappato nel contesto: l'elenco resta vuoto, non viene inventato.

## 5. Sprite, interni e illuminazione

- **42 sprite** (31 chiavi storiche invariate + 11 nuove: `car_blue`, `motorcycle`,
  `shopkeeper`, `mechanic`, `shirt`, `gift`, `heart`, `newspaper`, `shopping_basket`,
  `toolbox`, `tabacco_sign`); personaggi a 16×32 px/frame, sheet 64×128, piedi y=30.
  Manifest `version = "0.6.0"`, `pixel_per_metro = 16`.
- Alpha solo `0 / 44 / 255`; contorni a 1 px non cancellano l'ombra semitrasparente.
- Interni: **undici** PNG 576×384 a 48 px/m, `version = "0.6.0"`. ID, `kind`, porte e spawn
  storici invariati; sei stanze nuove: `supermarket`, `tobacco`, `bookmaker`, `bakery`,
  `clothing`, `workshop`, con porte ancorate ai rispettivi POI. Il `bookmaker` corrisponde
  alle Scommesse d'oro fittizie e dichiara esplicitamente la finzione nell'interazione.
  Il bar resta un bar napoletano riconoscibile; stazione con tabellone e tornelli;
  negozio con frigo e cassette; casa con letto, armadio `furnish` e spazio per arredi acquistati.
- Audio: **20 WAV originali** a 22050 Hz (`engine`, `scooter`, `traffic`, `market`,
  `relationship`, `shop_bell` aggiunti nella 0.6.0); manifest `version = "0.6.0"`.
- Illuminazione notturna: overlay e luci alle finestre reali del manifest; il piano terra resta buio.
  Profondità: edifici `anchor_y*16+1`, piedi `y*16`, arredi casa 220, overlay 900/950, hint 10000.

## 6. Palette, determinismo e QA

- Palette ristretta in `tools/artlib.py`; solo varianti di luminosità via `shade()`/`S()`.
- Vietati anti-aliasing, sfocature, gradienti morbidi, texture casuali e pixel decorativi
  senza funzione strutturale. Ogni dettaglio deve avere una ragione architettonica o narrativa.
- Tutti i generatori sono deterministici (seed da chiave stabile) e rigenerano il manifest.
- QA obbligatoria prima del rilascio: `tools/validate_world.py` (**70/70**),
  `npm run build` (`tsc --noEmit` + Vite OK), test end-to-end (**64/64** su Chrome headless
  in emulazione), `tools/visual_qa.py` (**85/85**), 13 screenshot reali in `screenshots/`.
  Non sono stati eseguiti test su dispositivi fisici né build di app native.
- Compatibilità: renderer Canvas 2D, browser desktop e mobile; nessuna dipendenza da API esterne
  durante il gameplay. Attribution: © OpenStreetMap contributors (ODbL 1.0), con operatore
  EAV / Ente Autonomo Volturno sui dati ferroviari.
- Rigenerazione (comandi esatti):

  ```bash
  python tools/fetch_osm_expanded.py  # solo per un nuovo dump OSM (richiede rete)
  python tools/convert_osm.py
  python tools/render_reference.py
  python tools/generate_world_tiles.py
  python tools/generate_buildings.py
  python tools/generate_sprites.py
  python tools/generate_interiors.py
  python tools/generate_audio.py
  python tools/validate_world.py
  python tools/visual_qa.py
  ```

  Su **PowerShell**, se `npm run build` dà problemi, usare
  `node node_modules/vite/bin/vite.js build` per il passaggio Vite.
- Difetti della 0.2.0 da non reintrodurre: finestre al tetto, ombra nera sfalsata, suolo a
  8 px/m scalato 2x, personaggi 24×36, linee con joint arrotondato, edifici spostati di 22 px.
