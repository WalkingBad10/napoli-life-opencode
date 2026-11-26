# Ricerca di riferimento — stazione Circumflegrea di Pianura (Napoli)

**Scopo:** raccogliere riferimenti reali e verificabili sulla stazione di Pianura e sul contesto stradale immediato, per migliorare la fedeltà artistica della ricostruzione pixel art senza inventare geometrie né copiare asset protetti.

**Data ricerca:** 2026-11-26  
**Ambito:** solo documentazione. Nessun file di codice, asset o configurazione è stato modificato; nessuna immagine trovata online è stata salvata nel repository; nessun commit/push eseguito.

## Metodo e limiti

- `websearch` non era disponibile (errori `Web search cancelled`), quindi la ricerca è stata fatta con `webfetch` diretto e con pagine di ricerca DuckDuckGo in HTML.
- Le due immagini della stazione su Wikimedia Commons sono state scaricate **solo in una cartella temporanea fuori dal repository** per analisi testuale; non sono state copiate negli asset.
- Il modello usato per la ricerca **non può vedere immagini**. Le descrizioni visive di seguito derivano da didascalie, metadati e fonti testuali. L'analisi colorimetrica locale è riportata solo come indicazione debole, non come prova.
- La foto 2018 è post-restauro 2006; la foto 2006 è durante i lavori. Sono le uniche due immagini della categoria Commons dedicata alla stazione.

---

## 1. Elenco delle fonti

### Fonti primarie / cartografiche

| # | Fonte | URL | Cosa contiene | Affidabilità |
|---|---|---|---|---|
| S1 | OpenStreetMap — edificio stazione (`way/503291719`) | https://www.openstreetmap.org/way/503291719 | `building=train_station`, 5 nodi, versione 1, curatore `fedc`, changeset 49825583. Bbox circa 57,6 × 15,2 m. | Alta per la geometria; il tag è minimale (nessun nome, piano o colore). |
| S2 | OpenStreetMap — nodo stazione (`node/4936292644`) | https://www.openstreetmap.org/node/4936292644 | `name=Pianura`, `railway=station`, `public_transport=station`, `train=yes`, `network=Circumflegrea`, `operator=Ente Autonomo Volturno`, `operator:short=EAV`, `wikidata=Q3970470`, `wikipedia=it:Stazione di Pianura`. Coordinate 40.8560001, 14.1624307. | Alta. |
| S3 | OpenStreetMap — area di fermata (`relation/16802901`) | https://www.openstreetmap.org/relation/16802901 | Relazione `public_transport=stop_area` "Pianura": nodo stazione, 2 stop position (8592196829, 8592196828), banchine `way/503291716` e `way/503291714`. | Alta. |
| S4 | OpenStreetMap — banchine `way/503291716`, `way/503291714` | https://www.openstreetmap.org/way/503291716 · https://www.openstreetmap.org/way/503291714 | `railway=platform`, `public_transport=platform`, `area=yes`, `lit=yes`, `tactile_paving=yes`, `bin=yes`. **`shelter=no` su entrambe.** `bench=yes` solo su `503291714`. | Alta. |
| S5 | OpenStreetMap — passerella `way/503291722` | https://www.openstreetmap.org/way/503291722 | `highway=footway`, `bridge=yes`, `layer=1`; attraversa i binari a ~40 m dal nodo stazione. | Alta. |
| S6 | Estratto Overpass locale | `data/osm/pianura_20261126.json` (timestamp OSM 2026-11-26T16:04:06Z) | Conferma i tag sopra e mostra diversi `highway=steps` / `highway=footway` (503291721, 503291723–503291730) entro ~40 m dalla stazione; nessun `tunnel=yes` e nessun tag lift/ascensore nell'estratto. | Alta per ciò che è mappato; l'assenza di tag non prova l'assenza fisica. |
| S7 | Wikidata `Q3970470` (EntityData JSON) | https://www.wikidata.org/wiki/Special:EntityData/Q3970470.json | Coordinate 40.8561/14.1624, `instance of` stazione ferroviaria, `located in` Napoli (Q2634), `opening date` 1962, `operator` EAV (Q3726202), `number of tracks` 2, `named after` Don Giustino Russolillo (Q1101657), immagine principale `Stazione Circumflegrea Pianura.png`. | Media-alta; molte affermazioni referenziano Wikipedia italiana, non fonti primarie. |

### Fonti testuali

| # | Fonte | URL | Cosa contiene | Affidabilità |
|---|---|---|---|---|
| S8 | Wikipedia IT — Stazione di Pianura | https://it.wikipedia.org/wiki/Stazione_di_Pianura | Nome completo "Pianura – Don Giustino Russolillo", Circumflegrea, via Picasso, attivazione 1962, 2 binari, ristrutturazione 2006, sottopassaggio al binario 2, 2 ascensori, biglietteria con edicola e bar, interscambio ANM/CTP, sovrappassaggio tra Via Picasso e Via del Polo Artigianale. | **Media**: la voce è esplicitamente segnalata "senza fonti". |
| S9 | Wikipedia EN — Pianura railway station | https://en.wikipedia.org/wiki/Pianura_railway_station | Voce collegata, sostanzialmente derivata da quella italiana. | Media (stessa limitazione). |
| S10 | Wikimedia Commons — categoria | https://commons.wikimedia.org/wiki/Category:Pianura_railway_station | Contiene solo due file: la foto 2018 e la foto 2006. | Alta per l'inventario. |
| S11 | File `Stazione_Circumflegrea_Pianura.png` | https://commons.wikimedia.org/wiki/File:Stazione_Circumflegrea_Pianura.png · https://upload.wikimedia.org/wikipedia/commons/c/c3/Stazione_Circumflegrea_Pianura.png | 976×699, autore **Microinfo10**, own work, 13 marzo 2018, **CC BY-SA 4.0**. Didascalia su Wikipedia: "L'entrata della stazione dopo il restauro del 2006". Mostra l'**ingresso lato strada** della stazione ristrutturata. | Alta per autore/licenza/didascalia. |
| S12 | File `Lavoricumana_pianura.jpg` | https://commons.wikimedia.org/wiki/File:Lavoricumana_pianura.jpg · https://upload.wikimedia.org/wikipedia/commons/c/cb/Lavoricumana_pianura.jpg | 800×600, autore/uploader **Utente:Catman** su it.wikipedia, pubblicato il 14 gennaio 2006, **public domain**. Didascalia: "La stazione Pianura durante i lavori del 2006". Mostra il cantiere del restauro. | Alta per metadati; immagine non scaricata con successo (429). |
| S13 | QuiCampiFlegrei, 8 luglio 2020 | https://www.quicampiflegrei.it/2020/07/08/la-stazione-di-pianura-della-circumflegrea-dedicata-a-don-giustino-due-murales-illustrano-la-vita-del-beato/ | Cerimonia del 7 luglio 2020: stazione intitolata a don Giustino Russolillo; **targhe con la nuova intitolazione**; **due murales dell'artista Luca Danza** (don Giustino con i bambini; costruzione del Vocazionario); presidente EAV Umberto De Gregorio; "recupero e rilancio di tutte le nostre stazioni". | Media-alta (testata locale, fatti datati e attribuiti). |
| S14 | Il Mattino, 21 giugno 2020 | https://www.ilmattino.it/napoli/citta/don_giustino_russolillo_murales_stazione_pianura-5300931.html | Annuncia i due murales di street art di **Luca Danza** e la dedica della stazione "dai primi di luglio"; descrive i soggetti (bambini/ragazzi; cantiere della "Casa" dei Vocazionisti); finanziamento EAV con contributo di artisti volontari. | Alta (quotidiano, firma Giuliana Covella). |
| S15 | EAV — storia della Circumflegrea | https://www.eavsrl.it/la-storia/sepsa/la-circumflegrea/ | Contesto storico della linea e passaggio a EAV. | Alta per il contesto, non descrive la stazione. |
| S16 | EAV — avviso lavori Pianura–Licola, 16–18 novembre 2024 | https://www.eavsrl.it/linee-flegree-interruzione-tratta-pianura-licola-dal-16-al-18-novembre-2024/ | Conferma che la stazione è tuttora operativa sulla Circumflegrea e che la tratta Pianura–Licola è soggetta a interruzioni per lavori. | Alta. |
| S17 | Comune di Napoli — Via Nelson Mandela | https://www.comune.napoli.it/multimediale/a-pianura-via-nelson-mandela/ | Via Nelson Mandela collega via Provinciale Napoli alla rotonda di Via Montagna Spaccata. | Alta per la toponomastica. |
| S18 | NapoliToday — inaugurazione Via Nelson Mandela | https://www.napolitoday.it/cronaca/via-nelson-mandela-napoli-inaugurazione.html | Contesto dell'asse stradale di Pianura. | Media. |
| S19 | ASIA Napoli — isola ecologica di Via Nelson Mandela | https://www.asianapoli.it/centri-di-raccolta/via-nelson-mandela-pianura/ | Isola ecologica in Via Nelson Mandela (risultava temporaneamente chiusa al momento della ricerca). | Alta. |
| S20 | Ferrovie.it, articolo 16602 | https://www.ferrovie.it/portale/articoli/16602 | Contesto ferroviario locale citato nelle ricerche. | Media; da usare solo come supporto. |

### Fonti interne al progetto (stato attuale della ricostruzione)

| # | File | Cosa documenta |
|---|---|---|
| D1 | `docs/reference/photo_analysis.txt` | Ipotesi attuali dalla foto fornita: 3 piani, giallo/verde, tetto a falda, finestre/persiane/balconi al primo piano, porta frontale, nessuna insegna, nessuna pensilina/binari/banchine/vegetazione visibili. |
| D2 | `tools/generate_buildings.py` | `pick_levels()` restituisce **1** per `station`; `wall = stucco_cream`; `roof_color = roof_grey`; `draw_flat_roof(..., station=True)`; `draw_canopy()`; `draw_station_sign()` scrive **"EAV  PIANURA"**; `gable = not is_station`. |
| D3 | `public/assets/buildings/manifest.json` | `way/503291719`, `kind=train_station`, `style=station`, `width_px=921`. |
| D4 | `docs/ART_SPEC.md`, `ASSET_GUIDE.md`, `MAP_SOURCES.md`, `CHANGELOG.md`, `HANDOFF.md` | Contratto grafico (tetto piano + pensilina), facciata 921 px derivata dal bbox OSM a 16 px/m, nodo origine 4936292644, cronologia del ridisegno 0.3.0. |

---

## 2. Fatti verificati

### Identità e servizio

- La stazione si chiama **Pianura**, ufficialmente **"Pianura – Don Giustino Russolillo"** (S8, S7, S13).
- È sulla **Circumflegrea**, gestita da **EAV / Ente Autonomo Volturno** (S2, S7, S8, S16).
- Attivata nel **1962** (S7, S8); **2 binari** (S7, S8).
- Coordinate del nodo stazione: **40.8560001, 14.1624307** (S2); Wikidata riporta 40.8561/14.1624 (S7).
- La voce Wikipedia la colloca **in via Picasso** (S8). L'estratto OSM mostra effettivamente `Via Pablo Picasso` a ~50–100 m e fermate bus denominate "Picasso" nelle immediate vicinanze (S6).
- La tratta **Pianura–Licola** è ancora oggetto di lavori/interruzioni programmate (S16): la stazione è operativa nel 2024.

### Storia recente e interventi

- **Restauro nel 2006** (S8). Esistono due foto: ingresso dopo il restauro (2018, S11) e stazione durante i lavori (2006, S12).
- **7 luglio 2020**: cerimonia di intitolazione a don Giustino Russolillo, con **targhe con la nuova denominazione** e **due murales realizzati da Luca Danza** (S13). Il Mattino (S14) aveva annunciato il progetto il 21 giugno 2020, descrivendo i due soggetti: don Giustino con bambini/ragazzi e il cantiere del futuro Vocazionario.
- L'iniziativa è stata promossa dal territorio (Associazione Amici di Don Giustino, IX Municipalità, Padri e Suore Vocazioniste) e finanziata da EAV con contributo di artisti di strada volontari (S13, S14).

### Geometria e tecnica (OSM)

- L'edificio è mappato come un unico poligono `building=train_station` con 5 nodi e **nessun tag su piani, colori o tipo di tetto** (S1). Il bounding box è circa **57,6 × 15,2 m**, che a 16 px/m dà **921 × 243 px**: è l'origine del `width_px: 921` del manifest (D3, D4).
- La stop area comprende **due stop position e due banchine** (S3, S4).
- **Entrambe le banchine hanno `shelter=no`** (S4). Sono presenti `lit=yes`, `tactile_paving=yes` e `bin=yes`; `bench=yes` solo sulla banchina `503291714`.
- Un **ponte pedonale** (`bridge=yes`, `layer=1`) attraversa i binari a circa 40 m dal nodo stazione (S5), coerente con il "sovrappassaggio" citato da Wikipedia (S8).
- L'estratto locale contiene diversi segmenti `highway=steps` e `highway=footway` vicino alla stazione (S6), ma **nessun tag `tunnel=yes` e nessun tag ascensore**.

### Contesto stradale immediato

- **Via Nelson Mandela** è l'asse che collega via Provinciale Napoli alla rotonda di Via Montagna Spaccata (S17, S18); OSM la mappa come `residential`/`service`, asfalto (S6).
- In Via Nelson Mandela è presente un'**isola ecologica ASIA** (S19).
- Nei pressi della stazione OSM riporta **Via Pablo Picasso**, **Via Amedeo Modigliani**, più fermate bus "Picasso" e uno **Stazionamento ANM** a ~33 m (S6).

---

## 3. Fatti plausibili ma NON verificati

1. **I 3 piani, i colori giallo/verde e il tetto a falda** di `photo_analysis.txt` (D1) non sono confermati da alcuna fonte testuale indipendente. La foto 2018 (S11) è l'unica immagine post-restauro disponibile, ma il suo contenuto visivo non è verificabile in questa sessione.
2. **Analisi colorimetricaLocale (indicativa, non conclusiva):** sull'anteprima 960 px della foto 2018 si trovano aree verdi (~7% dei pixel) e giallo/ocra (~3%), ma anche grandi aree blu (cielo) e molte tonalità grigie. Questo *non* dimostra che l'intonaco della stazione sia giallo/verde: potrebbero essere vegetazione, veicoli, insegne o riflessi.
3. **Tetto piano in lamiera grigia** (D2, D4): nessuna fonte testuale o metadato lo conferma. È una scelta di stile del generatore, non un dato verificato.
4. **Sottopassaggio al binario 2, 2 ascensori, biglietteria con edicola e bar, interscambio ANM/CTP** (S8): affermati testualmente da Wikipedia, ma la voce è segnalata senza fonti e OSM non contiene tag `tunnel` o lift. Sono quindi *plausibili*, da confermare con fonte primaria EAV/Comune o con una foto dei binari.
5. **La larghezza 921 px come "facciata"**: è correttamente derivata dal bbox OSM, ma rappresenta la **lunghezza dell'edificio**, non necessariamente il lato visibile nella foto di ingresso. La foto potrebbe inquadrare il lato corto.
6. **L'insegna blu "EAV PIANURA"** (D2): non risulta in nessuna fonte testuale; la documentazione del 2020 parla invece di targhe con la nuova intitolazione (S13). Non è possibile affermare che l'insegna attuale sia ancora quella generata.
7. **Posizione esatta della pensilina:** OSM dice `shelter=no` sulle banchine (S4), ma una pensilina potrebbe esistere come struttura non mappata. La foto lato strada non permette di controllare il lato binari.

---

## 4. Contraddizioni con la ricostruzione attuale

| Elemento | Ricostruzione attuale | Fonti a confronto | Giudizio |
|---|---|---|---|
| **Facciata 921 px** | `width_px=921` dal bbox 57,6 m a 16 px/m (D3, D4) | OSM `way/503291719` (S1) conferma il bbox; la foto 2018 (S11) mostra l'ingresso, non necessariamente il lato lungo. | **Non è un errore**, ma va descritto come "lunghezza edificio OSM", non come "facciata fotografata". |
| **Tetto piano in lamiera grigia** | `draw_flat_roof(..., station=True)`, `roof_grey`, `gable = not is_station` (D2) | `photo_analysis.txt` dice "tetto a falda" (D1); OSM non dà il tipo di tetto (S1). | **Contraddizione non risolta** tra due ipotesi; serve la foto originale o una nuova immagine. |
| **Numero di piani** | `pick_levels()` → **1** per `station` (D2) | `photo_analysis.txt` dice **3 piani** (D1). | **Contraddizione diretta**. Da verificare visivamente prima di cambiare. |
| **Colori** | `stucco_cream` + `roof_grey` + `eav_blue` (D2) | `photo_analysis.txt` dice **giallo e verde** (D1); analisi colorimetrica solo parzialmente compatibile. | **Contraddizione parziale**, non risolta. |
| **Pensilina lato binari** | `draw_canopy()` sempre per `station` (D2), prevista anche da `ART_SPEC.md` (D4) | OSM: **`shelter=no` su entrambe le banchine** (S4); `photo_analysis.txt`: nessuna pensilina visibile (D1). | **Contraddizione forte**: due fonti indipendenti sono contro la pensilina. |
| **Insegna "EAV PIANURA"** | `draw_station_sign()` scrive "EAV  PIANURA" (D2) | Nessuna fonte la conferma; 2020: targhe "Don Giustino Russolillo" (S13), foto 2018 senza insegne visibili secondo D1. | **Possibile obsolescenza** e contraddizione con la denominazione attuale. |
| **Binari/banchine assenti nella foto** | Il mondo di gioco include binari e banchine da OSM | `photo_analysis.txt` dice che non sono visibili (D1); OSM li mappa eccome (S3, S4). | **Non è una contraddizione reale**: la foto inquadra solo il fronte stradale. |

---

## 5. Raccomandazioni concrete per il generatore

Queste sono indicazioni per una **sessione di implementazione successiva**, non modifiche eseguite ora.

1. **Non toccare la geometria OSM.** Mantenere `way/503291719`, il nodo origine `4936292644` e `width_px=921`. Aggiornare solo la documentazione per dire che 921 px è la lunghezza del poligono OSM a 16 px/m, non una misura fotografica.
2. **Rivedere la pensilina (priorità alta).** Dato `shelter=no` su entrambe le banchine (S4), disabilitare `draw_canopy()` per `way/503291719`, oppure renderla un flag esplicito e dichiararla come licenza artistica in `ASSET_GUIDE.md`. Lasciare invariate le altre stazioni.
3. **Aggiornare la segnaletica.** Prevedere una variante di `draw_station_sign()` con testo `PIANURA` / `DON GIUSTINO RUSSOLILLO` e mantenere "EAV" solo come operatore, senza inventare un logo. Aggiungere una seconda targa più piccola come richiamo all'intitolazione del 2020 (S13).
4. **Aggiungere i murales come dettaglio originale, non come copia.** Generare proceduralmente due pannelli astratti/figurativi ispirati ai soggetti documentati (bambini/ragazzi; cantiere del Vocazionario, S13/S14), con palette tenue e coerente con `ART_SPEC.md`. **Non scaricare né riprodurre le opere di Luca Danza**; citare solo la fonte testuale nei crediti.
5. **Piani, tetto e colori: chiedere una conferma visiva.** Prima di cambiare `pick_levels()`, il tetto piano o `stucco_cream`, recuperare la foto originale usata per `photo_analysis.txt` o una nuova foto geolocalizzata del fronte. Fino ad allora etichettare questi valori come "best guess" e rimuovere la parola "Certi" da `photo_analysis.txt` nelle doc derivate.
6. **Sfruttare i dettagli OSM già verificati.** Se si aggiungono dettagli alle banchine: panchina solo su `503291714`, cassonetti, illuminazione, pavimentazione tattile (S4). Usare i segmenti `steps`/`footway` e il ponte pedonale `503291722` già presenti in `data/osm/`, senza inventare nuovi percorsi (direttiva AGENTS.md n. 1).
7. **Contesto stradale:** mantenere Via Nelson Mandela, Via Pablo Picasso e le fermate "Picasso" così come sono nel dato OSM (S6, S17). Non aggiungere il sovrappassaggio come geometria nuova: esiste già come `way/503291722`.
8. **Aggiornare la documentazione in un secondo momento:** `docs/ART_SPEC.md`, `ASSET_GUIDE.md`, `CHANGELOG.md`, `HANDOFF.md` dovranno recepire le scelte fatte, citando questo file. Non aggiornarle in questa fase di sola ricerca.
9. **Licenze e attribuzioni:** se in futuro si useranno le due foto come riferimento visivo, rispettare **CC BY-SA 4.0** (Microinfo10, 2018, S11) e **public domain** (Utente:Catman, 2006, S12). Non copiare immagini nel repository e non usare asset di altri giochi.

---

## 6. Domande aperte

- La foto fornita in origine (alla base di `photo_analysis.txt`) è la stessa `Stazione_Circumflegrea_Pianura.png` di Commons, oppure un'altra immagine?
- Il fabbricato ha davvero 3 piani e un tetto a falda, oppure `photo_analysis.txt` descrive un edificio diverso/una prospettiva ingannevole?
- La pensilina lato binari esiste fisicamente anche se OSM riporta `shelter=no`?
- Sottopassaggio e ascensori sono ancora presenti dopo il restauro 2006 e gli interventi 2020?
- L'insegna "EAV PIANURA" è stata sostituita dalle targhe del 2020?

*Fine del documento. Nessuna immagine è stata salvata in `napoli-life-opencode`; i file temporanei usati per l'analisi stanno in `C:\Users\rocka\AppData\Local\Temp\opencode\pianura_research\`.*
