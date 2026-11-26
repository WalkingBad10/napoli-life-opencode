# NAPOLI LIFE — OpenCode Edition

Simulatore di vita open world in pixel art 2D ambientato nella **vera Pianura (Napoli)**,
con partenza dalla **stazione Circumflegrea**. Il mondo è costruito da dati OpenStreetMap
reali, non da una ricostruzione approssimata.

- **Versione corrente:** 0.4.0 — Pianura rifinita: qualità artistica e vita quotidiana
- **Link web giocabile e verificato:** <https://walkingbad10.github.io/napoli-life-opencode/>
- **Repository:** <https://github.com/WalkingBad10/napoli-life-opencode>
- **Licenza dati:** © OpenStreetMap contributors, ODbL 1.0
- **Grafica/audio:** originali, generati da `tools/` con proiezione obliqua a tre quarti

## Perché Phaser 3 e non Godot

La versione web doveva essere giocabile fin dal primo aggiornamento e rimanere identica su
Windows, Android, browser e (in seguito) Apple. Phaser 3 + TypeScript + Vite offre un unico
renderer 2D Canvas, build statico immediatamente pubblicabile su GitHub Pages, touch e gamepad
nativi e la possibilità di incapsulare lo stesso build in Capacitor per APK. Godot 4 non era
installato e l'export web richiede template aggiuntivi; usare entrambi i motori avrebbe
duplicato gli asset senza vantaggi qualitativi.

Nella 0.3.0 il problema non era il motore ma la **pipeline grafica**: suolo a 8 px/m scalato
2× dal motore, sprite fuori metrica, ombre poligonali dure e finestre disegnate al piano
sbagliato. Ho valutato la sostituzione del renderer, ma Phaser Canvas 2D gestisce correttamente
la pixel art una volta rispettato il contratto in `docs/ART_SPEC.md`; cambiare motore avrebbe
messo a rischio gameplay, link pubblico e test senza migliorare la qualità visiva.

## Avvio

```bash
npm install
npm run dev      # http://localhost:5173 (solo sviluppo locale)
npm run build    # produce dist/
npm run preview  # verifica del build
npm run test:e2e     # screenshot reali + controlli funzionali
npm run test:visual  # analisi qualitativa degli screenshot e degli asset
npm run test:public  # verifica il link pubblico con browser reale
npm run test:all     # build + e2e + controllo visivo
```

Per rigenerare tutti gli asset dal grezzo (richiede rete solo per `fetch_osm.py`):

```bash
python -m pip install pillow numpy pyproj shapely requests
npm run assets
python tools/validate_world.py
```

## Comandi di gioco

| Azione | Tastiera | Touch / gamepad |
|---|---|---|
| Movimento 8 direzioni | WASD o frecce | joystick sinistro / stick sinistro |
| Corsa | Shift | pulsante CORRI / A o RB |
| Interazione | E o Spazio | pulsante E / B |
| Chiudere pannelli | Esc | pulsante ✕ |
| Menu | icone in alto a destra | stesse icone |

Le icone sono piccole e i pannelli sono chiusi di default. Ruotando lo smartphone non avviene
alcun reload: la camera si adatta, il personaggio resta dove si trova e i progressi restano intatti.

## Cosa cambia nella 0.4.0

- **Stazione secondo le fonti:** due piani, tetto piano con aggetto, insegna "PIANURA" e targa "DON GIUSTINO RUSSOLILLO" in font bitmap leggibile; due murales originali ispirati a fonti documentate. Pensilina rimossa: OSM riporta `shelter=no` su entrambe le banchine. Fatti e ipotesi in `docs/reference/station_research.md`.
- **Luci notturne reali:** il manifest edifici contiene le coordinate delle finestre e il motore illumina solo quelle, non una griglia approssimata; il piano terra resta buio.
- **Facciate napoletane:** cornici, marcapiani, portali con transom, persiane a listelli, balconi in ferro con fiori, gronde, terrazze con bucato e insegne coerenti con i tag OSM. Geometria e bbox invariati.
- **Suolo più credibile:** marciapiedi da 1,5/2 m con cordolo e giunti, asfalto con rattoppi/tombini, linea centrale tratteggiata solo sulle strade maggiori, binari con traverse e drenaggio, banchine tattili, recinzioni con montanti.
- **Sprite e interni rifatti:** 26 asset con volti/accessori differenziati e piedi ancorati; bar napoletano con espresso, sfogliatelle, babà e cannoli; stazione con tabellone e tornelli; negozio e casa con oggetti quotidiani. Spawn e interazioni invariati.
- **Analisi visiva locale:** Ollama `qwen2.5vl:3b` con `tools/ollama_vision.py`; nessuna immagine lascia il computer. Iterazioni e critiche in `docs/VISUAL_QA.md`.
- **Gameplay preservato:** 5 missioni, 8 NPC con routine, traffico, treno, economia, inventario, salvataggi v4, touch e rotazione senza reload.
- **Qualità verificata:** 26/26 validazioni, 30/30 test end-to-end, 27/27 controlli visivi, zero errori console; sei screenshot reali v0.4.

## Struttura

```
src/scenes/      BootScene, WorldScene
src/entities/    Player, NPC, Traffic
src/systems/     Input, Time, Save, Quest, Audio
src/world/       Collision, WorldLoader
src/ui/          UI HTML overlay
tools/           pipeline OSM, pixel art, audio, validazione e visual QA
docs/ART_SPEC.md contratto grafico vincolante della 0.4.0
data/osm/        risposta Overpass grezza + metadata
data/world/      mondo metrico convertito
public/assets/   tile, edifici, sprite, interni, audio
tests/           suite Playwright
screenshots/     screenshot e report dei test
```

## Piattaforme

- **Web:** link pubblico qui sopra, aggiornato da GitHub Actions.
- **Windows / macOS:** build statico Vite, imballabile in seguito con Electron/Tauri.
- **Android / iOS:** non ancora impacchettati; architettura pronta per Capacitor. Nessun APK o EXE è stato generato nella 0.4.0.

## Limitazioni note

Vedere `MAP_SOURCES.md` per le approssimazioni cartografiche, `docs/ART_SPEC.md` per il contratto grafico e `HANDOFF.md` per le attività pendenti. I test sono eseguiti in Chrome headless su Windows (emulazione), non su dispositivi fisici. L'analisi visiva automatica non sostituisce la revisione umana degli screenshot.
