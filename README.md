# NAPOLI LIFE — OpenCode Edition

Simulatore di vita open world in pixel art 2D ambientato nella **vera Pianura (Napoli)**,
con partenza dalla **stazione Circumflegrea**. Il mondo è costruito da dati OpenStreetMap
reali, non da una ricostruzione approssimata.

- **Versione corrente:** 0.3.0 — ricostruzione grafica straordinaria
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

## Cosa cambia nella 0.3.0

- **Proiezione corretta:** obliqua a tre quarti tipo Stardew Valley (cabinet), non isometrica improvvisata. Griglia quadrata, 1 m = 16 px.
- **Suolo riscritto:** 36 settori da 1024 × 1024 px generati direttamente a 16 px/m. Rimosso `setScale(2)`, bande chiare centrali, giunti arrotondati e ombre poligonali sfalsate.
- **Edifici architettonici:** 73 sprite unici dai bbox OSM con parete sud regolare, lato in profondità, tetti coerenti, finestre 12 × 16 su griglia 38 × 46, balconi allineati e porte a livello strada.
- **Stazione Pianura ricostruita:** facciata 921 px dal perimetro OSM reale, tetto piano in lamiera, pensilina lato binari, colonne, vetrate e insegna EAV; ingresso e spawn spostati sulla banchina corretta.
- **Sprite professionali:** personaggi 16 × 32 px (4 direzioni × 4 frame), auto 72 × 40, bus 112 × 44, treno EAV 576 × 56, arredo urbano con metrica uniforme. Niente rotazione del treno visto di lato.
- **Interni ridisegnati:** stazione, bar, negozio e casa in pixel art coerente con la proiezione esterna.
- **UI rinnovata:** HUD e icone più leggibili, pannelli più ampi, touch target maggiori, dialoghi non invasivi.
- **Gameplay preservato:** 5 missioni, 8 NPC, traffico, treno, economia, inventario, salvataggi v4 con migrazione automatica dalla v3.
- **Qualità verificata:** validazione cartografica/asset, test end-to-end con screenshot reali e controllo visivo automatico in CI.

## Struttura

```
src/scenes/      BootScene, WorldScene
src/entities/    Player, NPC, Traffic
src/systems/     Input, Time, Save, Quest, Audio
src/world/       Collision, WorldLoader
src/ui/          UI HTML overlay
tools/           pipeline OSM, pixel art, audio, validazione e visual QA
docs/ART_SPEC.md contratto grafico vincolante della 0.3.0
data/osm/        risposta Overpass grezza + metadata
data/world/      mondo metrico convertito
public/assets/   tile, edifici, sprite, interni, audio
tests/           suite Playwright
screenshots/     screenshot e report dei test
```

## Piattaforme

- **Web:** link pubblico qui sopra, aggiornato da GitHub Actions.
- **Windows / macOS:** build statico Vite, imballabile in seguito con Electron/Tauri.
- **Android / iOS:** non ancora impacchettati; architettura pronta per Capacitor. Nessun APK o EXE è stato generato nella 0.3.0.

## Limitazioni note

Vedere `MAP_SOURCES.md` per le approssimazioni cartografiche, `docs/ART_SPEC.md` per il contratto grafico e `HANDOFF.md` per le attività pendenti. I test sono eseguiti in Chrome headless su Windows (emulazione), non su dispositivi fisici. L'analisi visiva automatica non sostituisce la revisione umana degli screenshot.
