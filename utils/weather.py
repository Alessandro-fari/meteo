import logging
import requests
from utils.cache import PersistentTTLCache

logger = logging.getLogger(__name__)

# Il meteo si aggiorna ogni 10 minuti: TTL 600s, persiste su disco tra i riavvii
# In modalità offline usa offline_ttl (7 giorni) per servire l'ultima temperatura nota
_weather_cache = PersistentTTLCache(ttl=600, path="weather_cache.json")

# Campi richiesti all'API — aggiungere qui nuovi valori se necessario
CURRENT_FIELDS = "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"


def get_weather(lat: float, lon: float) -> dict:
    """Recupera temperatura, umidità, vento e precipitazioni per le coordinate fornite.

    Args:
        lat (float): Latitudine, es. 41.89 per Roma.
        lon (float): Longitudine, es. 12.48 per Roma.

    Returns:
        dict: Dati meteo correnti con le chiavi:
            - temperature  (float): gradi Celsius
            - humidity     (int):   percentuale umidità relativa
            - wind_speed   (float): km/h
            - precipitation(float): mm nell'ultima ora

    Raises:
        requests.exceptions.HTTPError: risposta HTTP non valida.
        requests.exceptions.ConnectionError: nessuna connessione di rete.
        requests.exceptions.Timeout: API non risponde entro 10 secondi.

    Example:
        >>> from utils.weather import get_weather
        >>> dati = get_weather(41.89, 12.48)
        >>> print(dati["temperature"])
        22.4
    """
    cache_key = f"{lat:.4f}_{lon:.4f}"
    url = "https://api.open-meteo.com/v1/forecast"

    result = _weather_cache.get(cache_key)
    if result:
        logger.info("trovato cache: %s, %s", lat, lon)
        return result["value"]

    logger.info("non trovato → chiamo API: %s?latitude=%s&longitude=%s", url, lat, lon)
    params = {
        "latitude":      lat,
        "longitude":     lon,
        "current":       CURRENT_FIELDS,
        "forecast_days": 1,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        stale = _weather_cache.get(cache_key, offline=True)
        if stale:
            return stale["value"]
        raise

    current = response.json()["current"]
    data = {
        "temperature":   current["temperature_2m"],
        "humidity":      current["relative_humidity_2m"],
        "wind_speed":    current["wind_speed_10m"],
        "precipitation": current["precipitation"],
    }
    _weather_cache.set(cache_key, data)
    return data


def get_forecast(lat: float, lon: float, days: int = 5) -> list[dict]:
    """Recupera la previsione meteo giornaliera per i prossimi giorni.

    Args:
        lat (float): Latitudine, es. 41.89 per Roma.
        lon (float): Longitudine, es. 12.48 per Roma.
        days (int):  Numero di giorni da prevedere. Default: 5. Max: 16.

    Returns:
        list[dict]: Lista di dizionari, uno per ogni giorno, con le chiavi:
            - date         (str):   Data in formato YYYY-MM-DD.
            - temp_max     (float): Temperatura massima in °C.
            - temp_min     (float): Temperatura minima in °C.
            - precipitation(float): Precipitazioni totali in mm.
            - wind_speed   (float): Velocità del vento massima in km/h.
            - weather_code (int):   Codice WMO della condizione meteo.

    Raises:
        requests.exceptions.HTTPError: risposta HTTP non valida.
        requests.exceptions.ConnectionError: nessuna connessione di rete.
        requests.exceptions.Timeout: API non risponde entro 10 secondi.
        ValueError: days non compreso tra 1 e 16.

    Example:
        >>> from utils.weather import get_forecast
        >>> previsione = get_forecast(41.89, 12.48, days=3)
        >>> previsione[0]["date"]
        '2026-03-22'
        >>> previsione[0]["temp_max"]
        18.5
    """
    if not 1 <= days <= 16:
        raise ValueError(f"days deve essere compreso tra 1 e 16, ricevuto: {days}")

    cache_key = f"forecast_{lat:.4f}_{lon:.4f}_{days}"
    url = "https://api.open-meteo.com/v1/forecast"

    result = _weather_cache.get(cache_key)
    if result:
        logger.info("trovato cache: previsione %s giorni per %s, %s", days, lat, lon)
        return result["value"]

    logger.info("non trovato → chiamo API: %s?latitude=%s&longitude=%s&forecast_days=%s", url, lat, lon, days)
    params = {
        "latitude":      lat,
        "longitude":     lon,
        "daily":         "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weather_code",
        "forecast_days": days,
        "timezone":      "auto",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        stale = _weather_cache.get(cache_key, offline=True)
        if stale:
            return stale["value"]
        raise

    daily = response.json()["daily"]
    forecast = [
        {
            "date":          daily["time"][i],
            "temp_max":      daily["temperature_2m_max"][i],
            "temp_min":      daily["temperature_2m_min"][i],
            "precipitation": daily["precipitation_sum"][i],
            "wind_speed":    daily["wind_speed_10m_max"][i],
            "weather_code":  daily["weather_code"][i],
        }
        for i in range(days)
    ]
    _weather_cache.set(cache_key, forecast)
    return forecast


def get_weather_batch(coords_list: list[tuple[float, float]]) -> list[dict]:
    """Recupera i dati meteo completi per più località con una singola chiamata API.

    Args:
        coords_list (list[tuple[float, float]]): Lista di coppie (lat, lon).
            Esempio: [(41.89, 12.48), (45.46, 9.19)]

    Returns:
        list[dict]: Lista di dati meteo nello stesso ordine di coords_list.
            Ogni dict contiene: temperature, humidity, wind_speed, precipitation.

    Raises:
        requests.exceptions.HTTPError: risposta HTTP non valida.
        requests.exceptions.Timeout: API non risponde entro 10 secondi.
        ValueError: coords_list è vuota.

    Example:
        >>> from utils.weather import get_weather_batch
        >>> results = get_weather_batch([(41.89, 12.48), (45.46, 9.19)])
        >>> results[0]["temperature"]
        22.4
    """
    if not coords_list:
        raise ValueError("coords_list non può essere vuota.")

    latitudes  = ",".join(str(lat) for lat, _ in coords_list)
    longitudes = ",".join(str(lon) for _, lon in coords_list)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":      latitudes,
        "longitude":     longitudes,
        "current":       CURRENT_FIELDS,
        "forecast_days": 1,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    items = data if isinstance(data, list) else [data]
    return [
        {
            "temperature":   item["current"]["temperature_2m"],
            "humidity":      item["current"]["relative_humidity_2m"],
            "wind_speed":    item["current"]["wind_speed_10m"],
            "precipitation": item["current"]["precipitation"],
        }
        for item in items
    ]
