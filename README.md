# App Meteo

App Python da riga di comando che recupera le condizioni meteorologiche attuali per qualsiasi città
nel mondo, utilizzando l'API gratuita [Open-Meteo](https://open-meteo.com/) — nessuna API key richiesta.

---

## Panoramica del progetto

L'app accetta il nome di una città come input, la converte in coordinate geografiche tramite
geocodifica, e recupera in tempo reale temperatura, velocità del vento e umidità.
Tutti gli errori (città non valide, problemi di rete, risposte API errate) vengono gestiti
in modo esplicito e le risposte vengono registrate automaticamente in un file di log.

```
Utente → inserisce nome città
           ↓
       Geocoding API  →  latitudine / longitudine
           ↓
       Forecast API   →  temperatura · vento · umidità
           ↓
       Stampa risultato + scrive nel log
```

---

## Funzionalità

- **Ricerca per nome città** — supporta qualsiasi città nel mondo
- **Dati in tempo reale** — temperatura (°C), velocità del vento (km/h), umidità relativa (%)
- **Gestione errori** — città non trovata, input vuoto, errori HTTP, errori di rete
- **Logging automatico** — ogni risposta API viene salvata in `meteo.log` con timestamp
- **Zero configurazione** — nessuna API key, nessun account necessario
- **Test suite** — 16 test unitari e di integrazione con `pytest`

---

## Requisiti

- Python 3.10 o superiore
- Connessione internet

---

## Installazione

```bash
# 1. Clona o scarica il progetto
cd meteo

# 2. (Consigliato) Crea un ambiente virtuale
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Installa le dipendenze
pip install -r requirements.txt
```

---

## Guida all'uso

```bash
python main.py
```

L'app chiederà il nome della città:

```
Inserisci il nome della città: Milano
```

Premi `Invio` e i dati vengono mostrati immediatamente.

---

## Output di esempio

```
Inserisci il nome della città: Roma

Meteo attuale a Roma:
  Temperatura  :  22.4 °C
  Vento        :  14.8 km/h
  Umidità      :  58 %
```

Esempio con città non trovata:

```
Inserisci il nome della città: CittàXYZ

Città 'CittàXYZ' non trovata. Controlla il nome e riprova.
```

Esempio con input vuoto:

```
Inserisci il nome della città:

Errore: inserisci un nome di città valido.
```

---

## Struttura del progetto

```
meteo/
├── main.py                  # Entry point: flusso principale
├── requirements.txt         # Dipendenze (requests, pytest)
├── .env.example             # Template variabili ambiente
├── .gitignore
├── README.md
├── meteo.log                # Log delle risposte API (generato a runtime)
├── utils/
│   ├── __init__.py
│   ├── geocoding.py         # Converte nome città → latitudine/longitudine
│   ├── weather.py           # Recupera dati meteo tramite coordinate
│   └── display.py           # Formatta e stampa i risultati
├── javascript/
│   └── weatherService.js    # Implementazione equivalente in JavaScript (ES2022)
└── tests/
    ├── __init__.py
    ├── test_geocoding.py    # 5 test per get_coordinates()
    ├── test_weather.py      # 5 test per get_temperature()
    ├── test_display.py      # 5 test per print_weather() e print_forecast()
    └── test_main.py         # 3 test di integrazione per main()
```

---

## Eseguire i test

```bash
pytest tests/ -v
```

Output atteso:

```
tests/test_geocoding.py::test_citta_valida_restituisce_coordinate   PASSED
tests/test_geocoding.py::test_citta_non_trovata_senza_chiave_results PASSED
tests/test_geocoding.py::test_citta_non_trovata_con_results_vuoto   PASSED
tests/test_geocoding.py::test_errore_http_propaga_eccezione         PASSED
tests/test_geocoding.py::test_errore_di_rete_propaga_eccezione      PASSED
tests/test_weather.py::test_coordinate_valide_restituisce_temperatura PASSED
...
16 passed in 0.XXs
```

---

## API utilizzate

| API | URL | Scopo |
|-----|-----|-------|
| Open-Meteo Geocoding | `geocoding-api.open-meteo.com/v1/search` | Nome città → lat/lon |
| Open-Meteo Forecast  | `api.open-meteo.com/v1/forecast`         | Lat/lon → dati meteo |

Entrambe le API sono **gratuite** e **senza API key**.

---

## Miglioramenti futuri

- [ ] **Previsioni multi-giorno** — mostrare meteo per i prossimi 7 giorni
- [ ] **Unità configurabili** — aggiungere supporto per °F e mph
- [ ] **Interfaccia web** — versione browser con Flask o FastAPI
- [ ] **Cache locale** — evitare chiamate ripetute per la stessa città nello stesso giorno
- [ ] **Notifiche** — alert automatici per condizioni meteo estreme
- [ ] **Storico ricerche** — salvare le ultime città cercate in un file JSON
- [ ] **CLI avanzata** — supporto argomenti da riga di comando con `argparse` (es. `python main.py --city Roma`)

---

## Sicurezza ed Etica

### Tecniche di programmazione sicura

| Pratica | Dove applicata |
|---------|----------------|
| HTTPS obbligatorio | Tutte le chiamate API usano `https://` — nessuna trasmissione in chiaro |
| Timeout sulle richieste | `timeout=10` in ogni chiamata `requests.get()` — previene blocchi indefiniti |
| Validazione dell'input | I giorni di previsione sono vincolati a `1 ≤ days ≤ 16`; le coordinate sono tipizzate `float` |
| Gestione errori HTTP | `raise_for_status()` propaga esplicitamente i codici di errore 4xx/5xx |
| Nessuna credenziale nel codice | Nessuna API key, token o password — il codice è sicuro da condividere pubblicamente |
| Nessun dato personale inviato | Le API ricevono solo nomi di città e coordinate geografiche pubbliche |
| Cache senza dati sensibili | I file `geo_cache.json` e `weather_cache.json` contengono solo dati meteo anonimi |
| Ambiente virtuale | L'uso di `venv` isola le dipendenze ed evita conflitti con il sistema |

### Licenze

| Componente | Licenza | Note |
|------------|---------|-------|
| **Open-Meteo API** | [Attribution License (CC BY 4.0)](https://open-meteo.com/en/terms) | Uso gratuito; richiede attribuzione in prodotti derivati |
| **requests** | Apache License 2.0 | Uso commerciale e didattico consentito |
| **colorama** | BSD License | Uso libero con mantenimento della nota di copyright |
| **pytest** | MIT License | Uso libero con mantenimento della nota di copyright |
| **Questo progetto** | Uso didattico — liberamente modificabile | Vedi sezione [Licenza](#licenza) |

> Quando si distribuisce o si estende questo progetto, rispettare i termini della CC BY 4.0 di Open-Meteo
> (citare la fonte nei risultati o nella documentazione pubblica).

### Uso responsabile del codice generato dall'intelligenza artificiale

Parti di questo progetto sono state sviluppate con l'assistenza di strumenti di AI generativa.
Di seguito alcune linee guida per un uso responsabile:

- **Revisione obbligatoria** — il codice generato dall'AI va sempre letto, compreso e testato prima di essere eseguito o distribuito; non va mai usato "alla cieca".
- **Verifica della sicurezza** — controllare che il codice suggerito non introduca vulnerabilità (iniezioni, esposizione di credenziali, dipendenze non sicure).
- **Test come garanzia** — la suite di test (`pytest tests/ -v`) è il principale strumento per verificare che il comportamento reale corrisponda alle aspettative, indipendentemente dall'origine del codice.
- **Responsabilità dello sviluppatore** — l'AI è uno strumento di supporto; la responsabilità finale della correttezza, sicurezza e conformità legale del codice rimane sempre allo sviluppatore.
- **Trasparenza** — in contesti accademici o professionali, dichiarare l'uso di AI nella generazione del codice quando richiesto dalle linee guida dell'istituzione o dell'organizzazione.
- **Citazione delle fonti** — rispettare i termini di servizio degli strumenti AI utilizzati (es. limitazioni sul codice generato a uso commerciale).

---

## Licenza

Progetto a uso didattico — liberamente modificabile.
