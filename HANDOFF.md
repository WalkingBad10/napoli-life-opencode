# HANDOFF.md — continuità tra sessioni

Ultimo aggiornamento: 2026-11-26 · versione **0.3.0** · branch `main`

## Stato reale del progetto

| Elemento | Valore verificato |
|---|---|
| Cartella | `C:\Users\rocka\Documents\Progetto predefinito\napoli-life-opencode` |
| Repository | `https://github.com/WalkingBad10/napoli-life-opencode` (pubblico) |
| Link giocabile | `https://walkingbad10.github.io/napoli-life-opencode/` |
| Backup 0.2.0 | tag `v0.2.0-stable` e branch `backup-v0.2.0` |
| Commit grafica | `8743e63` (`v0.3.0: ricostruzione grafica straordinaria di Pianura`) |
| Commit documentazione | vedere `git log -1` dopo l'ultimo push |
| Motore | Phaser 3.90, TypeScript, Vite, renderer Canvas 2D (scelta confermata dopo valutazione) |
| Dati | OpenStreetMap catturati il 2026-11-26, 2651 elementi, salvati nel repo |
| Test locali | 30/30 funzionali, 26/26 cartografici/asset, 18/18 visivi, 0 errori console |
| Test link pubblico | 8/8 su browser reale, HTTP 200, versione 0.3.0, movimento attivo |
| Test CI | workflow `CI` (`45870223405`) e `Deploy` (`45870223066`) entrambe `success` |

## Cosa è stato fatto davvero

- [x] Versione 0.2.0 preservata con tag e branch dedicati prima di qualsiasi modifica.
- [x] Analisi della fotografia fornita e diagnosi delle cause tecniche: suolo a 8 px/m scalato 2×, ombre poligonali dure, finestre al piano sbagliato, sprite fuori metrica, treno ruotato, stazione con ingresso sul lato sbagliato.
- [x] Scritto il contratto grafico vincolante `docs/ART_SPEC.md` e il registro iterazioni `docs/VISUAL_QA.md`.
- [x] Suolo rigenerato a 16 px/m (36 settori 1024 × 1024) e `setScale(2)` rimosso dal motore.
- [x] 73 edifici ricostruiti come volumi architettonici dai bbox OSM, con manifest contenente origini e griglia piani.
- [x] Stazione Pianura ridisegnata: facciata 921 px, tetto piano, pensilina, vetrate, insegna EAV; spawn e porta spostati sulla banchina.
- [x] Sprite e interni rigenerati con metrica uniforme; bar/negozio/casa ancorati a edifici OSM reali.
- [x] Salvataggi migrati alla v4: chi aveva lo spawn vecchio viene riportato sulla banchina senza perdere progressi.
- [x] UI ridimensionata e resa più leggibile; touch target maggiori.
- [x] Aggiunto `tools/visual_qa.py` e relativi controlli nella CI.
- [x] Build, test locali, controllo visivo, CI e deploy pubblicati con successo.
- [x] Link pubblico sullo stesso indirizzo della 0.2.0 verificato con 8/8 controlli e screenshot `v0.3_public_link.png`.

## Cosa NON è ancora stato fatto

- [ ] Test su dispositivi fisici: Pixel 9 Pro XL, MacBook M1 8 GB, iPhone, Windows nativo.
- [ ] APK, EXE, app Apple: non generati. Architettura pronta per Capacitor ma non configurata.
- [ ] Revisione visiva umana degli screenshot da parte del committente: il modello non supporta input immagine, quindi l'analisi è programmatica (palette, bordi, luminosità, ombre nere).
- [ ] Foto di riferimento EAV verificate per livrea del treno e interni reali.
- [ ] Codespace aperto e usato davvero dal browser con account GitHub.

## Approssimazioni da ricordare

Vedere `MAP_SOURCES.md` e `docs/ART_SPEC.md`. La geometria di strade, binari, banchine e perimetri è reale e deriva da OSM (© OpenStreetMap contributors, ODbL 1.0). Sono ricostruzioni artistiche originali: altezze edili, finestre/balconi/tegole, livrea del treno, arredi interni, dialoghi NPC e posizionamento dell'arredo urbano. La stazione usa la fotografia fornita solo come riferimento visivo: nessun pixel della foto è stato copiato.

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
Non ampliare la mappa prima che Pianura sia rifinita: la prossima priorità è la conferma visiva umana della 0.3.0, non la quantità di zone.
