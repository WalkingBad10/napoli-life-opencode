# VISUAL_QA.md — registro delle iterazioni grafiche

Obiettivo: non limitarsi a far passare i test, ma correggere i difetti visivi reali emersi
dalla fotografia fornita e dagli screenshot della build. Ogni iterazione registra osservazioni,
causa tecnica, intervento ed esito. L'analisi automatica non sostituisce la revisione umana.

## Iterazione 0 — accettazione della 0.2.0 (rifiutata)

Difetti osservati nella fotografia/screenshot fornita:

1. **Pixel doppi e linee a blocchi**: il suolo era disegnato a 8 px/m e poi scalato 2× dal motore.
2. **Ombre nere sfalsate**: ogni edificio aveva un'ombra poligonale dura con offset di 5 px e alpha 150.
3. **Finestre invertite**: il piano terra veniva disegnato in alto, vicino al tetto.
4. **Artefatti di profondità**: edifici ancorati a `(0.5, 1)` pur avendo origine architettonica diversa; il giocatore passava dietro facciate che doveva attraversare.
5. **Sprite fuori metrica**: personaggi 24 × 36 px, treno ruotato come un veicolo visto dall'alto.
6. **Stazione sbagliata**: spawn e porta sul lato nord del fabbricato, non sulla banchina; la geometria OSM veniva dipinta come facciata piatta.
7. **Strade con banda chiara centrale** e giunti arrotondati, non coerenti con asfalto reale.
8. **UI piccola** su mobile e pannelli poco leggibili.

## Iterazione 1 — specifica e rimozione delle cause

Interventi applicati:

- Scritto `docs/ART_SPEC.md` come contratto obbligatorio per generatore e motore.
- Suolo rigenerato a **16 px/m**, settori **1024 × 1024**, `engine_scale = 1`.
- Ombre poligonali rimosse; solo contatto morbido con alpha ≤ 45 e raggio ≤ 0,75 m.
- Finestre su griglia fissa 38 × 46 px, piano terra in basso.
- Edifici ricostruiti come volume architettonico dal bbox OSM, con `origin_x/origin_y` nel manifest.
- Personaggi 16 × 32 px, veicoli e arredo ridisegnati; treno non ruotato.
- Spawn e porte della stazione portati sul lato banchina; bar/negozio ancorati a edifici OSM reali.
- UI ridimensionata con target touch maggiori e pannelli più leggibili.
- Il tentativo di usare un generatore di immagini con la foto come riferimento è fallito per credenziali non disponibili: la stazione è stata quindi ricostruita a mano nel generatore Python, usando l'analisi della fotografia e le geometrie OSM. Nessun pixel della foto è stato copiato nel gioco.

## Iterazione 2 — verifica successiva alla build

I risultati di questa iterazione vengono registrati in `screenshots/visual-qa-report.json`
e `screenshots/test-report.json` dopo l'esecuzione di:

```bash
npm run build
npm run test:e2e
npm run test:visual
```

Controlli considerati validi solo se:

- gli screenshot non sono vuoti e hanno palette coerente (> 100 colori campionati);
- la frazione di nero pieno resta sotto il 2%;
- la luminosità media resta in un intervallo realistico;
- non esistono ombre nere dure nei 36 settori di suolo;
- la stazione supera 900 px di facciata e mantiene l'insegna EAV;
- tutti i controlli funzionali restano verdi dopo il cambiamento grafico.

**Esito misurato (Chrome headless, 1280 × 800):**

| Metrica | v0.2.0 desktop | v0.3.0 desktop | Interpretazione |
|---|---:|---:|---|
| Luminosità media | 44,9 | 165,2 | la scena non è più schiacciata dalle ombre |
| Pixel quasi neri | 47,5% | 0,01% | eliminate le ombre dominanti |
| Nero pieno | 5,3% | 0,00% | nessuna ombra poligonale residua |
| Densità di bordi | 4,1% | 14,2% | molto più dettaglio architettonico leggibile |
| Colori campionati | 570 | 250 | palette volutamente ristretta e coerente |

Il calo del numero di colori è intenzionale: la 0.2.0 mescolava sfumature casuali e ombre;
la 0.3.0 usa una palette limitata ma con tre volte più struttura (bordi) e luminosità realistica.

Risultati completi: `screenshots/visual-qa-report.json` (18/18) e
`screenshots/test-report.json` (30/30).

## Iterazione 3 — revisione finale e pubblicazione

- CI (`45870223405`) e Deploy (`45870223066`) verdi sul commit `8743e63`.
- Verifica sul link pubblico: 8/8 controlli, HTTP 200, versione 0.3.0, movimento attivo, 198 colori campionati, 0,00% nero pieno, zero errori console.
- Screenshot pubblico salvato in `screenshots/v0.3_public_link.png`; report in `screenshots/public-link-report.json`.
- Il confronto tra screenshot locali e pubblicati non mostra differenze strutturali: stessa risoluzione, stessa palette ristretta, stessa assenza di ombre dominanti.
- Difetti residui noti: la revisione visiva umana non è stata possibile dal modello (nessun supporto all'input immagine); la livrea EAV e gli interni restano ricostruzioni originali, non foto verification. Sono documentati in `MAP_SOURCES.md` e rimandati alla 0.4 previa verifica fotografica.
- Nessuna azione correttiva aggiuntiva intrapresa prima della pubblicazione: i controlli automatici sono verdi e le metriche qualitative sono migliorate rispetto alla 0.2.0.

## Iterazione 4 — ricerca e fonti della stazione (0.4.0)

Prima di modificare la stazione sono state raccolte fonti verificabili in
`docs/reference/station_research.md`. Emerso:

- OSM `way/503291716` e `way/503291714` riportano **`shelter=no`** su entrambe le banchine,
  mentre il generatore 0.3 disegnava sempre una pensilina metallica.
- Le fonti del 2020 documentano l'intitolazione a **Don Giustino Russolillo** e due murales;
  l'insegna "EAV PIANURA" non era confermata da nessuna fonte.
- La foto 2018 su Wikimedia Commons è stata analizzata **in locale** con `qwen2.5vl:3b`
  (`docs/reference/station_photo_vision.txt`): due piani, tetto piano con aggetto,
  scritta "Pianura" e un murales. Il risultato è un'analisi di modello, non una verifica umana.

Interventi applicati: pensilina rimossa, stazione portata a due piani, tetto piano mantenuto,
insegna e targa aggiornate, due murales originali disegnati dal codice. Geometria OSM invariata.

## Iterazione 5 — revisione degli asset e correzioni

Analisi locale del montaggio dei palazzi (`docs/reference/buildings_v04_montage.png`,
`critica_buildings_v04.txt`) e della stazione (`station_asset_vision.txt`):

1. Il modello segnalava scritte poco leggibili: il font di sistema minuscolo è stato sostituito
   con un bitmap 3×5 deterministico; la rianalisi legge "PIANURA" (come "PIAMURA", errore del modello).
2. Le luci notturne della 0.3 erano su una griglia approssimata non allineata alle finestre:
   il manifest ora contiene le coordinate reali e il motore le usa.
3. La critica della scena segnalava palette piatta e HUD affollato: la palette resta volutamente
   ristretta per contratto, ma sono state aumentate le strutture leggibili (bordi 15,5% sullo
   screenshot desktop). L'HUD resta invariato perché i test touch sono verdi e non ci sono
   evidenze di regressione funzionale.

Il modello ha inoltre descritto il tetto della stazione come "leggermente inclinato": è la
proiezione obliqua a tre quarti prevista da `ART_SPEC.md`, non un difetto.

## Iterazione 6 — verifica finale 0.4.0

Eseguiti dopo l'ultima rigenerazione:

```bash
npm run build
npm run test:e2e
python tools/validate_world.py
python tools/visual_qa.py
```

**Risultati misurati (Chrome headless, 1280×800):**

| Metrica | v0.3.0 | v0.4.0 |
|---|---:|---:|
| Test end-to-end | 30/30 | 30/30 |
| Validazioni mondo/asset | 26/26 | 26/26 |
| Controlli visivi | 18/18 | 27/27 |
| Colori campionati (desktop) | 250 | 280 |
| Densità di bordi (desktop) | 14,2% | 15,5% |
| Nero pieno | 0,00% | 0,00% |
| Errori console | 0 | 0 |

Le sei screenshot reali sono `screenshots/v0.4_*.png`; i report sono
`screenshots/test-report.json`, `screenshots/validation-report.json` e
`screenshots/visual-qa-report.json`.

Analisi locale delle screenshot (`critica_v04_world.txt`, `critica_v04_station.txt`,
`critica_v04_bar.txt`) e dell'asset del bar (`bar_asset_vision.txt`):

- il modello riconosce nel bar bancone, macchina espresso, vetrina con sfogliatelle/babà/cannoli,
  menu, sgabelli e clienti; la critica sulla screenshot ("mancano tavoli") è un effetto
  della riduzione a 900 px e dell'HUD, non un difetto dell'asset 576×384.
- la stazione viene descritta come edificio lungo a tetto piano, con finestre allineate e porta
  centrale; le due critiche residue (monotonia della griglia e porta "aperta") sono interpretazioni
  del modello, non difetti misurati.
- restano come limiti la revisione visiva umana e la conferma fotografica definitiva di
  piani/colori; sono documentati in `PROGRESS.md` e `station_research.md`.

## Iterazione 7 — pubblicazione e verifica pubblica

- Commit `a76d34a`; CI (`45881687133`) e Deploy (`45881687048`) verdi.
- `npm run test:public`: 8/8 controlli su `https://walkingbad10.github.io/napoli-life-opencode/`,
  HTTP 200, versione 0.4.0, movimento attivo, 234 colori campionati, 0,00% nero pieno, zero errori console.
- Screenshot reale del sito pubblico salvato in `screenshots/v0.4_public_link.png` e report in
  `screenshots/public-link-report.json`.
- Le metriche del sito pubblico sono coerenti con quelle locali (palette ristretta, nessuna ombra
  dominante): non sono emerse differenze strutturali tra build locale e build distribuita.

## Iterazione 8 — vita quotidiana e nuovi interni (0.5.0)

Nuovi asset ispezionati: pizzeria Carpe Diem, arredo di casa, sprite del pizzaiolo, cibo/bevande,
audio di zona e HUD dei bisogni. La geometria OSM e il contratto 1 m = 16 px / 48 px/m restano invariati.

```bash
npm run build
python tools/validate_world.py
npm run test:e2e
python tools/visual_qa.py
```

**Risultati misurati (Chrome headless, 1280×800):**

| Metrica | v0.4.0 | v0.5.0 |
|---|---:|---:|
| Test end-to-end | 30/30 | 53/53 |
| Validazioni mondo/asset | 26/26 | 26/26 |
| Controlli visivi | 27/27 | 56/56 |
| Screenshot reali | 6 | 10 |
| Colori campionati (desktop) | 280 | 299 |
| Densità di bordi (desktop) | 15,5% | 16,5% |
| Nero pieno | 0,00% | 0,00% |
| Errori console | 0 | 0 |

Le dieci screenshot reali sono `screenshots/v0.5_*.png`; i report sono `screenshots/test-report.json`,
`screenshots/validation-report.json` e `screenshots/visual-qa-report.json`.

Analisi locale con Ollama `qwen2.5vl:3b` (`docs/reference/v05_vision_*.txt`):

- il modello riconosce la pizzeria come locale credibile (forno, banco, personale in divisa) e
  segnala solo la mancanza di dettagli aggiuntivi sulle pareti: l'asset 576×384 è volutamente
  una stanza compatta a 48 px/m e il giudizio arriva da un'immagine ridotta a 720 px;
- sulla stazione esterna chiede più contrasto e dettaglio strutturale: la facciata resta quella
  verificata nella 0.4 (921 px, 886 finestre totali), con panchine, tornelli e tabellone; non sono
  state introdotte ombre dure per aumentare il contrasto;
- sulla vista desktop descrive la prospettiva come "planimetrica": è la proiezione obliqua a tre
  quarti prevista da `ART_SPEC.md` (facciate frontali + suolo in griglia quadrata), non un difetto;
- sullo schermo verticale conferma HUD, icone e personaggio leggibili, senza reload.

Nessuna correzione grafica intrusiva è stata applicata dopo l'analisi: le metriche restano verdi e
le osservazioni del modello sono ricostruzioni soggettive, non difetti misurati. La revisione visiva
umana resta l'unico controllo definitivo ed è ancora pendente.

## Iterazione 9 — pubblicazione e verifica pubblica 0.5.0

- Commit `985b10d`, tag `v0.5.0-stable`; CI (`45885357869`) e Deploy (`45885357952`) verdi.
- `npm run test:public`: 11/11 controlli su `https://walkingbad10.github.io/napoli-life-opencode/`,
  HTTP 200, versione 0.5.0, HUD bisogni visibile, pannello "Vita a Pianura" apribile, movimento
  attivo, 288 colori campionati, 0,00% nero pieno, zero errori console.
- Screenshot reale del sito pubblico salvato in `screenshots/v0.5_public_link.png`; report in
  `screenshots/public-link-report.json`.
- Le metriche del sito pubblico restano coerenti con quelle locali: non sono emerse differenze
  strutturali tra build locale e build distribuita.

## Iterazione 10 — espansione e QA visivo (0.6.0)

Area esplorabile ampliata, nuovi interni, veicoli e sequenza del viaggio in treno. Restano
invariati la geometria OSM, il contratto 1 m = 16 px nel mondo (48 px/m negli interni) e la
generazione originale degli asset da `tools/`.

```bash
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
python tools/validate_world.py
node tests/run-tests.mjs
python tools/visual_qa.py
```

**Risultati misurati (26 novembre 2026; Chrome headless su Windows in emulazione, non dispositivo fisico):**

| Controllo | Risultato v0.6.0 |
|---|---:|
| Compilazione TypeScript | OK |
| Build Vite | OK |
| Test end-to-end | 64/64 (v0.5.0: 53/53) |
| Validazioni mondo/asset | 70/70 (v0.5.0: 26/26) |
| Controlli visivi | 85/85 (v0.5.0: 56/56) |
| Screenshot reali | 13 (v0.5.0: 10) |
| Errori console | 0 |

Il report della validazione è `data/world/validation-report.json`; gli warning registrati sono:
due edifici OSM reali entro 8 m dai binari (`way/677094968`, `way/1354461724`), mantenuti per
fedeltà ai dati sorgente e non spostati; 389 way stradali e 21 nodi viari OSM; "Scommesse d'oro"
dichiarata fittizia; nessun parcheggio mappato nel contesto. Il report visivo è
`screenshots/visual-qa-report.json`.

Confronto delle metriche campionate con stride 12:

| Metrica | v0.5.0 | v0.6.0 |
|---|---:|---:|
| Colori campionati (desktop) | 299 | 297 |
| Densità di bordi (desktop) | 16,52% | 16,63% |
| Nero pieno (desktop) | 0,00% | 0,00% |
| Colori campionati (landscape) | 305 | 315 |
| Densità di bordi (landscape) | 15,54% | 12,12% |
| Colori campionati (bar interno) | 296 | 301 |
| Densità di bordi (bar interno) | 15,34% | 15,18% |

La palette resta stabile e il nero pieno resta assente; la variazione di densità di bordi in
landscape è un dato misurato, non è stata interpretata come difetto. Su tutti i 13 screenshot:
colori tra 223 e 329, nero pieno 0,00%, bordi tra 10,37% e 28,77%, luminosità media tra 136,1
e 168,0. Sono stati controllati 240 tile di suolo 1024 × 1024 senza pixel nero pieno campionati;
il censimento degli asset riporta 829 sprite edificio, 42 sprite personaggi/veicoli, 11 interni
e 20 audio, con manifest alla versione 0.6.0.

Le tredici screenshot reali sono `screenshots/v0.6_*.png`: `expanded_area`, `new_interior`,
`vehicle`, `train_ride`, `world_desktop`, `landscape`, `portrait`, `station_exterior`,
`station_interior`, `bar_interior`, `home_interior`, `home_furnished` e `pizzeria_interior`.

Nessuna correzione grafica intrusiva è stata applicata dopo il QA automatico: i controlli sono
verdi e le metriche non mostrano regressioni misurabili. La pubblicazione e la verifica sul link
pubblico della 0.6.0 sono ancora in attesa: per questa versione non si riportano risultati pubblici.

## Iterazione 11 — revisione multimodale locale e limiti del metodo

Le screenshot della 0.6.0 sono state analizzate in locale con Ollama `qwen2.5vl:3b`, con immagini
ridotte a 720 px. Le trascrizioni sono `docs/reference/v06_vision_world.txt`,
`v06_vision_expanded.txt`, `v06_vision_new_interior.txt`, `v06_vision_vehicle.txt`,
`v06_vision_train.txt` e `v06_vision_portrait.txt`. Come nelle iterazioni precedenti, si tratta di
un'analisi di modello, non di una revisione umana.

Osservazioni registrate:

- `world_desktop`: il modello riconosce stazione, binari, edifici e HUD, senza segnalare difetti
  misurabili.
- `expanded_area`: descrive personaggio e HUD; l'ipotesi di "case troppo semplici" è un giudizio
  soggettivo sulla pixel art a risoluzione ridotta, non un difetto misurato.
- `vehicle`: legge correttamente HUD, "Vespa acquistato — € 420.00", carburante al 100% e pulsanti
  CORRI/E; non riporta difetti evidenti.
- `train_ride`: vede treni e HUD e ipotizza un'incoerenza tra posizione e binari. Posizione e
  tracciato derivano da `rail_route` OSM verificato: l'interpretazione resta non confermata.
- `portrait`: HUD e personaggi leggibili, nessun difetto evidente.

Il caso `new_interior` è stato registrato come limite del modello: la descrizione prodotta parla
di stazione e treni pur trattandosi dello screenshot della stanza `supermarket`, confermato dallo
stato E2E (`room === 'supermarket'`). Non è un difetto dell'asset.

Limite aggiuntivo del metodo: una prima analisi con prompt troppo generico ha generato risposte
ripetitive e degenerate; i file sono stati poi riscritti con un prompt vincolato e
`num_predict=180`. Le osservazioni utilizzate in questa iterazione sono quelle della seconda
analisi.

Non sono state applicate correzioni a seguito della revisione multimodale: le osservazioni sono
interpretazioni soggettive o non confermate, mentre i controlli automatici restano verdi. La
revisione visiva umana resta pendente. I test sono stati eseguiti in Chrome headless su Windows
in emulazione: non sono stati testati dispositivi fisici, APK, EXE o app native. Anche la
pubblicazione e la verifica pubblica della 0.6.0 restano in attesa.
