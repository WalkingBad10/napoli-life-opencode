# CHANGELOG.md

## 0.4.0 — 2026-11-26 — "Pianura rifinita"

- Versione 0.3.0 preservata con tag `v0.3.0-stable` e branch `backup-v0.3.0`; nessun progetto esistente toccato e nessuna nuova zona aggiunta.
- Ricerca documentata sulla stazione reale in `docs/reference/station_research.md`: fonti OSM, Wikidata, Wikipedia, EAV e stampa locale; fatti verificati separati da ricostruzioni plausibili.
- Analisi locale della foto 2018 con `qwen2.5vl:3b` tramite `tools/ollama_vision.py`: nessuna immagine è uscita dal computer e nessuna foto è stata copiata negli asset.
- Stazione corretta secondo le fonti: **due piani**, tetto piano con aggetto sull'ingresso, insegna "PIANURA" leggibile in font bitmap e targa "DON GIUSTINO RUSSOLILLO"; **pensilina rimossa** perché OSM riporta `shelter=no` su entrambe le banchine; due murales originali ispirati ai soggetti documentati, non copie.
- 73 edifici rifiniti: cornici e marcapiani, plinti, gronde, portali napoletani con transom, persiane a listelli, balconi in ferro con fiori, tettoie, terrazze con bucato e insegne commerciali coerenti con i tag OSM.
- Luci notturne ancorate alle finestre reali: il manifest edifici ora contiene `windows`, il motore non usa più una griglia approssimata e il piano terra resta buio.
- Suolo rigenerato: marciapiedi 1,5 m/2 m con cordolo e giunti, asfalto con rattoppi e tombini regolari, linea centrale tratteggiata solo sulle strade gerarchicamente superiori, binari con traverse e drenaggio, banchine tattili, recinzioni con montanti.
- 26 sprite rifatti a mano: volti e accessori differenziati, 4 frame per direzione con piedi ancorati, veicoli con vetri/specchietti/targhe, treno EAV asse-aligned, arredo urbano con ombre alpha 44.
- Interni rifatti: bar napoletano con espresso a tre gruppi, vetrina di sfogliatelle/babà/cannoli, menu e frigo; stazione con tabellone, tornelli e biglietteria; negozio e casa con arredi quotidiani. Spawn e interazioni invariati.
- `docs/ART_SPEC.md` aggiornato a contratto v0.4; `docs/VISUAL_QA.md` registra le iterazioni e le critiche della visione locale.
- Verifiche: build OK, 26/26 validazioni, 30/30 test end-to-end, 27/27 controlli visivi, zero errori console; screenshot reali v0.4 in `screenshots/`.

## 0.3.0 — 2026-11-26 — "Ricostruzione grafica straordinaria"

- Versione 0.2.0 preservata con tag `v0.2.0-stable` e branch `backup-v0.2.0`; nessun progetto esistente toccato.
- Aggiunto `docs/ART_SPEC.md`: proiezione obliqua a tre quarti tipo Stardew Valley, metrica 1 m = 16 px, regole vincolanti per edifici, suolo, sprite e profondità.
- Suolo rigenerato direttamente a 16 px/m (36 settori 1024 × 1024); rimosso `setScale(2)`, bande chiare centrali, giunti arrotondati e ombre poligonali sfalsate.
- 73 edifici ricostruiti come volumi architettonici dai bbox OSM: finestre 12 × 16 su griglia 38 × 46, porte al livello strada, balconi allineati, tetti regolari e manifest con origini corrette.
- Fabbricato viaggiatori di Pianura ridisegnato dalla fotografia fornita e dai dati OSM: facciata 921 px, pensilina metallica, vetrate, colonne e insegna EAV; spawn e ingresso spostati sulla banchina reale.
- Sprite originali ridisegnati: personaggi 16 × 32 px, auto 72 × 40, bus 112 × 44, treno EAV 576 × 56, arredo urbano coerente; nessuna rotazione del treno visto di lato.
- Interni ridisegnati in pixel art coerente e ancorati a edifici OSM reali; bar, negozio e casa non sono più posizionati dentro il fabbricato viaggiatori.
- UI ridimensionata: HUD e icone più leggibili, pannelli più ampi, pulsanti touch maggiori.
- Salvataggi migrati alla versione 4: gli spawn vecchi vengono riportati sulla banchina senza perdere progressi.
- Aggiunti `tools/visual_qa.py` e il confronto quantitativo tra screenshot v0.2 e v0.3 in `docs/VISUAL_QA.md`.
- Verifiche: build OK, 26 controlli cartografici/asset, 30 test end-to-end, 18 controlli visivi, 0 errori console.
- Pubblicazione sullo stesso link GitHub Pages: CI e Deploy verdi (run `45870223405` / `45870223066`), verifica pubblica 8/8 (HTTP 200, versione 0.3.0, movimento attivo, palette ricca, zero errori).

## 0.2.0 — 2026-11-26 — "Pianura"

- Mondo giocabile da 300 × 300 m costruito da OSM: stazione Circumflegrea, binari, banchine, Via Nelson Mandela e condomini reali.
- Fabbricato viaggiatori con insegne EAV, vetrate, colonne e pensilina.
- Treno EAV a due casse, traffico stradale e 8 residenti con routine e dialoghi.
- Quattro interni accessibili (stazione, bar, negozio, abitazione) con arredi e commercianti.
- Cinque missioni complete con diario, ricompense e salvataggio dei progressi.
- Salvataggi versionati con migrazioni, esportazione e importazione; nessun account richiesto.
- Giorno/notte, finestre illuminate, audio ambientale e colonna sonora originali.
- Touch, gamepad, rotazione senza reload, menu a icone discrete.
- Test automatici: 25 controlli funzionali + 19 controlli cartografici, screenshot in `screenshots/`.
- CI e pubblicazione GitHub Pages tramite GitHub Actions; link pubblico verificato con 6/6 controlli su browser reale (HTTP 200, versione 0.2.0, movimento attivo, zero errori console).

## 0.1.0 — fondamenta (inclusa nella 0.2.0, non pubblicata separatamente)

- Configurazione strumenti, motore, repository, movimento, telecamera, collisioni, salvataggi e comandi touch.
