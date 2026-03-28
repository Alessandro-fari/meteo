// ============================================================
//  weatherService.js
//  Funzione per principianti: città → meteo (2 chiamate API)
// ============================================================

// Attiva i log di debug solo se la variabile d'ambiente DEBUG=true
// Esempio: DEBUG=true node weatherService.js
const DEBUG = typeof process !== "undefined" && process.env.DEBUG === "true";
const log = (...args) => DEBUG && console.log(...args);

// Mappa dei codici WMO → descrizione leggibile
const WMO_CODES = {
  0:  "Cielo sereno ☀️",
  1:  "Prevalentemente sereno 🌤️",
  2:  "Parzialmente nuvoloso ⛅",
  3:  "Coperto ☁️",
  45: "Nebbia 🌫️",
  48: "Nebbia con brina 🌫️",
  51: "Pioggerella leggera 🌦️",
  53: "Pioggerella moderata 🌦️",
  55: "Pioggerella intensa 🌧️",
  61: "Pioggia leggera 🌧️",
  63: "Pioggia moderata 🌧️",
  65: "Pioggia intensa 🌧️",
  71: "Neve leggera ❄️",
  73: "Neve moderata ❄️",
  75: "Neve intensa ❄️",
  80: "Rovesci leggeri 🌦️",
  81: "Rovesci moderati 🌧️",
  82: "Rovesci violenti ⛈️",
  95: "Temporale ⛈️",
  99: "Temporale con grandine ⛈️🌨️",
};

// ─────────────────────────────────────────────
// MOBILE CACHE — localStorage con TTL e supporto offline
// Funziona in browser e React Native (con AsyncStorage come polyfill)
// ─────────────────────────────────────────────

const CACHE_PREFIX  = "weather_cache:";
const TTL_WEATHER   = 10 * 60 * 1000;          // 10 minuti (ms)
const TTL_GEO       = 24 * 60 * 60 * 1000;     // 24 ore    (ms)
const TTL_OFFLINE   =  7 * 24 * 60 * 60 * 1000; // 7 giorni  (ms)

/**
 * Salva un valore in localStorage con timestamp Unix corrente.
 *
 * @param {string} key    - Chiave univoca (verrà prefissata con CACHE_PREFIX).
 * @param {*}      value  - Qualsiasi valore serializzabile in JSON.
 */
function cacheSet(key, value) {
  try {
    const entry = { value, savedAt: Date.now() };
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(entry));
  } catch {
    // localStorage pieno o non disponibile: ignora silenziosamente
  }
}

/**
 * Recupera un valore dalla cache con supporto modalità offline.
 *
 * In modalità online restituisce null se la voce è scaduta (TTL normale).
 * In modalità offline restituisce i dati anche scaduti (fino a TTL_OFFLINE),
 * marcandoli con stale: true così l'UI può mostrare un avviso all'utente.
 *
 * @param {string}  key     - Chiave da cercare.
 * @param {number}  ttl     - TTL normale in millisecondi.
 * @param {boolean} offline - Se true, usa TTL esteso per dati stale.
 * @returns {{ value: *, stale: boolean } | null}
 */
function cacheGet(key, ttl, offline = false) {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;

    const { value, savedAt } = JSON.parse(raw);
    const age = Date.now() - savedAt;

    if (age <= ttl)                        return { value, stale: false };
    if (offline && age <= TTL_OFFLINE)     return { value, stale: true  };
    if (!offline) localStorage.removeItem(CACHE_PREFIX + key);

    return null;
  } catch {
    return null;
  }
}

/**
 * Rimuove tutte le voci weather_cache:* da localStorage.
 * Utile per un pulsante "Aggiorna dati" nell'UI mobile.
 */
function cacheClear() {
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith(CACHE_PREFIX))
      .forEach((k) => localStorage.removeItem(k));
  } catch { /* ignore */ }
}

/**
 * Rileva se il dispositivo è offline usando navigator.onLine.
 * Fallback a true (online) se l'API non è disponibile.
 *
 * @returns {boolean}
 */
function isOffline() {
  return typeof navigator !== "undefined" && navigator.onLine === false;
}

// ─────────────────────────────────────────────
// UTILITY — fetch con timeout tramite AbortController
// Lancia un errore chiaro se l'API non risponde entro timeoutMs
// ─────────────────────────────────────────────
async function fetchWithTimeout(url, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { signal: controller.signal });
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error(`Timeout: nessuna risposta dopo ${timeoutMs}ms`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// ─────────────────────────────────────────────
// UTILITY — legge il corpo di una risposta HTTP in errore
// Prova prima JSON, poi testo semplice
// ─────────────────────────────────────────────
async function readErrorBody(response) {
  const text = await response.text();
  try {
    return JSON.stringify(JSON.parse(text));
  } catch {
    return text;
  }
}

// ─────────────────────────────────────────────
// STEP 1 — Geocoding: nome città → lat/lon
// ─────────────────────────────────────────────
async function getCityCoordinates(cityName) {
  if (!cityName || typeof cityName !== "string" || cityName.trim() === "") {
    throw new Error("Nome città non valido: inserisci una stringa non vuota.");
  }

  const offline  = isOffline();
  const cacheKey = `geo:${cityName.trim().toLowerCase()}`;
  const cached   = cacheGet(cacheKey, TTL_GEO, offline);
  if (cached) {
    if (cached.stale) log(`📦 [OFFLINE] Coordinate stale per "${cityName}"`);
    else              log(`📦 [CACHE]   Coordinate per "${cityName}"`);
    return cached.value;
  }
  if (offline) throw new Error(`Offline e nessun dato in cache per "${cityName}".`);

  const url = new URL("https://geocoding-api.open-meteo.com/v1/search");
  url.searchParams.set("name",     cityName.trim());
  url.searchParams.set("count",    "1");
  url.searchParams.set("language", "it");
  url.searchParams.set("format",   "json");

  let response;
  try {
    response = await fetchWithTimeout(url.toString());
  } catch (err) {
    throw new Error(`Errore di rete durante il geocoding: ${err.message}`);
  }

  if (!response.ok) {
    const body = await readErrorBody(response);
    throw new Error(`Geocoding API errore ${response.status}: ${body}`);
  }

  const data = await response.json();

  if (!data.results || data.results.length === 0) {
    throw new Error(`Città "${cityName}" non trovata. Controlla il nome e riprova.`);
  }

  const { name, latitude, longitude, country } = data.results[0];
  const result = { name, latitude, longitude, country };
  cacheSet(`geo:${cityName.trim().toLowerCase()}`, result);
  log(`📍 Coordinate trovate: ${name} (${country}) → lat: ${latitude}, lon: ${longitude}`);
  return result;
}

// ─────────────────────────────────────────────
// STEP 2 — Meteo: lat/lon → dati meteorologici
// ─────────────────────────────────────────────
async function getWeatherByCoordinates(latitude, longitude) {
  if (
    typeof latitude  !== "number" || typeof longitude !== "number" ||
    isNaN(latitude)  || isNaN(longitude)
  ) {
    throw new Error(`Coordinate non valide: lat=${latitude}, lon=${longitude}`);
  }

  const url = new URL("https://api.open-meteo.com/v1/forecast");
  url.searchParams.set("latitude",         latitude);
  url.searchParams.set("longitude",        longitude);
  url.searchParams.set("current",          "temperature_2m,weather_code,wind_speed_10m");
  url.searchParams.set("temperature_unit", "celsius");
  url.searchParams.set("timezone",         "auto");
  url.searchParams.set("forecast_days",    "1");

  let response;
  try {
    response = await fetchWithTimeout(url.toString());
  } catch (err) {
    throw new Error(`Errore di rete durante il fetch meteo: ${err.message}`);
  }

  if (!response.ok) {
    const body = await readErrorBody(response);
    throw new Error(`Weather API errore ${response.status}: ${body}`);
  }

  const data = await response.json();

  if (!data.current) {
    throw new Error("Risposta API meteo non valida: campo 'current' mancante.");
  }

  log(`🌡️  Dati meteo ricevuti:`, data.current);
  return data.current;
}

// ─────────────────────────────────────────────
// FUNZIONE PRINCIPALE — Combina i 2 step
// Il try/catch è rimosso: gli errori propagano direttamente al chiamante
// evitando che lo stesso errore venga loggato due volte
// ─────────────────────────────────────────────
async function getWeatherByCity(cityName) {
  const { name, latitude, longitude, country } = await getCityCoordinates(cityName);
  const weather = await getWeatherByCoordinates(latitude, longitude);

  return {
    city:        name,
    country,
    temperature: weather.temperature_2m,
    unit:        "°C",
    description: WMO_CODES[weather.weather_code] ?? "Condizione sconosciuta",
    windspeed:   weather.wind_speed_10m,
    timestamp:   weather.time,
  };
}

// ─────────────────────────────────────────────
// USO — Esempio pratico
// ─────────────────────────────────────────────
getWeatherByCity("appiano")
  .then((result) => {
    console.log("\n✅ Risultato finale:");
    console.log(`🏙️  Città:        ${result.city}, ${result.country}`);
    console.log(`🌡️  Temperatura:  ${result.temperature}${result.unit}`);
    console.log(`🌤️  Condizione:   ${result.description}`);
    console.log(`💨 Vento:        ${result.windspeed} km/h`);
    console.log(`🕒 Aggiornato:   ${result.timestamp}`);
  })
  .catch((error) => {
    console.error("Impossibile recuperare il meteo:", error.message);
  });
