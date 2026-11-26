# HANDOFF.md — continuità tra sessioni

Ultimo aggiornamento: 2026-11-26 · versione **0.4.0** · branch `main`

## Stato reale del progetto

| Elemento | Valore verificato |
|---|---|
| Cartella | `C:\Users\rocka\Documents\Progetto predefinito\napoli-life-opencode` |
| Repository | `https://github.com/WalkingBad10/napoli-life-opencode` (pubblico) |
| Link giocabile | `https://walkingbad10.github.io/napoli-life-opencode/` |
| Backup 0.2.0 | tag `v0.2.0-stable` e branch `backup-v0.2.0` |
| Backup 0.3.0 | tag `v0.3.0-stable` e branch `backup-v0.3.0` |
| Commit grafica 0.3 | `8743e63` (`v0.3.0: ricostruzione grafica straordinaria di Pianura`) |
| Commit 0.4 | `a76d34a` (`v0.4.0: rifinisci Pianura, stazione verificata e QA visiva locale`) |
| Motore | Phaser 3.90, TypeScript, Vite, renderer Canvas 2D (confermato) |
| Dati | OpenStreetMap catturati il 2026-11-26, 2651 elementi, salvati nel repo |
| Test locali | 30/30 funzionali, 26/26 cartografici/asset, 27/27 visivi, 0 errori console |
| Test link pubblico | 8/8 su browser reale, HTTP 200, versione 0.4.0, movimento attivo, 0 errori console |
| Test CI | workflow `CI` (`45881687133`) e `Deploy` (`45881687048`) entrambe `success` |

## Cosa è stato fatto davvero nella 0.4.0

- [x] Ricerca verificabile sulla stazione reale in `docs/reference/station_research.md` (OSM, Wikidata, Wikipedia, EAV, stampa locale); fatti distinti da ipotesi.
- [x] Analisi visiva locale con Ollama `qwen2.5vl:3b` e `tools/ollama_vision.py`: nessuna immagine è uscita dal computer, nessuna foto copiata negli asset.
- [x] Stazione corretta: due piani, tetto piano con aggetto, insegna "PIANURA" e targa "DON GIUSTINO RUSSOLILLO" in font bitmap, due murales originali; **pensilina rimossa** perché `shelter=no` su entrambe le banchine.
- [x] 73 edifici rifiniti con cornici, portali, persiane, balconi, gronde, terrazze e insegne da tag OSM; `windows` nel manifest per luci notturne sulle finestre vere.
- [x] Suolo rigenerato con marciapiedi 1,5/2 m, asfalto regolare, linee tratteggiate solo sulle strade maggiori, binari/banchine tattili e recinzioni con montanti.
- [x] 26 sprite e quattro interni rifatti a mano; bar napoletano riconoscibile, spawn e collider invariati.
- [x] `docs/ART_SPEC.md`, `docs/VISUAL_QA.md`, `CHANGELOG.md`, `PROGRESS.md`, `ASSET_GUIDE.md`, `MAP_SOURCES.md`, README aggiornati.
- [x] Build, 30/30 test end-to-end, 26/26 validazioni, 27/27 controlli visivi; sei screenshot reali v0.4 in `screenshots/`.

## Cosa NON è ancora stato fatto

- [x] Pubblicazione 0.4 e verifica finale del link pubblico/browser reale: 8/8 controlli, screenshot `v0.4_public_link.png`.
- [ ] Test su dispositivi fisici: Pixel 9 Pro XL, MacBook M1 8 GB, iPhone, Windows nativo.
- [ ] APK, EXE, app Apple: non generati. Architettura pronta per Capacitor ma non configurata.
- [ ] Revisione visiva umana degli screenshot: l'analisi locale con modello multimodale non la sostituisce.
- [ ] Conferma fotografica definitiva di piani/colori della stazione e delle targhe 2020.
- [ ] Foto verificate per livrea del treno e interni EAV reali.
- [ ] Codespace aperto e usato davvero dal browser con account GitHub.

## Approssimazioni da ricordare

Vedere `MAP_SOURCES.md`, `docs/ART_SPEC.md` e `docs/reference/station_research.md`. La geometria di strade, binari, banchine e perimetri è reale e deriva da OSM (© OpenStreetMap contributors, ODbL 1.0). Sono ricostruzioni artistiche originali: altezze degli edifici, finestre/balconi/tegole, livrea del treno, arredi interni, dialoghi NPC, arredo urbano e murales. I due piani della stazione e il tetto piano sono ipotesi supportate dall'analisi visiva locale, non dati OSM verificati.

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
Non ampliare la mappa prima che Pianura sia rifinita: la prossima priorità è la conferma visiva umana della 0.4.0, non la quantità di zone.
