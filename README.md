# NAPOLI LIFE — OpenCode Edition

Simulatore di vita open world in pixel art 2D ambientato nella **vera Pianura (Napoli)**,
con partenza dalla **stazione Circumflegrea**. Il mondo è costruito da dati OpenStreetMap
reali, non da una ricostruzione approssimata.

- **Versione corrente in locale:** 0.6.0 — "Pianura espansa": area rettangolare, veicoli, relazioni e POI reali (modifiche non ancora committate)
- **Ultima versione pubblicata e verificata:** 0.5.0 (tag `v0.5.0-stable`). Pubblicazione e verifica pubblica della 0.6.0 **da eseguire**
- **Link web:** <https://walkingbad10.github.io/napoli-life-opencode/>
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
piano sbagliato. La 0.6.0 mantiene Phaser Canvas 2D e il contratto dimensionale in
`docs/ART_SPEC.md`: l'area si espande solo con dati OSM reali e settori generati, senza
tracciati inventati né scala del motore.

## Avvio

```bash
npm install
npm run dev      # http://localhost:5173 (solo sviluppo locale)
```

Verifiche locali (su PowerShell non usare `npm run build` o `npm run test:*`: lo script
`npm.ps1` viene bloccato). Usare i comandi `node`/`python`:

```bash
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
python tools/validate_world.py
node tests/run-tests.mjs        # avvia da sé il preview su 127.0.0.1:4173
python tools/visual_qa.py
```

Il controllo del link pubblico è `node tests/verify-public.mjs`, da eseguire **dopo**
l'effettiva pubblicazione della 0.6.0.

Per rigenerare tutti gli asset dal mondo già salvato (nessuna API esterna a runtime):

```bash
python -m pip install pillow numpy pyproj shapely
python tools/convert_osm.py
python tools/render_reference.py
python tools/generate_world_tiles.py
python tools/generate_buildings.py
python tools/generate_sprites.py
python tools/generate_interiors.py
python tools/generate_audio.py
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
| Treno: guida manuale | frecce durante la corsa, E per scendere | pulsante interazione per scendere |
| Treno: viaggio passeggero | scelta "Viaggia come passeggero" in stazione | stessa scelta nel menu |
| Veicoli | pannello Veicoli per acquistare/guidare/rifornire, frecce per guidare, E per scendere | pulsanti del pannello Veicoli |
| Relazioni | pannello Relazioni: un regalo al giorno per persona | stesse icone |

Le icone sono piccole e i pannelli sono chiusi di default. Ruotando lo smartphone non avviene
alcun reload: la camera si adatta, il personaggio resta dove si trova e i progressi restano intatti.

## Cosa cambia nella 0.6.0

- **Area giocabile rettangolare:** `x [-256, 704]`, `y [-320, 704]` m (circa 960 × 1024 m), origine alla stazione `(0, 0)`, 240 settori da 64 m (15 × 16). Metrica invariata: 1 m = 16 px esterni, 48 px/m interni, `engine_scale = 1`.
- **Streaming del mondo:** `SectorStreamer` carica progressivamente un blocco 3 × 3 di settori attorno al giocatore, li mette in cache e scarica quelli lontani. I test registrano 4 settori caricati all'avvio e 9 dopo lo spostamento, su 240 totali.
- **OSM esteso:** dump `data/osm/pianura_expanded_20261126.json` (2591 elementi); i metadati della versione precedente restano in `data/osm/latest_v05.json`. Strade verificate: Via Nelson Mandela, Via Montagna Spaccata, Via Provinciale Napoli, Via Amedeo Modigliani, Via Pablo Picasso, Via Pallucci, Via Sartania, Via Nabucco, Via Giorgio De Chirico, Via San Josemaria Escrivà, Via Salvador Dalì.
- **Conteggi validati (70/70):** 410 elementi viari = 389 way stradali OSM + 21 elementi puntuali OSM (18 fermate, 2 stop, 1 semaforo); 14 binari Circumflegrea + 2 banchine; `rail_route` di 12 way OSM reali verso ovest e verso Montesanto, senza collegamenti inventati; 829 edifici tutti OSM; 129 POI reali più 2 POI fittizi esplicitamente dichiarati "Scommesse d'oro" (gialli, ancorati a `way/655446563` e `way/623181901`); 2 tabaccherie OSM; 50 landcover; 240 tile; 829 sprite edificio; 42 sprite; 11 interni; 20 audio.
- **POI reali notevoli:** Conad (128.6, 162.5), GoldBet (-217.9, 82.2), Eurobet (515.4, 406.7), Coop (372.4, 334.2) e (558.8, -57.4), Anema e Pane (243.0, 300.1), bar caffè (17.5, 142.9) e (255.9, 276.9), tabaccherie (391.9, -150.7) e (627.1, 408.3), edicole (424.7, -179.9) e (485.9, 24.6), mall (647.3, 337.1), McDonald's (646.0, 331.9), Vigili del Fuori Pianura e fermate bus presenti nel dump; nessun parcheggio è mappato nel rettangolo giocabile.
- **Nuovi sistemi:** `VehicleSystem` (acquisto, guida e rifornimento di auto e moto, carburante e collisioni), `SocialSystem` (amicizia, romance, regali una volta al giorno, livelli), porte ancorate ai POI e modalità passeggero EAV distinta dalla guida manuale del treno.
- **Compatibilità:** salvataggi v5 migrati a v6 in modo additivo con test E2E verde; nessun campo precedente rimosso. La 0.5.0 resta pubblicata con tag `v0.5.0-stable`: la storia della versione non è stata riscritta.
- **Verifiche locali reali:** `tsc --noEmit` OK, build Vite OK, `validate_world.py` 70/70, test end-to-end 64/64 con 0 errori console, `visual_qa.py` 85/85, 13 screenshot reali `screenshots/v0.6_*.png`. Lo screenshot desktop ha 297 colori, 0,00% nero e 16,63% bordi; portrait e landscape emulati senza reload. Ambiente: Chrome headless su Windows, non dispositivo fisico.
- **Da eseguire:** pubblicazione della 0.6.0 sul link GitHub Pages e relativa verifica pubblica. Il link qui sopra attualmente corrisponde alla 0.5.0 verificata.

## Struttura

```
src/scenes/      BootScene, WorldScene
src/entities/    Player, NPC, Traffic
src/systems/     Input, Time, Save, Needs, Business, Job, Quest, Audio, Vehicle, Social
src/world/       Collision, WorldLoader, SectorStreamer
src/ui/          UI HTML overlay (HUD bisogni, pannelli Vita/Veicoli/Relazioni)
tools/           pipeline OSM, pixel art, audio, validazione e visual QA
docs/ART_SPEC.md contratto grafico vincolante della 0.6.0
data/osm/        dump OSM esteso + metadati (latest_v05.json conservato)
data/world/      mondo metrico convertito (POI da way nominati inclusi)
public/assets/   240 tile, 829 sprite edificio, 42 sprite, 11 interni, 20 audio
tests/           suite Playwright locale e verifica link pubblico
screenshots/     13 screenshot v0.6 e report dei test
```

## Piattaforme

- **Web:** link pubblico qui sopra (verificato per la 0.5.0; aggiornamento alla 0.6.0 in attesa di pubblicazione).
- **Windows / macOS:** build statico Vite, imballabile in seguito con Electron/Tauri.
- **Android / iOS:** non ancora impacchettati; architettura pronta per Capacitor. Nessun APK o EXE generato.

## Limitazioni note

- Nessun test su dispositivi fisici Windows, Android, iOS o MacBook: solo emulazione browser e build web in Chrome headless su Windows.
- Nessun APK, EXE o app nativa Apple generata.
- Revisione visiva umana pendente: l'analisi multimodale locale con `qwen2.5vl:3b` non la sostituisce e nessuna immagine è uscita dal computer.
- Il tracciato ferroviario prosegue oltre l'area ricostruita: il viaggio passeggero si ferma al confine dei settori generati, senza collegamenti inventati.
- I 2 centri "Scommesse d'oro" sono esplicitamente fittizi, benché ancorati a edifici OSM reali.
- Alcune attività e uscite derivate da POI OSM senza orari dichiarati rispettano `BUSINESS_HOURS` simulati.
- Nessun parcheggio è mappato nel contatto immediato dell'area: non è stato inventato.
- Verifica pubblica della 0.6.0 da eseguire. Vedere `MAP_SOURCES.md`, `docs/ART_SPEC.md`, `HANDOFF.md` e `CHANGELOG.md` per dettagli e attività pendenti.
