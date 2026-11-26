# NAPOLI LIFE — OpenCode Edition

Simulatore di vita open world in pixel art 2D ambientato nella **vera Pianura (Napoli)**,
con partenza dalla **stazione Circumflegrea**. Il mondo è costruito da dati OpenStreetMap
reali, non da una ricostruzione approssimata.

- **Versione corrente:** 0.5.0 — "Vita a Pianura": routine, negozi, lavoro, casa e treno guidabile
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

Il difetto storico della 0.2.0 non era il motore ma la **pipeline grafica**: suolo a 8 px/m
scalato 2× dal motore, sprite fuori metrica, ombre poligonali dure e finestre disegnate al
piano sbagliato. La 0.5.0 mantiene Phaser Canvas 2D e irrobustisce la vita quotidiana senza
modificare la geometria OSM né il contratto dimensionale in `docs/ART_SPEC.md`.

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

Per rigenerare tutti gli asset dal mondo già salvato (nessuna API esterna a runtime):

```bash
python -m pip install pillow numpy pyproj shapely
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
| Treno: accelerare/frenare | frecce durante la corsa | pulsante interazione per scendere |

Le icone sono piccole e i pannelli sono chiusi di default. Ruotando lo smartphone non avviene
alcun reload: la camera si adatta, il personaggio resta dove si trova e i progressi restano intatti.

## Cosa cambia nella 0.5.0

- **Vita quotidiana non invasiva:** sazietà ed energia calano lentamente, il riposo al letto ripristina l'energia e avanza l'orologio; cibi e bevande dell'inventario si consumano dal pannello 🎒. Nessuna barra ingombrante: due meter sottili nell'HUD.
- **Orari commerciali simulati:** stazione 05:30–23:30, bar 07:00–21:00, negozio 08:00–20:00, Carpe Diem 11:00–22:30. OSM non riporta `opening_hours`, quindi gli orari sono ricostruzioni esplicite e documentate.
- **Pizzeria Carpe Diem:** quinto interno ancorato al POI OSM `way/655446533`, con forno a legna, pizzaiolo, banco pizze e menu; bread e bevande acquistabili, pizza al taglio a € 4,50.
- **Lavoro retribuito:** turni al bar (3 espressi, € 12) e in pizzeria (3 pizze, € 18); contatore `jobs` e salvataggio dei progressi.
- **Abitazione personalizzabile:** acquisto di libreria e pianta, persistenti nel salvataggio; armadio interattivo in casa.
- **Treno EAV guidabile:** con biglietto valido (90 min) si sale in banchina, si accelera/frena con le frecce e si scende registrando il viaggio. Il percorso segue i binari OSM reali.
- **Audio di zona:** sei loop ambientali (ambience, music, birds, night, crowd, bar_murmur) e otto nuovi effetti (cash, eat, sleep, ui inclusi), tutti sintetizzati originalmente.
- **Asset originali aggiunti:** sprite `pizzaiolo`, `pizza`, `coffee_cup`, `bookshelf`, `plant`; interni `pizzeria`; audio; manifest versione 0.5 con metadati coerenti. Nessun asset copiato.
- **Compatibilità:** salvataggi v4 migrati a v5 senza perdite; API test `window.__napoli` additive (`setTime`, `setNeeds`, `setMoney`, `teleportRoom`, `interact`, `boardTrain`, `setTrain`, `audioState`).
- **Qualità verificata in locale:** build OK, 26/26 validazioni cartografiche, 53/53 test end-to-end, 56/56 controlli visivi, zero errori console, dieci screenshot reali v0.5 e analisi locale con `qwen2.5vl:3b`.

## Struttura

```
src/scenes/      BootScene, WorldScene
src/entities/    Player, NPC, Traffic
src/systems/     Input, Time, Save, Needs, Business, Job, Quest, Audio
src/world/       Collision, WorldLoader
src/ui/          UI HTML overlay (HUD bisogni, pannello Vita)
tools/           pipeline OSM, pixel art, audio, validazione e visual QA
docs/ART_SPEC.md contratto grafico vincolante della 0.5.0
data/osm/        risposta Overpass grezza + metadata
data/world/      mondo metrico convertito (POI da way nominati inclusi)
public/assets/   tile, edifici, sprite, interni, audio
tests/           suite Playwright locale e verifica link pubblico
screenshots/     screenshot e report dei test
```

## Piattaforme

- **Web:** link pubblico qui sopra, aggiornato da GitHub Actions.
- **Windows / macOS:** build statico Vite, imballabile in seguito con Electron/Tauri.
- **Android / iOS:** non ancora impacchettati; architettura pronta per Capacitor. Nessun APK o EXE è stato generato nella 0.5.0.

## Limitazioni note

Gli orari commerciali sono simulati (il dump OSM non contiene `opening_hours`). I test sono
eseguiti in Chrome headless su Windows con emulazione viewport, non su dispositivi fisici.
L'analisi visiva automatica e il modello multimodale locale non sostituiscono la revisione
umana. Vedere `MAP_SOURCES.md`, `docs/ART_SPEC.md` e `HANDOFF.md` per dettagli e attività pendenti.
