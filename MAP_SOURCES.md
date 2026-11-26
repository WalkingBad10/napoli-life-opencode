# MAP_SOURCES.md — fonti cartografiche, licenze e approssimazioni

## Fonte primaria

Tutta la geometria del mondo deriva da **OpenStreetMap**, scaricata tramite Overpass.

| Proprietà | Valore |
|---|---|
| Endpoint Overpass | `https://maps.mail.ru/osm/tools/overpass/api/interpreter` |
| Data cattura (UTC) | `2026-11-26T16:06:11Z` |
| Bbox | sud 40.8530 · ovest 14.1590 · nord 40.8590 · est 14.1660 |
| Query | `[out:json][timeout:180]; (nwr(40.853,14.159,40.859,14.166);); out ids tags geom;` |
| Elementi grezzi | 2651 |
| File grezzo conservato | `data/osm/pianura_20261126.json` (copia corrente in `data/osm/latest.json`) |
| Nodo origine stazione | `node/4936292644` — 40.8560001, 14.1624307 (Via Nelson Mandela, Pianura) |
| Proiezione | UTM 33N / EPSG:32633, origine locale nel nodo della stazione |
| Convenzione assi | `x = est`, `y = sud` (schermo), 1 metro = 16 pixel |
| Licenza | **© OpenStreetMap contributors, ODbL 1.0** — https://www.openstreetmap.org/copyright |

L'attribuzione è visibile nella schermata iniziale, nelle impostazioni e in questo file.
I dati grezzi e convertiti sono inclusi nel repository: il gioco **non effettua chiamate di rete** durante il gameplay.

## Elementi OSM utilizzati

- `highway` (96 tratti): `primary`, `secondary`, `tertiary`, `residential`, `unclassified`, `service`, `footway`, `steps`, `path`.
- `railway=rail` (11 segmenti) e `railway=platform` (2 banchine) della Ferrovia Circumflegrea.
- `building` (73 perimetri), incluso `way/503291719` (`building=train_station`, 57,6 × 15,2 m).
- `landuse` / `leisure` (10 aree), `amenity=parking` (2), `barrier` (2).
- POI (12): negozi, bar/ristoranti, fermate, servizi.

### Verifiche automatiche

`tools/validate_world.py` controlla che ogni edificio derivi da un elemento OSM presente nel grezzo,
che il fabbricato viaggiatori sia entro 30 m dal nodo EAV, che la sua facciata sia lunga 40–80 m,
che Via Nelson Mandela sia presente, che le proporzioni degli sprite rispettino 16 px/m e che
non esistano edifici *inventati* nel corridoio ferroviario.

## Approssimazioni dichiarate

Queste scelte sono state necessarie in assenza di rilievi o fotografie verificate e **non** vanno confuse con dati OSM:

1. **Livrea e proporzioni del treno EAV**: la sagoma a due casse (36,0 m) e i colori blu/oro sono ricostruzioni originali plausibili, non una riproduzione fotografica certificata.
2. **Interni** (stazione, bar, negozio, abitazione): ambienti originali in pixel art, coerenti con la proiezione del gioco; le posizioni esatte di banchi, macchinette e arredi non provengono da OSM.
3. **Altezza degli edifici**: stimata da `building:levels` quando disponibile, altrimenti da 2–4 piani in base al contesto; non è un dato verificato sul posto.
4. **Facciate e tetti**: la pianta, la posizione e le dimensioni derivano dal bbox OSM; finestre, balconi, tegole e insegne sono ricostruzioni artistiche regolari, non rilievi fotografici. La stazione è stata ridisegnata nella 0.4.0 usando OSM, fonti testuali e un'analisi visiva locale della foto 2018; **nessun pixel della foto è stato copiato**. I gradi di certezza sono in `docs/reference/station_research.md`.
   - Verificato: geometria 57,6 × 15,2 m, due binari, due banchine con `shelter=no`, titolazione a Don Giustino Russolillo del 2020.
   - Plausibile non verificato: due piani, tetto piano con aggetto, colori dell'intonaco, testo esatto dell'insegna, murales riprodotti come illustrazioni originali.
   - La pensilina della 0.3.0 è stata **rimossa** in 0.4.0 perché contraddetta da OSM e dall'analisi della foto.
5. **Arredi urbani** (lampioni, panchine, bidoni, piani fioriti): posizionati proceduralmente sui marciapiedi derivati dalle strade OSM, non censiti singolarmente.
6. **Nomi e dialoghi dei NPC**: personaggi fittizi; i POI commerciali reali sono usati solo come ancoraggi geografici.
7. **Treno e traffico**: i percorsi seguono i tracciati OSM reali, ma orari, velocità e frequenze sono simulati.
8. **Stato dei POI**: un'attività presente in OSM potrebbe aver cambiato stato rispetto alla cattura; la versione 0.5.0 usa lo stato dei tag al momento dello scarico. Le insegne commerciali derivano solo da tag/nome OSM o categoria generica; non sono attribuzioni certe a esercizi reali.
9. **Orari commerciali nella 0.5.0**: il dump OSM non contiene tag `opening_hours` per bar, negozi e stazione. Gli orari mostrati nel telefono di gioco sono quindi **simulazioni dichiarate**, non dati OSM; `convert_osm.py` esporta comunque il campo quando presente.
10. **Pizzeria Carpe Diem**: `way/655446533` (`amenity=restaurant`, `cuisine=pizza`) è un POI OSM reale dentro l'area giocabile, con perimetro edificato. L'interno e le interazioni sono ricostruzioni originali ancorate a quel poligono; nessuna attività è stata inventata per riempire la mappa.
11. **Tabaccherie**: non risulta alcuna tabaccheria mappata nei dati OSM disponibili. Il generatore può usare l'etichetta generica `TABACCHI` solo come insegna architettonica su edifici OSM, non come attività giocabile.
12. **Bisogni, routine e lavoro**: fame, energia, turni, prezzi e validità del biglietto (90 minuti) sono regole di gameplay simulate; le posizioni di partenza dei residenti sono ancorate a strade ed edifici OSM.

## Rigenerazione

```bash
python tools/fetch_osm.py       # richiede rete; aggiorna data/osm/
python tools/convert_osm.py     # aggiorna data/world/ e public/data/world/
python tools/generate_world_tiles.py
python tools/generate_buildings.py
python tools/generate_sprites.py
python tools/generate_interiors.py
python tools/generate_audio.py
python tools/validate_world.py
```

Se si cambia la bbox, aggiornare anche la tabella in alto e il `CHANGELOG.md`.

## Mirror Overpass

L'endpoint principale `overpass-api.de` ha risposto con timeout/502/406 durante la sessione di acquisizione;
anche `overpass.kumi.systems` e `overpass.private.coffee` sono scaduti. È stato usato il mirror
`maps.mail.ru`, che ha restituito l'intero dataset. `overpass.osm.ch` risponde ma copre solo la Svizzera
ed è inadatto a Napoli. La query è conservata in `data/osm/latest.json` per ripetibilità.
