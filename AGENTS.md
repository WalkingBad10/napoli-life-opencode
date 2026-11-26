# AGENTS.md — direttive permanenti di NAPOLI LIFE — OpenCode Edition

Questo file vale per ogni agente AI, dispositivo o ambiente cloud che lavora al progetto.
Leggerlo **prima** di toccare qualsiasi file.

## Direttive assolute

1. FEDELTÀ GEOGRAFICA PRIMA DI TUTTO. Le strade, i perimetri e i binari derivano da OpenStreetMap già salvato in `data/osm/` e convertito in `data/world/pianura_world.json`. Non inventare conformazioni stradali.
2. QUALITÀ PRIMA DELLA QUANTITÀ. Una strada riconoscibile vale più di dieci strade approssimate.
3. DETTAGLIO PRIMA DELL'ESPANSIONE. Non aggiungere nuove zone prima che Pianura sia rifinita.
4. PROPORZIONI REALISTICHE. Standard unico: **1 metro = 16 pixel** nel mondo; 48 px/m negli interni.
5. ASSET ORIGINALI. Tutta la grafica e l'audio sono generati dal codice in `tools/`. Non copiare asset di Stardew Valley o di altri giochi.
6. LINK PUBBLICO DOPO OGNI AGGIORNAMENTO STABILE. Pubblicare su GitHub Pages e verificare il link.
7. CONTINUITÀ WINDOWS / SMARTPHONE / CLOUD. Ogni sessione significativa termina con commit, push, documentazione aggiornata e HANDOFF.md pronto.

## Cosa NON fare

- Non modificare `bacoli-life`, `campania-life`, `campania-codex`, `campania-open-code-1`, `napoli-life-pixel-edition` o altri progetti esistenti.
- Non agganciarsi a API esterne durante il gameplay: i dati sono già nel repository.
- Non inserire token, credenziali o chiavi nel repository.
- Non attivare servizi a pagamento senza autorizzazione esplicita.
- Non dichiarare complete attività non eseguite (es. APK, EXE, test su dispositivi reali).

## Architettura

- **Un solo motore**: Phaser 3.90 + TypeScript + Vite, renderer Canvas 2D (compatibilità universale, anche browser headless e mobile).
- Nessun secondo motore grafico: Godot non è installato e la sua export web richiederebbe template dedicati; Phaser permette il link giocabile subito. Capacitor potrà avvolgere lo stesso build web per Android/iOS in seguito.
- Dati cartografici: Overpass → `data/osm/` → `tools/convert_osm.py` → `data/world/` + copia runtime in `public/data/world/`.
- Generazione asset: `tools/generate_*.py` (Pillow, numpy, pyproj, shapely). Rigenerare con `npm run assets`.
- Logica di gioco: `src/scenes/` (Boot, World), `src/entities/`, `src/systems/`, `src/ui/`, `src/world/`.

## Comandi standard

```bash
npm install
npm run build          # tsc --noEmit && vite build
npm run test:e2e       # Playwright + screenshot in screenshots/
python tools/validate_world.py
npm run dev            # server locale solo per sviluppo
```

Workflow di pubblicazione: `.github/workflows/ci.yml` (validazione + build) e
`.github/workflows/deploy.yml` (GitHub Pages). Link stabile:
`https://walkingbad10.github.io/napoli-life-opencode/`.

## Regole per nuove zone

1. Scaricare nuovi dati con `tools/fetch_osm.py` (modificando la bbox) e ricordare l'attribuzione in `MAP_SOURCES.md`.
2. Riconvertire, rigenerare solo gli asset interessati, aggiornare `ASSET_GUIDE.md` se cambiano le proporzioni.
3. Aggiungere test visivi e aggiornare `PROGRESS.md`, `CHANGELOG.md`, `HANDOFF.md`.
4. Non ampliare l'area finché i controlli di Pianura non sono verdi.

## Stato corrente

Versione 0.2.0 — vedere `PROGRESS.md` e `HANDOFF.md` per dettagli e attività pendenti.
