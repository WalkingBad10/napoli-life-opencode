# HANDOFF.md — continuità tra sessioni

Ultimo aggiornamento: 2026-11-26 · versione **0.2.0** · branch `main`

## Stato reale del progetto

| Elemento | Valore verificato |
|---|---|
| Cartella | `C:\Users\rocka\Documents\Progetto predefinito\napoli-life-opencode` |
| Repository | `https://github.com/WalkingBad10/napoli-life-opencode` (pubblico) |
| Link giocabile | `https://walkingbad10.github.io/napoli-life-opencode/` |
| Commit | `e11d24e` + commit finale di documentazione (vedi `git log -1`) |
| Motore | Phaser 3.90, TypeScript, Vite, renderer Canvas 2D |
| Dati | OpenStreetMap catturati il 2026-11-26, 2651 elementi, salvati nel repo |
| Test locali | 25/25 funzionali, 19/19 cartografici, 0 errori console |
| Test link pubblico | 6/6 su browser reale, HTTP 200, versione 0.2.0, movimento attivo |
| Test CI | workflow `CI` e `Deploy` entrambe `success` (run `45859084662` / `45859084655`) |

## Cosa è stato fatto davvero

- [x] Acquisizione OSM reale tramite mirror Overpass `maps.mail.ru` e conversione UTM 33N.
- [x] Mondo 300 × 300 m: 96 strade, 73 edifici reali, 11 binari, 2 banchine, 12 POI.
- [x] Pixel art e audio originali generati da `tools/` (36 tile, 73 edifici, 7 personaggi, 4 interni, 6 tracce).
- [x] Gameplay: movimento, collisioni, interazioni, 5 missioni, 4 interni, 8 NPC, traffico, treno, giorno/notte.
- [x] Salvataggi versionati v3 con migrazioni, import/export, nessun login.
- [x] UI a icone, pannelli chiusi, touch/gamepad, rotazione senza reload.
- [x] Build di produzione funzionante, screenshot reali in `screenshots/`.
- [x] Git inizializzato, repository creato, push effettuato, workflow CI e Pages configurate.
- [x] GitHub Pages abilitato via API (`POST /pages`, `build_type=workflow`) e deployment riuscito.
- [x] Link pubblico verificato con `npm run test:public`: 6/6 controlli, screenshot `v0.2_public_link.png`.

## Cosa NON è ancora stato fatto

- [ ] Test su dispositivi fisici: Pixel 9 Pro XL, MacBook M1 8 GB, iPhone, Windows nativo.
- [ ] APK, EXE, app Apple: non generati. Architettura pronta per Capacitor ma non configurata.
- [ ] Verifica visiva umana degli screenshot da parte del modello (non supporta input immagine): i controlli sono programmatici.
- [ ] Foto di riferimento EAV verificate per livrea del treno e interni reali.
- [ ] Codespace aperto e usato davvero dal browser con account GitHub.

## Approssimazioni da ricordare

Vedere `MAP_SOURCES.md` per l'elenco completo. Le principali: livrea del treno EAV e interni ricostruiti proceduralmente, altezze edili stimate da `building:levels`, arredi urbani posizionati sui marciapiedi in modo automatico. **La geometria di strade, binari e perimetri è reale e deriva da OSM.**

## Come riprendere il lavoro

```bash
cd "C:\Users\rocka\Documents\Progetto predefinito\napoli-life-opencode"
git pull
npm install
npm run build
npm run test:e2e
python tools/validate_world.py
```

Dopo ogni modifica: aggiornare `PROGRESS.md`, `CHANGELOG.md`, `HANDOFF.md`, fare commit e push.
Verificare sempre che i workflow `.github/workflows/ci.yml` e `deploy.yml` siano verdi prima di dichiarare la versione stabile.

## Regola per la prossima sessione

Leggere `AGENTS.md` **prima** di toccare qualsiasi file. Non modificare progetti esistenti.
Non ampliare la mappa prima che Pianura sia rifinita: la prossima priorità è la qualità visiva, non la quantità di zone.
