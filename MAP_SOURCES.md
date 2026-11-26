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

1. **Livrea e proporzioni del treno EAV**: la sagoma a due casse (35,5 m) e i colori blu/oro sono ricostruzioni procedurali plausibili, non una riproduzione fotografica certificata.
2. **Interni** (stazione, bar, negozio, abitazione): disegnati a mano come ambienti plausibili; le posizioni esatte di banchi, macchinette e arredi non provengono da OSM.
3. **Altezza degli edifici**: stimata da `building:levels` quando disponibile, altrimenti da 2–4 piani in base al contesto; non è un dato verificato sul posto.
4. **Arredi urbani** (lampioni, panchine, bidoni, piani fioriti): posizionati proceduralmente sui marciapiedi derivati dalle strade OSM, non censiti singolarmente.
5. **Nomi e dialoghi dei NPC**: personaggi fittizi; i POI commerciali reali sono usati solo come ancoraggi geografici.
6. **Treno e traffico**: i percorsi seguono i tracciati OSM reali, ma orari, velocità e frequenze sono simulati.
7. **Stato dei POI**: un'attività presente in OSM potrebbe aver cambiato stato rispetto alla cattura; la versione 0.2.0 usa lo stato dei tag al momento dello scarico.

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
