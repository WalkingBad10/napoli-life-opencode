# ART_SPEC.md — specifica grafica vincolante per la 0.4.0

Questo documento è il contratto tra generatori di asset e motore di gioco.
Ogni asset deve rispettarlo; se non lo rispetta è un difetto e va rigenerato.
La 0.4.0 non amplia la mappa: rifinisce Pianura. La geometria OSM resta la fonte
di ogni posizione e dimensione; l'interpretazione artistica è originale e generata
dal codice in `tools/`.

## 1. Proiezione e metrica

- **Proiezione obliqua a tre quarti** ("cabinet", come logica prospettica di Stardew Valley),
  **non isometrica**. Nessun asset di un altro gioco viene copiato.
- Metrica universale: **1 m = 16 px** nel mondo; **48 px/m** negli interni;
  `engine_scale = 1`. Un settore copre 64×64 m = **1024×1024 px**.
- Griglia quadrata allineata agli assi. I personaggi e gli arredi sono sprite eretti,
  con origine ai piedi e **nessuna rotazione** (incluso il treno, asse-aligned).
- Edifici: parete sud rettangolare (`W = larghezza_m × 16`, `H = piani × 46 px`),
  parete est parallelogramma che arretra di `D × 8` px verso destra e verso l'alto,
  tetto compatibile con overhang di 2 px. Il footprint OSM non viene dipinto come poligono piatto.
- Le coordinate di ancoraggio del manifest (`anchor_x`, `anchor_y`) e le frazioni
  `origin_x`, `origin_y` sono obbligatori: il motore usa `setOrigin(origin_x, origin_y)`.

## 2. Dimensioni

| Elemento | Dimensione | Note |
|---|---|---|
| Personaggio | 16×32 px/frame | 1,0×2,0 m; 4 direzioni × 4 frame; piedi ancorati a y=30 |
| Automobile | 72×40 px | 4,5×2,5 m; origine (36, 30) |
| Autobus | 112×44 px | 7,0×2,75 m |
| Scooter | 52×34 px | 3,25×2,1 m |
| Treno EAV | 576×56 px | 36×3,5 m, due casse, pantografo; nessuna rotazione |
| Lampione | 24×76 px | 1,5×4,75 m |
| Panchina | 56×26 px | 3,5×1,6 m |
| Bidone | 20×26 px | 1,25×1,6 m |
| Albero | 64×88 px | chioma 4 m, tronco 1,5 m |
| Fioriera | 32×20 px | 2×1,25 m |
| Macchinetta EAV | 20×40 px | 1,25×2,5 m |
| Interni | 576×384 px | 48 px/m; quattro stanze |
| Marciapiede | 24 px (1,5 m) | strade minori; 32 px (2 m) su tertiary/secondary e superiori |
| Finestre | 12×16 px | passo 38×46 px |
| Porta | 22×38 px | livello strada |
| Traverse ferroviarie | ogni 12 px | 0,75 m |

## 3. Edifici e facciate

1. Usare il **bbox OSM**: `anchor_x = (minx+maxx)/2`, `anchor_y = maxy`. Nessun edificio inventato.
2. Il manifest deve contenere `origin_x`, `origin_y`, `wall_h_px`, `width_px`, `depth_px`.
   Aggiungere `windows`: coppie `[centro-x locale, top-y locale]` delle finestre dei piani superiori.
   Il motore disegna le luci notturne **solo** su queste coordinate: niente griglia approssimata.
3. Finestre incassate con cornice in pietra, cassonetto, davanzale, telai e riflessi obliqui;
   persiane a listelli nelle case, serranda nei negozi, vetrate blu alla stazione.
4. Portale napoletano: cornice a gradoni, transom a tre riquadri, ante con pannelli,
   maniglie ottonate, targhetta civico e gradino in pietra.
5. Balconi solo ai piani superiori, con lastra, ringhiera in ferro, montanti e fiori.
   Marcapiani e plinti seguono il passo verticale di 46 px.
6. Tetti: tegole in file regolari, comignoli e antenne ancorati al colmo; terrazze piane con
   parapetto, botole, serbatoio dell'acqua e bucato solo dove la larghezza lo consente.
7. Insegne commerciali derivano da tag/nome OSM o da categoria generica; mai nomi inventati
   attribuiti a un edificio specifico.
8. Stazione (`way/503291719`): **due piani** (ipotesi dalla foto 2018 analizzata in locale),
   tetto piano con aggetto sull'ingresso, insegna "PIANURA" e targa "DON GIUSTINO RUSSOLILLO".
   **Nessuna pensilina lato binari**: OSM riporta `shelter=no` su entrambe le banchine.
   I due pannelli murali sono illustrazioni originali ispirate ai soggetti documentati, non copie.
   Vedere `docs/reference/station_research.md` per fonti, fatti verificati e ipotesi.
9. Ombre: solo contatto leggero centrato sotto la parete sud, raggio ≤ 1 m, alpha ≤ 45.
   Vietate le ombre poligonali sfalsate della 0.2.0.

## 4. Suolo, strade e ferrovia

- Nessuna scala nel motore; asfalto con texture fine su griglia, giunti ogni 2 m,
  rattoppi regolari e tombini; nessuna banda chiara continua al centro.
- Linea centrale **tratteggiata sottile (2 px)** solo su secondary/primary/tertiary;
  mai su residential o service.
- Marciapiedi con cordolo chiaro, lastricato regolare e giunti ogni 1 m; piastrelle tattili
  presso banchine e `highway=crossing`. La carreggiata OSM non viene modificata.
- Binari: massicciata ordinata, traverse ogni 0,75 m, rotaie con anima scura e luce metallica,
  drenaggio laterale. Banchine con pavimento regolare e bordo giallo di sicurezza tattile.
- Recinzioni con montanti ogni 1,5 m e due correnti orizzontali; muri di sostegno a blocchi.
- Aree verdi con ciuffi su griglia sfalsata e seed stabile; alberi restano sprite a parte.

## 5. Sprite, interni e illuminazione

- 26 sprite con nomi, dimensioni, origini e chiavi di manifest invariati rispetto alla 0.3.0;
  solo il campo `version` passa a `0.4.0`. Personaggi a 112 frame totali e accessori coerenti.
- Alpha solo `0 / 44 / 255`; contorni a 1 px non cancellano l'ombra semitrasparente.
- Interni: quattro PNG 576×384 a 48 px/m, con spawn e interazioni invariati.
  Il bar è un bar napoletano riconoscibile (bancone, espresso 3 gruppi, vetrina con
  sfogliatelle/babà/cannoli, menu, frigo, barista e clienti).
- Illuminazione notturna:overlay e luci alle finestre reali del manifest; il piano terra resta buio.
  Profondità: edifici `anchor_y*16+1`, piedi `y*16`, overlay 900/950, hint 10000.

## 6. Palette e qualità

- Palette ristretta in `tools/artlib.py`; solo varianti di luminosità via `shade()`/`S()`.
- Vietati anti-aliasing, sfocature, gradienti morbidi, texture casuali e pixel decorativi
  senza funzione strutturale. Ogni dettaglio deve avere una ragione architettonica o narrativa.
- Tutti i generatori sono deterministici (seed da chiave stabile) e rigenerano il manifest.
- QA obbligatoria prima del rilascio: `validate_world.py`, build, test end-to-end,
  `visual_qa.py`, analisi visiva locale con `tools/ollama_vision.py` sugli screenshot.
- Compatibilità: renderer Canvas 2D, browser desktop e mobile; nessuna dipendenza da API esterne
  durante il gameplay.
- Difetti della 0.2.0 da non reintrodurre: finestre al tetto, ombra nera sfalsata, suolo a
  8 px/m scalato 2x, personaggi 24×36, linee con joint arrotondato, edifici spostati di 22 px.
