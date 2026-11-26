# PROGRESS.md — stato dello sviluppo

Aggiornato: 2026-11-26 — versione 0.5.0 (vita quotidiana a Pianura)

## Completato

- [x] Analisi strumenti: Node, Python 3.12, Pillow/numpy/pyproj/shapely, Git/GitHub CLI autenticata, Chrome per Playwright, Ollama locale `qwen2.5vl:3b`.
- [x] Scelta architettura confermata: Phaser 3.90 + TypeScript + Vite, renderer Canvas 2D; nessun secondo motore grafico.
- [x] Repository indipendente; v0.2.0, v0.3.0 e v0.4.0 preservate con tag/branch dedicati; nessun altro progetto toccato.
- [x] OSM reale convertito: 96 strade, 73 edifici, 11 binari, 2 banchine, 33 POI (inclusi way nominati come Carpe Diem); geometria immutata in 0.5.
- [x] **0.5.0 — sistemi di vita**: tempo, bisogni, orari commerciali, lavoro, audio a zone e salvataggio v5 con migrazione v4 → v5 senza perdite.
- [x] **0.5.0 — routine e interazioni**: NPC con routine orarie, negozi con orari simulati, acquisto cibo/bevande, riposo, arredo casa, turni retribuiti e treno guidabile con biglietto valido.
- [x] **0.5.0 — asset**: 31 sprite (nuovi `pizzaiolo`, `pizza`, `coffee_cup`, `bookshelf`, `plant`), 5 interni (nuova `pizzeria` OSM), 14 file audio originali; manifest versionati 0.5.0.
- [x] **0.5.0 — contratto dimensionale**: 1 m = 16 px nel mondo, 48 px/m negli interni, `engine_scale = 1`, personaggi 16×32, sheet 64×128, piedi `y=30`, griglia quadrata e proiezione obliqua a tre quarti invariati.
- [x] Build TypeScript + Vite OK; **26/26** validazioni cartografiche/asset; **53/53** test end-to-end; **56/56** controlli visivi; zero errori console.
- [x] Dieci screenshot reali v0.5 in `screenshots/` (desktop, stazione esterna/interna, bar, casa arredata, pizzeria, treno, portrait, landscape) e report JSON aggiornati.
- [x] Iterazioni di critica visiva locale registrate in `docs/VISUAL_QA.md`, con esiti delle analisi Ollama `qwen2.5vl:3b` e azioni correttive.
- [x] `README.md`, `CHANGELOG.md`, `HANDOFF.md`, `docs/ART_SPEC.md`, `docs/VISUAL_QA.md`, `ASSET_GUIDE.md` e `MAP_SOURCES.md` aggiornati a 0.5.0.
- [x] Workflow CI (`45885357869`) e Deploy (`45885357952`) verdi sul commit `985b10d`.
- [x] Link pubblico verificato: 11/11 controlli, HTTP 200, versione 0.5.0, movimento attivo, 288 colori campionati, zero errori console; screenshot `v0.5_public_link.png`.

## In corso / non ancora completato

- [ ] Verifica concreta di un Codespace remoto (richiede apertura dal browser con account GitHub).
- [ ] Pacchetti EXE, APK e nativi Apple: non generati e non dichiarati come pronti.
- [ ] Test su dispositivi fisici (Pixel 9 Pro XL, MacBook M1, iPhone) e misurazione FPS reale.
- [ ] Revisione visiva umana degli screenshot: l'analisi automatica locale non la sostituisce.
- [ ] Conferma fotografica definitiva di piani/colori della stazione e delle targhe 2020 sul fronte.
- [ ] Foto verificate per livrea del treno e interni EAV reali.

## Prossimo obiettivo

Pubblicare la 0.5.0 sullo stesso link GitHub Pages, verificare CI/Deploy e la versione pubblicata,
poi raccogliere il giudizio visivo umano. Nessuna nuova zona verrà aggiunta finché la qualità di
Pianura non sarà confermata. Link stabile: `https://walkingbad10.github.io/napoli-life-opencode/`.
