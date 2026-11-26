# CHANGELOG.md

## 0.3.0 — 2026-11-26 — "Ricostruzione grafica straordinaria"

- Versione 0.2.0 preservata con tag `v0.2.0-stable` e branch `backup-v0.2.0`; nessun progetto esistente toccato.
- Aggiunto `docs/ART_SPEC.md`: proiezione obliqua a tre quarti tipo Stardew Valley, metrica 1 m = 16 px, regole vincolanti per edifici, suolo, sprite e profondità.
- Suolo rigenerato direttamente a 16 px/m (36 settori 1024 × 1024); rimosso `setScale(2)`, bande chiare centrali, giunti arrotondati e ombre poligonali sfalsate.
- 73 edifici ricostruiti come volumi architettonici dai bbox OSM: finestre 12 × 16 su griglia 38 × 46, porte al livello strada, balconi allineati, tetti regolari e manifest con origini corrette.
- Fabbricato viaggiatori di Pianura ridisegnato dalla fotografia fornita e dai dati OSM: facciata 921 px, pensilina metallica, vetrate, colonne e insegna EAV; spawn e ingresso spostati sulla banchina reale.
- Sprite originali ridisegnati: personaggi 16 × 32 px, auto 72 × 40, bus 112 × 44, treno EAV 576 × 56, arredo urbano coerente; nessuna rotazione del treno visto di lato.
- Interni ridisegnati in pixel art coerente e ancorati a edifici OSM reali; bar, negozio e casa non sono più posizionati dentro il fabbricato viaggiatori.
- UI ridimensionata: HUD e icone più leggibili, pannelli più ampi, pulsanti touch maggiori.
- Salvataggi migrati alla versione 4: gli spawn vecchi vengono riportati sulla banchina senza perdere progressi.
- Aggiunti `tools/visual_qa.py` e il confronto quantitativo tra screenshot v0.2 e v0.3 in `docs/VISUAL_QA.md`.
- Verifiche: build OK, 26 controlli cartografici/asset, 30 test end-to-end, 18 controlli visivi, 0 errori console.
- Pubblicazione sullo stesso link GitHub Pages: CI e Deploy verdi (run `45870223405` / `45870223066`), verifica pubblica 8/8 (HTTP 200, versione 0.3.0, movimento attivo, palette ricca, zero errori).

## 0.2.0 — 2026-11-26 — "Pianura"

- Mondo giocabile da 300 × 300 m costruito da OSM: stazione Circumflegrea, binari, banchine, Via Nelson Mandela e condomini reali.
- Fabbricato viaggiatori con insegne EAV, vetrate, colonne e pensilina.
- Treno EAV a due casse, traffico stradale e 8 residenti con routine e dialoghi.
- Quattro interni accessibili (stazione, bar, negozio, abitazione) con arredi e commercianti.
- Cinque missioni complete con diario, ricompense e salvataggio dei progressi.
- Salvataggi versionati con migrazioni, esportazione e importazione; nessun account richiesto.
- Giorno/notte, finestre illuminate, audio ambientale e colonna sonora originali.
- Touch, gamepad, rotazione senza reload, menu a icone discrete.
- Test automatici: 25 controlli funzionali + 19 controlli cartografici, screenshot in `screenshots/`.
- CI e pubblicazione GitHub Pages tramite GitHub Actions; link pubblico verificato con 6/6 controlli su browser reale (HTTP 200, versione 0.2.0, movimento attivo, zero errori console).

## 0.1.0 — fondamenta (inclusa nella 0.2.0, non pubblicata separatamente)

- Configurazione strumenti, motore, repository, movimento, telecamera, collisioni, salvataggi e comandi touch.
