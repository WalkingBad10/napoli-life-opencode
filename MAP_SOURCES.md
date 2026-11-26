# MAP_SOURCES.md — fonti cartografiche, licenze e approssimazioni (v0.6.0)

## Fonte primaria

Tutta la geometria del mondo deriva da **OpenStreetMap**, scaricata tramite Overpass in fase di build (`tools/fetch_osm_expanded.py`). Il gioco **non effettua chiamate di rete** durante il gameplay: i dati sono già nel repository.

| Proprietà | Valore |
|---|---|
| Endpoint Overpass | `https://maps.mail.ru/osm/tools/overpass/api/interpreter` (usato anche per la query ferroviaria; fallback `overpass-api.de`, `overpass.kumi.systems`) |
| Data cattura (UTC) | `2026-11-26T19:46:53Z` |
| Bbox elementi | sud 40.8480 · ovest 14.1520 · nord 40.8640 · est 14.1720 |
| Bbox ferroviaria | sud 40.8380 · ovest 14.1340 · nord 40.8580 · est 14.1640 |
| Query | `[out:json][timeout:240]; (way["highway"]; way["building"]; way["railway"]; way["landuse"]; way["leisure"]; way["natural"]; way["barrier"]; node["highway"]; node["building"]; node["railway"]; node["public_transport"]; node["shop"]; node["amenity"]; node["place"]; node["barrier"]; relation["railway"];); out ids tags geom;` — solo i tag necessari, non l'intera bbox |
| Query ferroviaria | `[out:json][timeout:240]; (way["railway"]; node["railway"]; relation["railway"];); out ids tags geom;` sulla bbox ferroviaria |
| Elementi grezzi | **2591** (2422 way + 169 node), dopo unione delle due risposte senza duplicati |
| File grezzo conservato | `data/osm/pianura_expanded_20261126.json` (copia corrente in `data/osm/latest.json`) |
| Metadati 0.5 preservati | `data/osm/latest_v05.json` — dump `pianura_20261126.json`, 2651 elementi, cattura `2026-11-26T16:06:11Z` |
| Nodo origine stazione | `node/4936292644` — 40.8560001, 14.1624307 (Via Nelson Mandela, Pianura) |
| Proiezione | UTM 33N / EPSG:32633, origine locale nel nodo della stazione |
| Convenzione assi | `x = est`, `y = sud` (schermo), 1 metro = 16 pixel |
| Licenza | **© OpenStreetMap contributors, ODbL 1.0** — https://www.openstreetmap.org/copyright |
| Ferrovia | Circumflegrea, operatore `Ente Autonomo Volturno` (EAV) riportato nei tag OSM: attribuzione OSM + EAV |

L'attribuzione è visibile nella schermata iniziale, nelle impostazioni e in questo file.

## Area di gioco e clip dei dati

- Rettangolo giocabile della 0.6.0: `x ∈ [-256, 704]`, `y ∈ [-320, 704]` metri (960 × 1024 m), 240 settori da 64 m.
- Il dump grezzo è molto più ampio (circa `x = -2166 … 1848`, `y = -1591 … 2021` m): Overpass restituisce le **way intere** che attraversano la bbox richiesta, non solo i segmenti interni.
- `tools/convert_osm.py` seleziona gli elementi che intersecano il rettangolo di gioco più **48 m di contesto visivo** (`[-304, -368, 752, 752]`); i settori vengono disegnati solo dentro il rettangolo giocabile. Le way di `rail_route` conservano tutti i vertici OSM perché servono al percorso reale del treno verso Montesanto.
- Nessuna conformazione stradale o ferroviaria è stata disegnata a mano per riempire l'area estesa.

## Elementi OSM utilizzati

- **410 elementi viari**: 389 way stradali (`highway`) + 21 nodi viari OSM reali (18 `bus_stop`, 2 `stop`, 1 `traffic_signals`). I nodi sono conservati come elementi puntuali, senza ricostruire tracciati.
- **14 way ferroviarie della Circumflegrea** (11 `railway=rail` + 3 `railway=construction`) + **2 way `railway=platform`**; `rail_route` contiene **12 way OSM complete**, con operator EAV. Le connessioni esistono solo dove i dati OSM le definiscono: **nessun tracciato inventato**.
- **829 edifici**, tutti con ID OSM reale e perimetro convertito dal grezzo; **50** aree `landuse`/`leisure`/`natural`, **3** barriere, **0** parcheggi mappati nel contesto (non inventati).
- Due edifici OSM reali, `way/677094968` e `way/1354461724`, ricadono entro 8 m dai binari e sono stati **mantenuti per fedeltà ai dati**, non rimossi né spostati.
- **129 POI OSM reali**, più **2 POI fittizi dichiarati** "Scommesse d'oro" (vedi sotto).

### Strade verificate nel mondo convertito

Via Nelson Mandela · Via Montagna Spaccata · Via Provinciale Napoli · Via Amedeo Modigliani · Via Pablo Picasso · Via Pallucci · Via Sartania · Via Nabucco · Via Giorgio De Chirico · Via San Josemaria Escrivà · Via Salvador Dalì.

### POI verificati nel mondo convertito

Conad · Coop (POI OSM reali, anche come way) · GoldBet · Eurobet · McDonald's · centro commerciale (`Complesso Commerciale Via Nabucco`) · Anema e Pane · bar/caffè · tabaccherie · edicole · fermata `Montagna Spaccata - Vigili del Fuoco` · altre fermate bus OSM.

### POI esplicitamente fittizi

I due centri "Scommesse d'oro" (`fictional/scommesse_doro_west`, `fictional/scommesse_doro_east`) sono **finzione dichiarata**, non attività reali:

- `shop = bookmaker`, facciata gialla (`style = "yellow"`), orario `10:00-22:00` dichiarato nei dati e mostrato nel gioco come simulazione;
- ancorati ai baricentri di edifici OSM reali `way/655446563` e `way/623181901`;
- non sostituiscono i POI reali GoldBet/Eurobet, che restano invariati; l'interazione in gioco è etichettata "fittizia".

### Verifiche automatiche

`tools/validate_world.py` (**70/70**, report `data/world/validation-report.json`) controlla bounds rettangolari, contesto, provenienza OSM di ogni edificio, stazione entro 30 m dal nodo EAV, facciata lunga 40–80 m, presenza delle strade verificate, almeno 380 way stradali e 400 elementi viari, 12 way reali in `rail_route` con geometria completa, assenza di edifici inventati e coerenza dei manifest asset.

`tools/visual_qa.py` (**85/85**, `screenshots/visual-qa-report.json`) analizza 13 screenshot reali e gli asset generati; `tests/run-tests.mjs` passa **64/64** su Chrome headless in emulazione (non dispositivi fisici). Build `tsc --noEmit` + Vite OK. Non sono state eseguite prove su dispositivi fisici o app native.

## Approssimazioni dichiarate

Queste scelte sono state necessarie in assenza di rilievi o fotografie verificate e **non** vanno confuse con dati OSM:

1. **Livrea e proporzioni del treno EAV**: la sagoma a due casse (36,0 m) e i colori blu/oro sono ricostruzioni originali plausibili, non una riproduzione fotografica certificata.
2. **Interni**: ambienti originali in pixel art, coerenti con la proiezione del gioco; le posizioni esatte di banchi, macchinette e arredi non provengono da OSM.
3. **Altezza degli edifici**: stimata da `building:levels` quando disponibile, altrimenti da 2–4 piani in base al contesto; non è un dato verificato sul posto.
4. **Facciate e tetti**: la pianta, la posizione e le dimensioni derivano dal bbox OSM; finestre, balconi, tegole e insegne sono ricostruzioni artistiche regolari, non rilievi fotografici. La stazione è stata ridisegnata nella 0.4.0 usando OSM, fonti testuali e un'analisi visiva locale della foto 2018; **nessun pixel della foto è stato copiato**. I gradi di certezza sono in `docs/reference/station_research.md`.
   - Verificato: geometria 57,6 × 15,2 m, due binari, due banchine con `shelter=no`, titolazione a Don Giustino Russolillo del 2020.
   - Plausibile non verificato: due piani, tetto piano con aggetto, colori dell'intonaco, testo esatto dell'insegna, murales riprodotti come illustrazioni originali.
   - La pensilina della 0.3.0 è stata **rimossa** in 0.4.0 perché contraddetta da OSM e dall'analisi della foto.
5. **Arredi urbani** (lampioni, panchine, bidoni, piani fioriti): posizionati proceduralmente sui marciapiedi derivati dalle strade OSM, non censiti singolarmente.
6. **Nomi e dialoghi dei NPC**: personaggi fittizi; i POI commerciali reali sono usati solo come ancoraggi geografici.
7. **Treno e traffico**: il percorso segue le 12 way reali di `rail_route` e i tracciati stradali OSM; orari, velocità, frequenze e collegamenti tra way non contigui sono simulati, mai inventati come geometria.
8. **Stato dei POI**: un'attività presente in OSM potrebbe aver cambiato stato rispetto alla cattura; la 0.6.0 usa lo stato dei tag al momento dello scarico. Le insegne commerciali derivano solo da tag/nome OSM o categoria generica.
9. **Orari commerciali**: il dump OSM non contiene tag `opening_hours` per bar, negozi e stazione; gli orari mostrati nel telefono di gioco sono **simulazioni dichiarate**. `convert_osm.py` esporta comunque il campo quando presente; l'unica eccezione sono gli orari dei due POI fittizi, dichiarati esplicitamente nei dati.
10. **Pizzeria Carpe Diem**: `way/655446533` (`amenity=restaurant`, `cuisine=pizza`) è un POI OSM reale dentro l'area giocabile, con perimetro edificato. L'interno e le interazioni sono ricostruzioni originali ancorate a quel poligono.
11. **Tabaccherie**: nella 0.6.0 risultano **due tabaccherie reali nei POI OSM convertiti**; il generatore può usare l'etichetta generica `TABACCHI` come insegna architettonica su edifici OSM, senza attribuirla a un esercizio non mappato.
12. **Bisogni, routine, lavoro e relazioni**: fame, energia, turni, prezzi, validità del biglietto (90 minuti) e regalo giornaliero sono regole di gameplay simulate; le posizioni di partenza dei residenti sono ancorate a strade ed edifici OSM.
13. **Scommesse d'oro**: attività fittizia esplicita, ancorata a edifici OSM reali; nessun tentativo di presentarla come esercizio esistente.
14. **Parcheggi**: nessun `amenity=parking` è presente nel contesto convertito; l'elenco resta vuoto invece di essere riempito con parcheggi inventati.

## Rigenerazione

```bash
python tools/fetch_osm_expanded.py  # richiede rete; aggiorna data/osm/ e conserva latest_v05.json
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

Equivalente npm per soli asset: `npm run assets` (non scarica dati da rete). Verifiche e build:

```bash
npm run build          # tsc --noEmit && vite build
npm run test:e2e       # Playwright + screenshot in screenshots/
python tools/validate_world.py
```

Su **PowerShell**, se `npm run build` dà problemi, usare `node node_modules/vite/bin/vite.js build` per il passaggio di build Vite. Non dichiarare pubblicazioni o test su dispositivi fisici non eseguiti.

Se si cambia la bbox, aggiornare anche la tabella in alto e il `CHANGELOG.md`.

## Mirror Overpass

L'endpoint `overpass-api.de` e `overpass.kumi.systems` restano come fallback nello script; per la cattura della 0.6.0 è stato usato il mirror `maps.mail.ru`, che ha restituito sia la query filtrata sull'area estesa sia quella dedicata al corridoio ferroviario. `tools/fetch_osm_expanded.py` prova gli endpoint in ordine e interrompe solo se nessuno risponde. La query esatta e i metadati di cattura sono conservati in `data/osm/latest.json`; la versione precedente resta in `data/osm/latest_v05.json`.
