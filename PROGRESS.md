# PROGRESS.md — stato dello sviluppo

Aggiornato: 2026-11-26 — versione 0.4.0 (qualità artistica e vita quotidiana a Pianura)

## Completato

- [x] Analisi strumenti: Node 26, Python 3.12, Pillow/numpy/pyproj/shapely, Git/GitHub CLI autenticata, Chrome per Playwright, Ollama locale `qwen2.5vl:3b`.
- [x] Scelta architettura confermata: Phaser 3.90 + TypeScript + Vite, renderer Canvas 2D; Aseprite/LibreSprite non disponibili, Tiled non necessario perché il mondo usa settori PNG pre-renderizzati.
- [x] Repository indipendente; v0.2.0 e v0.3.0 preservate con tag/branch dedicati; nessun altro progetto toccato.
- [x] OSM reale convertito: 96 strade, 73 edifici, 11 binari, 2 banchine, 12 POI; geometria immutata in 0.4.
- [x] **0.4.0 — ricerca stazione**: `docs/reference/station_research.md` con 20 fonti, fatti verificati e ipotesi; analisi visiva locale della foto 2018 in `docs/reference/station_photo_vision.txt`.
- [x] **0.4.0 — contratto grafico**: `docs/ART_SPEC.md` aggiornato con standard universale, palette, metriche, regole QA e distinzione tra elementi verificati e plausibili.
- [x] **0.4.0 — edifici**: 73 facciate rifinite (cornici, portali, persiane, balconi, tettoie, terrazze, insegne); stazione a due piani senza pensilina, con insegna/targa leggibili e murales originali.
- [x] **0.4.0 — illuminazione**: `windows` nel manifest e luci notturne disegnate sulle finestre vere, non su griglia approssimata.
- [x] **0.4.0 — suolo**: marciapiedi da 1,5/2 m, asfalto con giunti e tombini, linee tratteggiate solo sulle strade maggiori, binari e banchine dettagliati, recinzioni con montanti.
- [x] **0.4.0 — sprite**: 26 asset rifatti; personaggi 16×32 con 4 direzioni × 4 frame e piedi ancorati; veicoli e treno EAV più credibili.
- [x] **0.4.0 — interni**: bar napoletano, stazione, negozio e casa ridisegnati; porte/spawn/collider invariati e verificati.
- [x] Movimento 8 direzioni, corsa, collisioni, profondità piedi, culling, interazioni, 5 missioni, economia, diario, salvataggi v4.
- [x] 8 residenti con routine e dialoghi orari, traffico stradale, treno, giorno/notte, audio originale, touch e rotazione senza reload.
- [x] Build TypeScript + Vite OK; **26/26** validazioni; **30/30** test end-to-end; **27/27** controlli visivi; zero errori console.
- [x] Sei screenshot reali v0.4 in `screenshots/` (desktop, stazione esterna/interna, bar, portrait, landscape) e report JSON aggiornati.
- [x] Iterazioni di critica visiva locale registrate in `docs/VISUAL_QA.md`, con esito delle analisi Ollama e azioni correttive.

## In corso / non ancora completato

- [ ] Verifica concreta di un Codespace remoto (richiede apertura dal browser con account GitHub).
- [ ] Pacchetti EXE, APK e nativi Apple: non generati e non dichiarati come pronti.
- [ ] Test su dispositivi fisici (Pixel 9 Pro XL, MacBook M1, iPhone) e misurazione FPS reale.
- [ ] revisione visiva umana degli screenshot: l'analisi automatica locale non la sostituisce.
- [ ] Conferma fotografica definitiva di piani/colori della stazione e della presenza effettiva delle targhe 2020 sul fronte.

## Prossimo obiettivo

Pubblicare la 0.4.0 sullo stesso link GitHub Pages, verificare CI/Deploy e la versione pubblicata,
poi raccogliere il giudizio visivo umano. Nessuna nuova zona verrà aggiunta finché la qualità di
Pianura non sarà confermata. Link stabile: `https://walkingbad10.github.io/napoli-life-opencode/`.
