# ART_SPEC.md — specifica grafica vincolante per la 0.3.0

Questo documento è il contratto tra generatore degli asset e motore di gioco.
Ogni asset deve rispettarlo. Se un asset non rispetta la specifica, è difetto e va rigenerato.

## 1. Proiezione

**Proiezione 2D a tre quarti tipo Stardew Valley (obliqua a "cabinet"), NON isometrica.**

- Il terreno è una griglia **quadrata** allineata agli assi: 1 metro = 16 pixel.
- Unsettore di terreno copre 64 × 64 m = **1024 × 1024 px**, generato direttamente a 16 px/m.
  Il motore NON deve scalare i settori (`engine_scale = 1`). La scala 2x della 0.2.0 è stata eliminata:
  era la causa principale dei pixel doppi e delle linee "a blocchi".
- I personaggi e gli oggetti sono sprite eretti con origine ai piedi; non vengono ruotati.
- Gli edifici usano una proiezione obliqua con asse di profondità a 45° e scala 0,5:
  - parete sud (fronte): rettangolo di larghezza `W = larghezza_m · 16`, altezza `H = piani · 46 px`;
  - parete est (lato): parallelogramma che arretra di `D · 8` pixel verso destra e verso l'alto
    (`D = profondità_m`);
  - tetto: parallelogramma compatibile con le due pareti, overhang di 2 px.
- Le geometrie OSM restano la **fonte** di posizione, larghezza e profondità, ma non vengono
  disegnate come poligoni piatti: la rappresentazione finale è architettonica, non cartografica.

## 2. Metriche uniformi (1 m = 16 px)

| Elemento | Dimensione sprite | Note |
|---|---|---|
| Personaggio | 16 × 32 px per frame | 1,0 × 2,0 m; 4 direzioni × 4 frame; piedi a y=30 |
| Automobile | 72 × 40 px | 4,5 × 2,5 m; vista 3/4 dall'alto, origine (36, 30) |
| Autobus | 112 × 44 px | 7,0 × 2,75 m |
| Scooter | 52 × 34 px | 3,25 × 2,1 m |
| Treno EAV | 576 × 56 px | 36 × 3,5 m; due casse; origine centro |
| Lampione | 24 × 76 px | 1,5 × 4,75 m |
| Panchina | 56 × 26 px | 3,5 × 1,6 m |
| Bidone | 20 × 26 px | 1,25 × 1,6 m |
| Albero | 64 × 88 px | chioma 4 m, tronco 1,5 m |
| Fioriera | 32 × 20 px | 2 × 1,25 m |
| Macchinetta EAV | 20 × 40 px | 1,25 × 2,5 m |
| Edificio residenziale | larghezza `W*16 + D*8 + 32`, altezza `H + D*8 + 24` | vedi §3 |

## 3. Edifici — regole di costruzione

1. Usare il **bbox** del perimetro OSM: `minx, maxx, miny, maxy`.
   `anchor_x = (minx+maxx)/2`, `anchor_y = maxy` (bordo sud, livello strada).
2. Il manifest deve contenere, oltre ad `anchor_x/anchor_y`, i campi
   `origin_x`, `origin_y` (frazioni 0..1) corrispondenti al punto di ancoraggio nell'immagine,
   e `wall_h_px`, `depth_px`, `width_px`. Il motore userà `setOrigin(origin_x, origin_y)`.
3. **Finestre**: griglia regolare, 12 × 16 px, passo orizzontale 38 px (2,4 m), passo verticale
   46 px (1 piano). Non si inventano posizioni casuali. L'ordine dei piani è dal basso verso l'alto:
   piano terra = porte/vetrine, primo piano = finestre, ecc.
4. **Porta**: sempre al livello strada, al centro della parete sud, 22 × 38 px, con gradino.
5. **Balconi**: solo ai piani superiori, allineati alle finestre, con ringhiera verticale e lastra.
6. **Tetto**: tegole in file regolari, colmo, comignoli; nessuna riga diagonale casuale.
   La stazione ha tetto piano in lamiera e pensilina metallica lato binari.
7. **Ombre**: vietate le ombre poligonali dure e sfalsate della 0.2.0. Solo ombra di contatto
   morbida, raggio ≤ 1 m, alpha ≤ 45, centrata sotto la parete sud.
8. Stile: intonaco napoletano (crema, ocra, rosa), tetti in cotto, persiane verdi o legno,
   condizionatori e antenne solo in posizioni coerenti con la griglia.

## 4. Suolo

- Nessuna scala applicata dal motore.
- Asfalto con texture fine e giunti regolari; marciapiedi larghi 3 mx 3 px per lato con cordolo;
  strisce pedonali solo dove `highway=crossing`; **nessuna banda chiara al centro della strada**.
- Binari: massicciata, traverse ogni 0,75 m, due rotaie parallele con lucentezza metallica.
- Banchine: lastricato regolare con bordo giallo di sicurezza.
- Aree verdi: base erbosa con ciuffi sparsi in modo deterministico.
- Recinzioni: montanti ogni 1,5 m, non linee continue piatte.

## 5. Profondità e ordinamento

- Edifici: `depth = anchor_y · 16 + 1` (bordo sud).
- Personaggi/NPC/veicoli/arredi: `depth = y_px` del piede.
- Il giocatore passa davanti a un edificio se la sua y è maggiore del bordo sud, dietro altrimenti.
- Overlay notturno e luci: depth 900/950; hint contestuali: 10000.
- Vietato l'uso di `setRotation` su sprite visti di lato (treno): il treno va ruotato solo come
  sprite vista dall'alto, o mantenuto asse-aligned se la tratta è sostanzialmente est-ovest.

## 6. Palette

Ristretta e coerente, definita in `artlib.py`. Niente anti-aliasing, niente gradienti morbidi,
nessun colore fuori palette se non varianti di luminosità calcolate da `shade()`.

## 7. Verifica

Ogni generatore deve essere deterministico (seed da chiave stabile) e deve aggiornare il proprio
manifest. `tools/validate_world.py` deve essere esteso ai nuovi vincoli.
I difetti noti della 0.2.0 da NON reintroducere:
- finestre del piano Terra disegnate al tetto;
- ombra nera sfalsata di 5 px sotto ogni edificio;
- suolo a 8 px/m scalato 2x dal motore;
- sprite personaggio 24×36 px;
- linee stradali con joint arrotondato e banda centrale chiara;
- edifici ancorati 22 px più a nord del perimetro reale.
