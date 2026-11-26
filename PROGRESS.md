# PROGRESS.md — stato dello sviluppo

Aggiornato: 2026-11-26 — versione 0.2.0

## Completato

- [x] Analisi strumenti: Node 26, Python 3.12, Pillow/numpy/pyproj/shapely, Git/GitHub CLI autenticata, Chrome per Playwright.
- [x] Scelta architettura: Phaser 3 + TypeScript + Vite, renderer Canvas, un solo motore.
- [x] Repository indipendente e Cartella dedicata, senza toccare progetti esistenti.
- [x] Acquisizione OSM reale da Overpass (2651 elementi, bbox 40.8530–40.8590 N, 14.1590–14.1660 E).
- [x] Conversione UTM 33N con origine nel nodo stazione 4936292644; 96 strade, 73 edifici, 11 binari, 2 banchine, 12 POI.
- [x] Pixel art originale generata da codice: 36 settori suolo, 73 edifici unici, 7 personaggi, 19 oggetti, treno EAV, 4 interni, 6 tracce audio.
- [x] Movimento 8 direzioni, corsa, collisioni precise, profondità piedi, culling per settori.
- [x] Interazione, dialoghi, 5 missioni funzionanti, diario, economia e inventario.
- [x] Interni: stazione, bar, negozio, casa; acquisti e uscita libera.
- [x] 8 NPC, routine orarie, traffico, treno, giorno/notte e finestre illuminate.
- [x] Salvataggi manuali/automatici versionati (v3), migrazioni, import/export, senza account.
- [x] UI discreta con 8 icone, pannelli chiusi di default, touch e gamepad.
- [x] Rotazione verticale/orizzontale senza reload, posizione e progressi conservati.
- [x] Build, 25 test Playwright, 19 controlli cartografici, 4 screenshot reali.
- [x] Workflow CI/CD e devcontainer per sviluppo cloud.
- [x] Repository GitHub pubblico creato e push effettuato.
- [x] GitHub Pages abilitato (build_type `workflow`), CI e Deploy verdi.
- [x] Link pubblico verificato con browser reale: 6/6 controlli, HTTP 200, nessun errore console.

## In corso / non ancora completato

- [ ] Verifica concreta di un Codespace remoto (richiede apertura dal browser con account GitHub).
- [ ] Pacchetti EXE, APK e nativi Apple.
- [ ] Test su dispositivi fisici (Pixel 9 Pro XL, MacBook M1) e misurazione FPS reale.
- [ ] Riferimenti fotografici EAV verificati per livrea e interni del treno.
- [ ] Interni derivati da rilievi reali (oggi sono ricostruzioni plausibili).
- [ ] Fase 0.3 (bar/negozi più estesi, animazioni ambientali aggiuntive).

## Prossimo obiettivo

Consolidare la qualità grafica di Pianura (revisione visiva degli screenshot, dettagli EAV verificati)
prima di iniziare la 0.3. Il link pubblico della 0.2.0 è già stabile e verificato.
