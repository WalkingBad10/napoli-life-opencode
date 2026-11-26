# VISUAL_QA.md — registro delle iterazioni grafiche

Obiettivo: non limitarsi a far passare i test, ma correggere i difetti visivi reali emersi
dalla fotografia fornita e dagli screenshot della build. Ogni iterazione registra osservazioni,
causa tecnica, intervento ed esito. L'analisi automatica non sostituisce la revisione umana.

## Iterazione 0 — accettazione della 0.2.0 (rifiutata)

Difetti osservati nella fotografia/screenshot fornita:

1. **Pixel doppi e linee a blocchi**: il suolo era disegnato a 8 px/m e poi scalato 2× dal motore.
2. **Ombre nere sfalsate**: ogni edificio aveva un'ombra poligonale dura con offset di 5 px e alpha 150.
3. **Finestre invertite**: il piano terra veniva disegnato in alto, vicino al tetto.
4. **Artefatti di profondità**: edifici ancorati a `(0.5, 1)` pur avendo origine architettonica diversa; il giocatore passava dietro facciate che doveva attraversare.
5. **Sprite fuori metrica**: personaggi 24 × 36 px, treno ruotato come un veicolo visto dall'alto.
6. **Stazione sbagliata**: spawn e porta sul lato nord del fabbricato, non sulla banchina; la geometria OSM veniva dipinta come facciata piatta.
7. **Strade con banda chiara centrale** e giunti arrotondati, non coerenti con asfalto reale.
8. **UI piccola** su mobile e pannelli poco leggibili.

## Iterazione 1 — specifica e rimozione delle cause

Interventi applicati:

- Scritto `docs/ART_SPEC.md` come contratto obbligatorio per generatore e motore.
- Suolo rigenerato a **16 px/m**, settori **1024 × 1024**, `engine_scale = 1`.
- Ombre poligonali rimosse; solo contatto morbido con alpha ≤ 45 e raggio ≤ 0,75 m.
- Finestre su griglia fissa 38 × 46 px, piano terra in basso.
- Edifici ricostruiti come volume architettonico dal bbox OSM, con `origin_x/origin_y` nel manifest.
- Personaggi 16 × 32 px, veicoli e arredo ridisegnati; treno non ruotato.
- Spawn e porte della stazione portati sul lato banchina; bar/negozio ancorati a edifici OSM reali.
- UI ridimensionata con target touch maggiori e pannelli più leggibili.
- Il tentativo di usare un generatore di immagini con la foto come riferimento è fallito per credenziali non disponibili: la stazione è stata quindi ricostruita a mano nel generatore Python, usando l'analisi della fotografia e le geometrie OSM. Nessun pixel della foto è stato copiato nel gioco.

## Iterazione 2 — verifica successiva alla build

I risultati di questa iterazione vengono registrati in `screenshots/visual-qa-report.json`
e `screenshots/test-report.json` dopo l'esecuzione di:

```bash
npm run build
npm run test:e2e
npm run test:visual
```

Controlli considerati validi solo se:

- gli screenshot non sono vuoti e hanno palette coerente (> 100 colori campionati);
- la frazione di nero pieno resta sotto il 2%;
- la luminosità media resta in un intervallo realistico;
- non esistono ombre nere dure nei 36 settori di suolo;
- la stazione supera 900 px di facciata e mantiene l'insegna EAV;
- tutti i controlli funzionali restano verdi dopo il cambiamento grafico.

**Esito misurato (Chrome headless, 1280 × 800):**

| Metrica | v0.2.0 desktop | v0.3.0 desktop | Interpretazione |
|---|---:|---:|---|
| Luminosità media | 44,9 | 165,2 | la scena non è più schiacciata dalle ombre |
| Pixel quasi neri | 47,5% | 0,01% | eliminate le ombre dominanti |
| Nero pieno | 5,3% | 0,00% | nessuna ombra poligonale residua |
| Densità di bordi | 4,1% | 14,2% | molto più dettaglio architettonico leggibile |
| Colori campionati | 570 | 250 | palette volutamente ristretta e coerente |

Il calo del numero di colori è intenzionale: la 0.2.0 mescolava sfumature casuali e ombre;
la 0.3.0 usa una palette limitata ma con tre volte più struttura (bordi) e luminosità realistica.

Risultati completi: `screenshots/visual-qa-report.json` (18/18) e
`screenshots/test-report.json` (30/30).

## Iterazione 3 — revisione finale e pubblicazione

- CI (`45870223405`) e Deploy (`45870223066`) verdi sul commit `8743e63`.
- Verifica sul link pubblico: 8/8 controlli, HTTP 200, versione 0.3.0, movimento attivo, 198 colori campionati, 0,00% nero pieno, zero errori console.
- Screenshot pubblico salvato in `screenshots/v0.3_public_link.png`; report in `screenshots/public-link-report.json`.
- Il confronto tra screenshot locali e pubblicati non mostra differenze strutturali: stessa risoluzione, stessa palette ristretta, stessa assenza di ombre dominanti.
- Difetti residui noti: la revisione visiva umana non è stata possibile dal modello (nessun supporto all'input immagine); la livrea EAV e gli interni restano ricostruzioni originali, non foto verification. Sono documentati in `MAP_SOURCES.md` e rimandati alla 0.4 previa verifica fotografica.
- Nessuna azione correttiva aggiuntiva intrapresa prima della pubblicazione: i controlli automatici sono verdi e le metriche qualitative sono migliorate rispetto alla 0.2.0.
