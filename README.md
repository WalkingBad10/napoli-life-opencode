# NAPOLI LIFE — OpenCode Edition

Simulatore di vita open world in pixel art 2D ambientato nella **vera Pianura (Napoli)**,
con partenza dalla **stazione Circumflegrea**. Il mondo è costruito da dati OpenStreetMap
reali, non da una ricostruzione approssimata.

- **Versione corrente:** 0.2.0
- **Link web giocabile:** <https://walkingbad10.github.io/napoli-life-opencode/>
- **Repository:** <https://github.com/WalkingBad10/napoli-life-opencode>
- **Licenza dati:** © OpenStreetMap contributors, ODbL 1.0
- **Grafica/audio:** originali, generati proceduralmente da `tools/`

## Perché Phaser 3 e non Godot

La versione web doveva essere giocabile fin dal primo aggiornamento e rimanere identica su
Windows, Android, browser e (in seguito) Apple. Phaser 3 + TypeScript + Vite offre un unico
renderer 2D Canvas, build statico immediatamente pubblicabile su GitHub Pages, touch e gamepad
nativi e la possibilità di incapsulare lo stesso build in Capacitor per APK. Godot 4 non era
installato e l'export web richiede template aggiuntivi; usare entrambi i motori avrebbe
duplicato gli asset senza vantaggi qualitativi.

## Avvio

```bash
npm install
npm run dev      # http://localhost:5173 (solo sviluppo locale)
npm run build    # produce dist/
npm run preview  # verifica del build
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

## Cosa c'è nella 0.2.0

- Mondo 300 × 300 m intorno alla stazione con 73 edifici reali, 96 tratti stradali, 11 segmenti ferroviari, 2 banchine, parcheggi, aree verdi e POI da OSM.
- Fabbricato viaggiatori con insegne EAV, vetrate e pensilina; binari, recinzioni e treno EAV a due casse.
- Movimento a 8 direzioni, corsa, collisioni vettoriali sui perimetri reali, profondità con punto-piedi.
- Quattro interni accessibili: stazione, bar napoletano, negozio, abitazione.
- 8 NPC con routine, dialoghi e popolazione variabile per fascia oraria; traffico automobilistico e treno.
- 5 missioni funzionanti (caffè, biglietto, pacco, chiavi smarrite, lavoretto retribuito) con diario.
- Economia, inventario, salvataggi manuali/automatici con migrazioni, import/export, nessun account.
- Ciclo giorno/notte, illuminazione delle finestre, audio ambientale e colonna sonora originali.
- Test Playwright con 25 controlli e 4 screenshot reali in `screenshots/`.

## Struttura

```
src/scenes/      BootScene, WorldScene
src/entities/    Player, NPC, Traffic
src/systems/     Input, Time, Save, Quest, Audio
src/world/       Collision, WorldLoader
src/ui/          UI HTML overlay
tools/           pipeline OSM, pixel art, audio, validazione
data/osm/        risposta Overpass grezza + metadata
data/world/      mondo metrico convertito
public/assets/   tile, edifici, sprite, interni, audio
tests/           suite Playwright
screenshots/     screenshot e report dei test
```

## Piattaforme

- **Web:** link pubblico qui sopra, aggiornato da GitHub Actions.
- **Windows / macOS:** build statico Vite, imballabile in seguito con Electron/Tauri.
- **Android / iOS:** non ancora impacchettati; architettura pronta per Capacitor. Nessun APK o EXE è stato generato nella 0.2.0.

## Limitazioni note

Vedere `MAP_SOURCES.md` per le approssimazioni cartografiche e `HANDOFF.md` per le attivitàpendenti. I test sono stati eseguiti in Chrome headless su Windows (emulazione), non su dispositivi fisici.
