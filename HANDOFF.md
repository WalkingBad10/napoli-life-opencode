# HANDOFF.md — continuità tra sessioni

Ultimo aggiornamento: 2026-11-26 · versione **0.6.0 in locale** · branch `main` · modifiche non committate

## Stato reale del progetto

| Elemento | Valore verificato |
|---|---|
| Cartella | `C:\Users\rocka\Documents\Progetto predefinito\napoli-life-opencode` |
| Repository | `https://github.com/WalkingBad10/napoli-life-opencode` (pubblico) |
| Link giocabile | `https://walkingbad10.github.io/napoli-life-opencode/` — ultima versione pubblicata e verificata: 0.5.0; 0.6.0 in attesa di pubblicazione |
| Backup 0.2.0 | tag `v0.2.0-stable` e branch `backup-v0.2.0` |
| Backup 0.3.0 | tag `v0.3.0-stable` e branch `backup-v0.3.0` |
| Backup 0.4.0 | tag `v0.4.0-stable` |
| Commit 0.4 | `a76d34a` (`v0.4.0: rifinisci Pianura, stazione verificata e QA visiva locale`) |
| Commit 0.5 | `985b10d` (`v0.5.0: vita quotidiana a Pianura, pizzeria OSM, lavoro, casa e treno guidabile`) |
| Tag 0.5 | `v0.5.0-stable` — versione pubblicata, storia non riscritta |
| Commit documentazione 0.5 | `14de3b0` (`docs: 0.5.0 pubblicata, verifica link e report visivi finali`) |
| Commit 0.6 | **nessuno**: le modifiche sono nel working tree di `main`, non committate e non pushate |
| Motore | Phaser 3.90, TypeScript, Vite, renderer Canvas 2D (confermato) |
| Dati | dump OSM esteso `data/osm/pianura_expanded_20261126.json` (2591 elementi); metadati v0.5 in `data/osm/latest_v05.json` |
| Area | `x [-256, 704]`, `y [-320, 704]` m (circa 960 × 1024 m); 240 settori 64 m (15 × 16); origine stazione `(0, 0)`; 1 m = 16 px, 48 px/m interni, `engine_scale = 1` |
| Conteggi | 410 viari (389 way + 21 puntuali: 18 fermate, 2 stop, 1 semaforo), 14 binari, 2 banchine, 12 way `rail_route`, 829 edifici OSM, 129 POI reali + 2 fittizi, 2 tabaccherie, 50 landcover, 240 tile, 829 sprite edificio, 42 sprite, 11 interni, 20 audio |
| Test locali 0.6 | `tsc --noEmit` OK; build Vite OK; 70/70 validazioni; 64/64 test end-to-end con 0 errori console; 85/85 controlli visivi; 13 screenshot `v0.6_*.png` |
| Metriche desktop 0.6 | 297 colori, 0,00% nero, 16,63% bordi; portrait/landscape emulati senza reload |
| Test link pubblico | 11/11 per la **0.5.0**: HTTP 200, versione 0.5.0, movimento attivo, 288 colori, 0 errori console. Verifica pubblica della 0.6.0 **da eseguire** |
| Test CI 0.5 | workflow `CI` (`45885357869`) e `Deploy` (`45885357952`) entrambe `success`; nessun risultato CI/Deploy dichiarato per la 0.6.0 |
| Ambiente test | Chrome headless su Windows, emulazione viewport — non dispositivo fisico |

## Cosa è stato fatto davvero nella 0.6.0

- [x] Salvataggio versione 6 con migrazione **additiva** da v5, verificata dai test end-to-end; campi e API di test precedenti conservati.
- [x] Area rettangolare estesa con 240 settori da 64 m; `SectorStreamer` carica un blocco 3 × 3 attorno al giocatore, mette in cache e scarica il resto (4 settori all'avvio, 9 dopo lo spostamento nei test).
- [x] OSM esteso con dump verificato: Via Nelson Mandela, Via Montagna Spaccata, Via Provinciale Napoli, Via Amedeo Modigliani, Via Pablo Picasso, Via Pallucci, Via Sartania, Via Nabucco, Via Giorgio De Chirico, Via San Josemaria Escrivà, Via Salvador Dalì; 12 way `rail_route` reali verso ovest e Montesanto, senza collegamenti inventati.
- [x] POI reali notevoli nel dump: Conad (128.6, 162.5), GoldBet (-217.9, 82.2), Eurobet (515.4, 406.7), Coop (372.4, 334.2) e (558.8, -57.4), Anema e Pane (243.0, 300.1), bar caffè (17.5, 142.9) e (255.9, 276.9), tabaccherie (391.9, -150.7) e (627.1, 408.3), edicole (424.7, -179.9) e (485.9, 24.6), mall (647.3, 337.1), McDonald's (646.0, 331.9), Vigili del Fuori Pianura e fermate bus presenti nel dump; nessun parcheggio è mappato nel rettangolo giocabile.
- [x] I 2 centri "Scommesse d'oro" sono POI fittizi dichiarati, gialli, ancorati a `way/655446563` e `way/623181901`; GoldBet ed Eurobet restano POI OSM reali.
- [x] Nuovi sistemi: `VehicleSystem` (acquisto, guida e rifornimento di auto e moto, carburante, collisioni), `SocialSystem` (amicizia/romance, regali una volta al giorno, livelli), porte POI-ancorate, modalità passeggero EAV distinta dalla guida manuale del treno.
- [x] Sei interni nuovi ancorati a POI OSM (supermercato, bookmaker, tabaccheria, forno, abbigliamento, officina) più i cinque storici: 11 interni totali; 42 sprite e 20 audio originali generati da `tools/`.
- [x] Verifiche locali con i comandi `node`/`python` (PowerShell blocca `npm.ps1`): 70/70 validazioni cartografiche, 64/64 test end-to-end, 85/85 controlli visivi, zero errori console; 13 screenshot reali in `screenshots/`.
- [x] Analisi visiva locale con `qwen2.5vl:3b` in `docs/reference/v06_vision_*.txt`: nessuna immagine è uscita dal computer; critiche e esiti non sostituiscono la revisione umana.
- [x] Documentazione aggiornata: README, CHANGELOG, PROGRESS, HANDOFF, ROADMAP e AGENTS. Nessun commit, nessun push e nessun altro file toccato in questa sessione.

## Cosa NON è ancora stato fatto

- [ ] Pubblicazione della 0.6.0 e verifica pubblica del link: da eseguire; non dichiarare risultati o run CI/Deploy per la 0.6.0.
- [ ] Commit e push delle modifiche 0.6.0 (richiesti dalla procedura standard, ma esplicitamente sospesi in questa sessione).
- [ ] Test su dispositivi fisici: Windows nativo, Pixel 9 Pro XL/Android, iPhone/iOS, MacBook M1; FPS reale non misurato.
- [ ] APK, EXE, app Apple: non generati. Architettura pronta per Capacitor ma non configurata.
- [ ] Revisione visiva umana degli screenshot: l'analisi locale con modello multimodale non la sostituisce.
- [ ] Il tracciato ferroviario prosegue oltre l'area ricostruita: il viaggio passeggero si ferma al confine dei settori generati.
- [ ] Conferma fotografica definitiva di piani/colori della stazione e delle targhe 2020; foto verificate per livrea del treno e interni EAV reali.
- [ ] Codespace aperto e usato davvero dal browser con account GitHub.

## Approssimazioni da ricordare

Vedere `MAP_SOURCES.md`, `docs/ART_SPEC.md` e `docs/reference/station_research.md`. La geometria di
strade, binari, banchine e perimetri è reale e deriva da OSM (© OpenStreetMap contributors, ODbL 1.0).
Sono ricostruzioni artistiche originali: altezze degli edifici, finestre/balconi/tegole, livrea del
treno, arredi interni, dialoghi NPC, arredo urbano e murales. Gli orari dei negozi sono simulati:
il dump OSM non contiene `opening_hours` per le attività coinvolte; alcune attività/uscite derivate
da POI OSM senza orari dichiarati rispettano `BUSINESS_HOURS`. I 2 centri "Scommesse d'oro" sono
fittizi e dichiarati. Nessun parcheggio è mappato nel contatto immediato, quindi non è stato inventato.

## Come riprendere il lavoro

```bash
cd "C:\Users\rocka\Documents\Progetto predefinito\napoli-life-opencode"
git status
git pull
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
python tools/validate_world.py
node tests/run-tests.mjs
python tools/visual_qa.py
```

Dopo la pubblicazione, e solo allora: `node tests/verify-public.mjs`.
Evitare `npm run build` e `npm run test:*` da PowerShell: lo script `npm.ps1` viene bloccato.
Dopo ogni modifica: aggiornare `PROGRESS.md`, `CHANGELOG.md`, `HANDOFF.md`, fare commit e push
se la sessione non vieta esplicitamente di farlo. Verificare sempre che i workflow
`.github/workflows/ci.yml` e `deploy.yml` siano verdi prima di dichiarare la versione stabile.

## Regola per la prossima sessione

Leggere `AGENTS.md` **prima** di toccare qualsiasi file. Non modificare progetti esistenti.
Non ampliare l'area oltre i settori generati prima che la 0.6.0 sia pubblicata, verificata e
confermata visivamente da una persona: la priorità è la qualità di Pianura, non la quantità di zone.
Prima di dichiarare la 0.6.0 stabile: pubblicare, verificare CI/Deploy e link pubblico.
