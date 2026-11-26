# HANDOFF.md — continuità tra sessioni

Ultimo aggiornamento: 2026-11-26 · versione **0.5.0** · branch `main`

## Stato reale del progetto

| Elemento | Valore verificato |
|---|---|
| Cartella | `C:\Users\rocka\Documents\Progetto predefinito\napoli-life-opencode` |
| Repository | `https://github.com/WalkingBad10/napoli-life-opencode` (pubblico) |
| Link giocabile | `https://walkingbad10.github.io/napoli-life-opencode/` |
| Backup 0.2.0 | tag `v0.2.0-stable` e branch `backup-v0.2.0` |
| Backup 0.3.0 | tag `v0.3.0-stable` e branch `backup-v0.3.0` |
| Backup 0.4.0 | tag `v0.4.0-stable` |
| Commit 0.4 | `a76d34a` (`v0.4.0: rifinisci Pianura, stazione verificata e QA visiva locale`) |
| Commit 0.5 | da assegnare dopo il commit finale |
| Motore | Phaser 3.90, TypeScript, Vite, renderer Canvas 2D (confermato) |
| Dati | OpenStreetMap catturati il 2026-11-26, salvati nel repo; 33 POI dopo l'export dei way nominati |
| Test locali | 53/53 funzionali, 26/26 cartografici/asset, 56/56 visivi, 0 errori console |
| Test link pubblico | verifica 0.5 in corso dopo il deploy (la 0.4 era 8/8) |
| Test CI | verifica 0.5 in corso dopo il push (la 0.4 era verde) |

## Cosa è stato fatto davvero nella 0.5.0

- [x] Sistemi nuovi e salvataggio v5: tempo, bisogni, orari, lavoro, audio a zone; migrazione v4 → v5 additiva e API test estesa senza rimuovere campi vecchi.
- [x] Vita quotidiana: cibi/bevande acquistabili e consumabili, riposo, libro/pianta in casa, turni retribuiti al bar e in pizzeria, treno EAV guidabile con biglietto di 90 minuti.
- [x] Quinto interno `pizzeria` ancorato a OSM `way/655446533` (Carpe Diem); orari commerciali simulati e documentati perché OSM non ha `opening_hours`.
- [x] Nuovi sprite, interni e audio generati dal codice; manifest versionati 0.5.0; `npm run assets` non usa più rete.
- [x] Geometria OSM invariata: 96 strade, 73 edifici, 11 binari, 2 banchine; nessuna nuova zona.
- [x] Build, 53/53 test end-to-end, 26/26 validazioni, 56/56 controlli visivi; dieci screenshot reali `v0.5_*.png`.
- [x] Analisi visiva locale con `qwen2.5vl:3b`: nessuna immagine è uscita dal computer; esiti in `docs/VISUAL_QA.md` e `docs/reference/v05_vision_*.txt`.
- [x] Documentazione aggiornata: README, CHANGELOG, PROGRESS, `docs/ART_SPEC.md`, `docs/VISUAL_QA.md`, `ASSET_GUIDE.md`, `MAP_SOURCES.md`.

## Cosa NON è ancora stato fatto

- [ ] Test su dispositivi fisici: Pixel 9 Pro XL, MacBook M1 8 GB, iPhone, Windows nativo.
- [ ] APK, EXE, app Apple: non generati. Architettura pronta per Capacitor ma non configurata.
- [ ] Revisione visiva umana degli screenshot: l'analisi locale con modello multimodale non la sostituisce.
- [ ] Conferma fotografica definitiva di piani/colori della stazione e delle targhe 2020.
- [ ] Foto verificate per livrea del treno e interni EAV reali.
- [ ] Codespace aperto e usato davvero dal browser con account GitHub.

## Approssimazioni da ricordare

Vedere `MAP_SOURCES.md`, `docs/ART_SPEC.md` e `docs/reference/station_research.md`. La geometria di strade, binari, banchine e perimetri è reale e deriva da OSM (© OpenStreetMap contributors, ODbL 1.0). Sono ricostruzioni artistiche originali: altezze degli edifici, finestre/balconi/tegole, livrea del treno, arredi interni, dialoghi NPC, arredo urbano e murales. Gli orari dei negozi sono simulati: il dump OSM non contiene `opening_hours`.

## Come riprendere il lavoro

```bash
cd "C:\Users\rocka\Documents\Progetto predefinito\napoli-life-opencode"
git pull
npm install
npm run build
npm run test:e2e
npm run test:visual
python tools/validate_world.py
npm run test:public
```

Dopo ogni modifica: aggiornare `PROGRESS.md`, `CHANGELOG.md`, `HANDOFF.md`, fare commit e push.
Verificare sempre che i workflow `.github/workflows/ci.yml` e `deploy.yml` siano verdi prima di dichiarare la versione stabile.

## Regola per la prossima sessione

Leggere `AGENTS.md` **prima** di toccare qualsiasi file. Non modificare progetti esistenti.
Non ampliare la mappa prima che Pianura sia rifinita: la prossima priorità è la conferma visiva umana della 0.5.0, non la quantità di zone.
