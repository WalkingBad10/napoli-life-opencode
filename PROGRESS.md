# PROGRESS.md — stato dello sviluppo

Aggiornato: 2026-11-26 — versione 0.6.0 (Pianura espansa, pubblicata e verificata sul link GitHub Pages)

## Completato

- [x] Analisi strumenti: Node, Python 3.12, Pillow/numpy/pyproj/shapely, Git/GitHub CLI autenticata, Chrome per Playwright, Ollama locale `qwen2.5vl:3b`.
- [x] Scelta architettura confermata: Phaser 3.90 + TypeScript + Vite, renderer Canvas 2D; nessun secondo motore grafico.
- [x] Repository indipendente; v0.2.0, v0.3.0, v0.4.0 e v0.5.0 preservate con tag/branch dedicati; nessun altro progetto toccato. La 0.5.0 resta disponibile con tag `v0.5.0-stable` e la 0.6.0 è pubblicata con tag `v0.6.0-stable`.
- [x] OSM reale esteso: dump `data/osm/pianura_expanded_20261126.json` (2591 elementi), metadati v0.5 conservati in `data/osm/latest_v05.json`; 410 elementi viari (389 way stradali + 21 puntuali: 18 fermate, 2 stop, 1 semaforo), 829 edifici OSM, 14 binari, 2 banchine, `rail_route` di 12 way OSM reali, 129 POI reali + 2 fittizi dichiarati, 2 tabaccherie OSM, 50 landcover.
- [x] **0.6.0 — area rettangolare:** `x [-256, 704]`, `y [-320, 704]` m (circa 960 × 1024 m), origine stazione `(0, 0)`, 240 settori da 64 m (15 × 16), 1 m = 16 px esterni, 48 px/m interni, `engine_scale = 1`; 240 tile e 829 sprite edificio generati.
- [x] **0.6.0 — streaming:** `SectorStreamer` con blocco 3 × 3 attorno al giocatore, cache e scarico; test con 4 settori all'avvio e 9 dopo lo spostamento su 240 totali.
- [x] **0.6.0 — sistemi:** `VehicleSystem` (acquisto/guida/rifornimento auto e moto, carburante, collisioni), `SocialSystem` (amicizia/romance, un regalo al giorno, livelli), porte ancorate ai POI, modalità passeggero EAV distinta dalla guida manuale del treno.
- [x] **0.6.0 — salvataggi:** versione 6 con migrazione additiva da v5 verificata dai test end-to-end; progressi e campi vecchi preservati.
- [x] **0.6.0 — POI e interni:** Strade verificate (Nelson Mandela, Montagna Spaccata, Provinciale Napoli, Amedeo Modigliani, Pablo Picasso, Pallucci, Sartania, Nabucco, Giorgio De Chirico, San Josemaria Escrivà, Salvador Dalì); POI notevoli reali (Conad 128.6/162.5, GoldBet -217.9/82.2, Eurobet 515.4/406.7, Coop 372.4/334.2 e 558.8/-57.4, Anema e Pane 243.0/300.1, bar caffè 17.5/142.9 e 255.9/276.9, tabaccherie 391.9/-150.7 e 627.1/408.3, edicole 424.7/-179.9 e 485.9/24.6, mall 647.3/337.1, McDonald's 646.0/331.9, Vigili del Fuori Pianura e fermate bus dal dump; parcheggi non mappati nel rettangolo giocabile); 11 interni totali, 42 sprite, 20 audio.
- [x] Verifiche locali reali: `node node_modules/typescript/bin/tsc --noEmit` OK; `node node_modules/vite/bin/vite.js build` OK; `python tools/validate_world.py` 70/70; `node tests/run-tests.mjs` 64/64 con 0 errori console; `python tools/visual_qa.py` 85/85.
- [x] Tredici screenshot reali `screenshots/v0.6_*.png`; desktop 297 colori, 0,00% nero, 16,63% bordi; portrait/landscape emulati senza reload.
- [x] Critica visiva locale registrata in `docs/reference/v06_vision_*.txt` con `qwen2.5vl:3b`: nessuna immagine è uscita dal computer; non sostituisce la revisione umana.
- [x] Documentazione aggiornata a 0.6.0: README, CHANGELOG, PROGRESS, HANDOFF, ROADMAP e AGENTS.
- [x] Pubblicazione 0.6.0: commit `221b5ab`, tag `v0.6.0-stable`, push su `main`, CI `45890587139` e Deploy `45890587057` verdi; verifica pubblica 14/14 con screenshot `screenshots/v0.6_public_link.png` e report `screenshots/public-link-report.json`.

## In corso / non ancora completato

- [ ] Verifica concreta di un Codespace remoto (richiede apertura dal browser con account GitHub).
- [ ] Pacchetti EXE, APK e nativi Apple: non generati e non dichiarati come pronti.
- [ ] Test su dispositivi fisici Windows/Android/iOS/MacBook e misurazione FPS reale: solo emulazione browser e build web in Chrome headless su Windows.
- [ ] Revisione visiva umana degli screenshot: l'analisi automatica e il modello multimodale locale non la sostituiscono.
- [ ] Il tracciato ferroviario prosegue oltre l'area ricostruita: il viaggio passeggero si ferma al confine dei settori generati, senza collegamenti inventati.
- [ ] I 2 centri "Scommesse d'oro" restano esplicitamente fittizi, ancorati a `way/655446563` e `way/623181901`.
- [ ] Conferma fotografica definitiva di piani/colori della stazione e delle targhe 2020 sul fronte; foto verificate per livrea del treno e interni EAV reali.

## Prossimo obiettivo

La 0.6.0 è pubblicata, verificata (14/14 controlli pubblici, 70/70 validazioni, 64/64 test end-to-end, 85/85 controlli visivi) e taggata `v0.6.0-stable`. Prossimo obiettivo: raccogliere il giudizio visivo umano e, solo dopo, valutare la 0.7 multipiattaforma. Nessuna nuova zona verrà aggiunta finché la qualità dell'area ricostruita non sarà confermata da una persona. Alcune attività/uscite derivate da POI OSM senza orari dichiarati rispettano `BUSINESS_HOURS`; nessun parcheggio è stato inventato nel contatto immediato. Link stabile: `https://walkingbad10.github.io/napoli-life-opencode/`.
