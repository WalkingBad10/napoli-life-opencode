# AGENTS.md — direttive permanenti di NAPOLI LIFE — OpenCode Edition

Questo file vale per ogni agente AI, dispositivo o ambiente cloud che lavora al progetto.
Leggerlo **prima** di toccare qualsiasi file.

## Direttive assolute

1. FEDELTÀ GEOGRAFICA PRIMA DI TUTTO. Le strade, i perimetri e i binari derivano dagli elementi OSM già salvati in `data/osm/` (dump esteso `pianura_expanded_20261126.json`, 2591 elementi) e convertiti in `data/world/pianura_world.json`: 389 way stradali OSM + 21 elementi puntuali, 829 edifici OSM, 14 binari, 2 banchine e `rail_route` di 12 way reali. Non inventare conformazioni stradali, collegamenti ferroviari, parcheggi o attività commerciali.
2. QUALITÀ PRIMA DELLA QUANTITÀ. Una strada riconoscibile vale più di dieci strade approssimate.
3. DETTAGLIO PRIMA DELL'ESPANSIONE. La 0.6.0 è pubblicata e verificata, ma la conferma visiva umana è ancora pendente: non aggiungere nuove zone oltre i 240 settori generati finché una persona non avrà confermato la qualità dell'area attuale.
4. PROPORZIONI REALISTICHE. Standard unico: **1 metro = 16 pixel** nel mondo, 48 px/m negli interni, `engine_scale = 1`, settori da 64 m. L'area corrente è `x [-256, 704]`, `y [-320, 704]` m.
5. ASSET ORIGINALI. Tutta la grafica e l'audio sono generati dal codice in `tools/`. Non copiare asset di Stardew Valley o di altri giochi.
6. LINK PUBBLICO DOPO OGNI AGGIORNAMENTO STABILE. Pubblicare su GitHub Pages e verificare il link. Il link corrente corrisponde alla 0.6.0 (tag `v0.6.0-stable`, verifica pubblica 14/14); la 0.5.0 resta preservata dal tag `v0.5.0-stable`.
7. CONTINUITÀ WINDOWS / SMARTPHONE / CLOUD. Ogni sessione significativa termina con commit, push, documentazione aggiornata e `HANDOFF.md` pronto, salvo divieto esplicito della sessione.
8. SOLO AFFERMAZIONI VERIFICABILI. Citare i numeri dei report locali e distinguerli dai risultati pubblici. I test girano in Chrome headless su Windows con emulazione viewport, non su dispositivi fisici; l'analisi con `qwen2.5vl:3b` non sostituisce la revisione visiva umana.

## Cosa NON fare

- Non modificare `bacoli-life`, `campania-life`, `campania-codex`, `campania-open-code-1`, `napoli-life-pixel-edition` o altri progetti esistenti.
- Non agganciarsi a API esterne durante il gameplay: i dati sono già nel repository.
- Non inserire token, credenziali o chiavi nel repository.
- Non attivare servizi a pagamento senza autorizzazione esplicita.
- Non dichiarare complete attività non eseguite (es. APK, EXE, test su dispositivi reali o revisione visiva umana). La verifica pubblica della 0.6.0 è invece documentata da 14/14 controlli reali.
- Non usare `npm run build` o `npm run test:*` da PowerShell: lo script `npm.ps1` viene bloccato. Usare i comandi `node`/`python` qui sotto.
- Non presentare i 2 centri "Scommesse d'oro" come reali: sono fittizi e dichiarati, ancorati a `way/655446563` e `way/623181901`.

## Architettura

- **Un solo motore**: Phaser 3.90 + TypeScript + Vite, renderer Canvas 2D (compatibilità universale, anche browser headless e mobile).
- Nessun secondo motore grafico: Godot non è installato e la sua export web richiederebbe template dedicati; Phaser permette il link giocabile subito. Capacitor potrà avvolgere lo stesso build web per Android/iOS in seguito.
- Dati cartografici: Overpass → `data/osm/` → `tools/convert_osm.py` → `data/world/` + copia runtime in `public/data/world/`; metadati della 0.5 conservati in `data/osm/latest_v05.json`.
- Generazione asset: `tools/generate_*.py` (Pillow, numpy, pyproj, shapely). Rigenerare con le chiamate `python` elencate sotto.
- Logica di gioco: `src/scenes/` (Boot, World), `src/entities/`, `src/systems/` (Input, Time, Save, Needs, Business, Job, Quest, Audio, Vehicle, Social), `src/ui/`, `src/world/` (Collision, WorldLoader, SectorStreamer).
- Salvataggi: versione 6, migrazione additiva da v5; il viaggio passeggero EAV si ferma al confine dei settori generati, senza collegamenti inventati.

## Comandi standard

```bash
npm install
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
node tests/run-tests.mjs       # avvia da sé il preview su 127.0.0.1:4173
python tools/validate_world.py
python tools/visual_qa.py
npm run dev                    # server locale solo per sviluppo
```

Workflow di pubblicazione: `.github/workflows/ci.yml` (validazione + build) e
`.github/workflows/deploy.yml` (GitHub Pages). Link stabile:
`https://walkingbad10.github.io/napoli-life-opencode/`. Il controllo pubblico
`node tests/verify-public.mjs` va eseguito solo dopo la pubblicazione della versione da verificare.

## Regole per nuove zone

1. Scaricare nuovi dati con `tools/fetch_osm_expanded.py` (modificando la bbox) e ricordare l'attribuzione in `MAP_SOURCES.md`; conservare i dump e i metadati delle versioni precedenti.
2. Riconvertire, rigenerare solo gli asset interessati (240 tile da 64 m, 829 sprite edificio), aggiornare `ASSET_GUIDE.md` se cambiano le proporzioni.
3. Aggiungere test visivi e aggiornare `PROGRESS.md`, `CHANGELOG.md`, `HANDOFF.md`.
4. Non ampliare l'area finché i controlli della zona corrente non sono verdi e la versione non è stata pubblicata; il tracciato ferroviario reale può proseguire, ma il viaggio si ferma al confine dei settori generati.

## Stato corrente

Versione 0.6.0 pubblicata e verificata (commit `221b5ab`, tag `v0.6.0-stable`, branch `main` pulito). Area rettangolare 960 × 1024 m, 240 settori
64 m, 2591 elementi OSM nel dump esteso: 410 elementi viari, 129 POI reali + 2 fittizi dichiarati,
829 edifici, 50 landcover, 42 sprite, 11 interni e 20 audio. Nuovi sistemi `SectorStreamer`,
`VehicleSystem` e `SocialSystem`; salvataggio v6 con migrazione additiva da v5.
Verifiche locali: build e `tsc` OK, 70/70 validazioni, 64/64 test end-to-end, 85/85 controlli
visivi, 13 screenshot reali, 0 errori console in Chrome headless su Windows.
Pubblicazione: CI `45890587139` e Deploy `45890587057` verdi; verifica pubblica 14/14 su
`https://walkingbad10.github.io/napoli-life-opencode/` con screenshot `screenshots/v0.6_public_link.png`
e report `screenshots/public-link-report.json`. Restano pendenti revisione visiva umana e test su
dispositivi fisici. Vedere `docs/ART_SPEC.md`, `PROGRESS.md`, `CHANGELOG.md` e `HANDOFF.md` per dettagli.
