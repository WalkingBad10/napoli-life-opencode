# PROGRESS.md — stato dello sviluppo

Aggiornato: 2026-11-26 — versione 0.3.0 (ricostruzione grafica straordinaria)

## Completato

- [x] Analisi strumenti: Node 26, Python 3.12, Pillow/numpy/pyproj/shapely, Git/GitHub CLI autenticata, Chrome per Playwright.
- [x] Scelta architettura: Phaser 3 + TypeScript + Vite, renderer Canvas, un solo motore. Valutata e scartata la sostituzione: il difetto era la pipeline grafica, non Phaser.
- [x] Repository indipendente e cartella dedicata; nessun progetto esistente è stato toccato.
- [x] Copia della versione precedente preservata con tag `v0.2.0-stable` e branch `backup-v0.2.0`.
- [x] Acquisizione OSM reale da Overpass (2651 elementi, bbox 40.8530–40.8590 N, 14.1590–14.1660 E).
- [x] Conversione UTM 33N con origine nel nodo stazione 4936292644; 96 strade, 73 edifici, 11 binari, 2 banchine, 12 POI.
- [x] **0.3.0 — contratto grafico** `docs/ART_SPEC.md` con proiezione obliqua a tre quarti, metrica 1 m = 16 px e regole di costruzione vincolanti.
- [x] **0.3.0 — suolo** rigenerato a 16 px/m: 36 settori 1024 × 1024, `engine_scale = 1`, ombre dure rimosse, marciapiedi/binari/banchine ricostruiti.
- [x] **0.3.0 — edifici** ricostruiti come volumi architettonici dai bbox OSM: finestre allineate 12 × 16, passo 38 × 46, porte a livello strada, tetti regolari, manifest con origini corrette.
- [x] **0.3.0 — stazione** ridisegnata dalla foto fornita e dai dati OSM: facciata 921 px, lamiera, pensilina, colonne, vetrate, insegna EAV; ingresso e spawn sulla banchina reale.
- [x] **0.3.0 — sprite** originali professionali: personaggi 16 × 32 px (4 × 4 frame), auto 72 × 40, bus 112 × 44, treno 576 × 56, 26 asset con manifest 16 px/m.
- [x] **0.3.0 — interni** ridisegnati in pixel art coerente; porte ancorate a edifici OSM reali e verificate dal validatore.
- [x] **0.3.0 — UI** ridimensionata: HUD e icone più leggibili, pannelli più ampi, touch target maggiori.
- [x] Movimento 8 direzioni, corsa, collisioni precise, profondità piedi, culling per settori.
- [x] Interazione, dialoghi, 5 missioni funzionanti, diario, economia e inventario.
- [x] 8 NPC, routine orarie, traffico, treno, giorno/notte e finestre illuminate sulle nuove griglie.
- [x] Salvataggi v4 con migrazione automatica dalla v3 (spostamento dallo spawn vecchio alla banchina), import/export, senza account.
- [x] Rotazione verticale/orizzontale senza reload, posizione e progressi conservati.
- [x] Build TypeScript + Vite OK; 26 controlli cartografici/asset; 30 test end-to-end; 18 controlli visivi automatici.
- [x] Screenshot reali v0.3 in `screenshots/` (desktop, bar, portrait, landscape, link pubblico).
- [x] Workflow CI e Deploy GitHub Pages entrambe `success` sul commit `8743e63` (run `45870223405` / `45870223066`).
- [x] Link pubblico verificato: 8/8 controlli, HTTP 200, versione 0.3.0, movimento attivo, palette ricca, zero errori console.

## In corso / non ancora completato

- [ ] Verifica concreta di un Codespace remoto (richiede apertura dal browser con account GitHub).
- [ ] Pacchetti EXE, APK e nativi Apple.
- [ ] Test su dispositivi fisici (Pixel 9 Pro XL, MacBook M1 8 GB, iPhone) e misurazione FPS reale.
- [ ] Riferimenti fotografici EAV verificati per livrea e interni del treno.
- [ ] Revisione umana degli screenshot da parte del committente: l'analisi automatica non la sostituisce.
- [ ] Fase 0.4 (quartiere vivo: animazioni ambientali, orari dei negozi, più percorsi pedonali).

## Prossimo obiettivo

Raccogliere il giudizio visivo umano sulla 0.3.0 pubblicata e rifinire Pianura prima di passare
alla 0.4. Nessuna nuova zona verrà aggiunta finché la qualità della zona iniziale non sarà confermata.
Il link pubblico della 0.3.0 è stabile e verificato sullo stesso indirizzo della 0.2.0.
