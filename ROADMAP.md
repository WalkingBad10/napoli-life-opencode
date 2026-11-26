# ROADMAP.md

La regola rimane: **qualità prima dell'espansione**. Nessuna nuova zona verrà aggiunta fintanto che i test visivi e cartografici della zona precedente non saranno verdi.

## 0.3 — Ricostruzione grafica straordinaria (pubblicata)
- Proiezione obliqua a tre quarti tipo Stardew Valley; nessuna prospettiva isometrica improvvisata.
- Suolo generato a 16 px/m con `engine_scale = 1`: eliminate le ombre dure e i pixel doppi.
- Edifici ricostruiti da bbox OSM con facciate regolari, finestre allineate, balconi, tetti coerenti e porte a livello strada.
- Stazione Pianura ridisegnata dal riferimento fotografico fornito e dai dati OSM.
- Personaggi 16 × 32 px, veicoli e arredi ridisegnati con metrica uniforme; UI rinnovata.

## 0.4 — Pianura rifinita (pubblicata)
- Stazione corretta dalle fonti: due piani, tetto piano con aggetto, insegna "PIANURA", targa "DON GIUSTINO RUSSOLILLO"; pensilina rimossa perché OSM riporta `shelter=no`.
- 73 edifici rifiniti con cornici, marcapiani, portali napoletani, persiane, balconi e insegne coerenti con i tag OSM.
- Luci notturne ancorate alle finestre reali dei manifest, non a griglie approssimate.
- Suolo rigenerato con marciapiedi, cordoli, asfalto rattoppato, binari con traverse e banchine tattili; 26 sprite e interni rifatti.
- `docs/ART_SPEC.md` introdotto come contratto grafico vincolante; verifica pubblica sul link stabile.

## 0.5 — Simulatore di vita (pubblicata, tag `v0.5.0-stable`)
- Tempo, bisogni, orari commerciali simulati, lavoro retribuito e audio a zone.
- Abitazione personalizzabile con arredo persistente; quinto interno `pizzeria` ancorato al POI OSM Carpe Diem.
- Treno EAV guidabile con biglietto valido 90 minuti; salvataggio v5 con migrazione additiva da v4.
- Pubblicata e verificata sul link GitHub Pages: 11/11 controlli pubblici, nessuna storia riscritta.
- Ancora da fare, spostato alle milestone successive: amicizie e relazioni (realizzate nella 0.6.0), veicoli guidabili (realizzati nella 0.6.0), abbigliamento completo e animali domestici.

## 0.6 — Pianura espansa (pubblicata e verificata)
- Area rettangolare `x [-256, 704]`, `y [-320, 704]` m (circa 960 × 1024 m), 240 settori da 64 m (15 × 16), origine alla stazione; 1 m = 16 px esterni, 48 px/m interni, `engine_scale = 1`.
- `SectorStreamer`: caricamento progressivo 3 × 3 settori, cache e scarico; 240 tile e 829 sprite edificio da OSM.
- Dump OSM esteso a 2591 elementi con strade verificate, 410 elementi viari, 14 binari, 2 banchine e 12 way `rail_route` reali senza collegamenti inventati.
- 129 POI reali + 2 POI fittizi dichiarati "Scommesse d'oro"; 50 landcover; 2 tabaccherie OSM; 11 interni, 42 sprite, 20 audio.
- `VehicleSystem` (auto e moto, carburante e collisioni), `SocialSystem` (amicizia/romance, regali una volta al giorno, livelli), porte POI-ancorate e viaggio passeggero EAV distinto dalla guida manuale.
- Salvataggio v6 con migrazione additiva da v5; 70/70 validazioni, 64/64 test end-to-end, 85/85 controlli visivi, 13 screenshot reali in Chrome headless su Windows.
- Pubblicata e verificata: commit `221b5ab`, tag `v0.6.0-stable`, CI `45890587139` e Deploy `45890587057` verdi, 14/14 controlli pubblici con screenshot `screenshots/v0.6_public_link.png`. Nessun test su dispositivi fisici e revisione visiva umana ancora pendenti.

## 0.7 — Beta multipiattaforma (da fare)
- EXE Windows, APK Android (Capacitor), ottimizzazione web e test su dispositivi reali.
- Telemetria delle prestazioni anonima e locale (nessun account), solo se esplicitamente autorizzata.
- Verifica Codespaces e sviluppo da smartphone.

## 1.0 — Espansione di Pianura
- Fermata Trencia e Bar Etoile **solo previa verifica dei riferimenti**, nuove attività commerciali reali da OSM.
- Via Provinciale Napoli è già presente nel dump verificato della 0.6.0: non è più un obiettivo futuro.
- Nuove zone solo oltre il confine dei settori generati, con estrazione OSM documentata e viaggio passeggero esteso senza tracciati inventati.

## Dopo la 1.0 (ordine di priorità)
Montesanto → Centro Storico / Piazza del Gesù Nuovo → Fuorigrotta / Stadio Maradona → Vomero → Mergellina / Lungomare / Villa Comunale → Posillipo / Parco Virgiliano → Bacoli / Miseno / Miliscola / Fusaro / Lucrino / Torregaveta → Avellino / Caserta / Salerno.

Ogni espansione richiederà: nuova estrazione OSM documentata, nuovi sprite originali, test visivi e un link pubblico aggiornato.
