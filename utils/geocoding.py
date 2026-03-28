import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.cache import PersistentTTLCache

logger = logging.getLogger(__name__)

# Le coordinate non cambiano mai: TTL 24h, persiste su disco tra i riavvii
# In modalità offline usa offline_ttl (7 giorni) per servire dati stale
_geo_cache = PersistentTTLCache(ttl=86_400, path="geo_cache.json")


def get_coordinates(city: str) -> tuple[float, float] | None:
    """Converte il nome di una città nelle sue coordinate geografiche.

    Esegue una richiesta all'API Open-Meteo Geocoding e restituisce
    latitudine e longitudine del primo risultato trovato. Restituisce
    None se la città non esiste nel database dell'API.

    Args:
        city (str): Nome della città da cercare. Può essere in qualsiasi
                    lingua supportata da Open-Meteo.
                    Esempio: "Roma", "Paris", "New York".

    Returns:
        tuple[float, float] | None: Coppia (latitudine, longitudine) se la
            città viene trovata. Esempio: (41.89474, 12.48232) per Roma.
            Restituisce None se nessun risultato corrisponde al nome fornito.

    Raises:
        requests.exceptions.HTTPError: Se l'API risponde con un codice di
            errore HTTP (es. 400, 500).
        requests.exceptions.ConnectionError: Se non è disponibile una
            connessione di rete.

    Example:
        >>> from utils.geocoding import get_coordinates
        >>> coords = get_coordinates("Roma")
        >>> if coords:
        ...     lat, lon = coords
        ...     print(f"Latitudine: {lat}, Longitudine: {lon}")
        Latitudine: 41.89474, Longitudine: 12.48232

        >>> get_coordinates("CittàInesistente")
        None
    """
    cache_key = city.lower()

    cache_key = city.lower()

    cache_key = city.lower()
    url = "https://geocoding-api.open-meteo.com/v1/search"

    result = _geo_cache.get(cache_key)
    if result:
        logger.info("trovato cache: %s", city)
        return tuple(result["value"])

    logger.info("non trovato → chiamo API: %s?name=%s", url, city)
    try:
        response = requests.get(url, params={"name": city, "count": 1, "language": "it"}, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        stale = _geo_cache.get(cache_key, offline=True)
        if stale:
            return tuple(stale["value"])
        raise

    results = response.json().get("results")
    if not results:
        return None

    coords = (results[0]["latitude"], results[0]["longitude"])
    _geo_cache.set(cache_key, list(coords))
    return coords


def get_coordinates_many(cities: list[str]) -> list[dict]:
    """Recupera le coordinate di più città in parallelo.

    Esegue le chiamate di geocoding simultaneamente usando un thread pool,
    riducendo il tempo totale da O(N) a O(1) rispetto alle chiamate sequenziali.

    Args:
        cities (list[str]): Lista di nomi di città da cercare.
                            Esempio: ["Roma", "Milano", "Napoli"]

    Returns:
        list[dict]: Lista di dizionari nello stesso ordine dell'input.
            Ogni dizionario ha la forma:
            - Trovata:     {"city": "Roma", "lat": 41.89, "lon": 12.48}
            - Non trovata: {"city": "Roma", "lat": None, "lon": None, "error": "..."}

    Example:
        >>> from utils.geocoding import get_coordinates_many
        >>> results = get_coordinates_many(["Roma", "CittàFalsa"])
        >>> results[0]
        {'city': 'Roma', 'lat': 41.89474, 'lon': 12.48232}
        >>> results[1]
        {'city': 'CittàFalsa', 'lat': None, 'lon': None, 'error': 'non trovata'}
    """
    results = [None] * len(cities)

    def _fetch(index: int, city: str) -> tuple[int, dict]:
        try:
            coords = get_coordinates(city)
            if coords is None:
                return index, {"city": city, "lat": None, "lon": None, "error": "non trovata"}
            return index, {"city": city, "lat": coords[0], "lon": coords[1]}
        except Exception as e:
            return index, {"city": city, "lat": None, "lon": None, "error": str(e)}

    max_workers = min(len(cities), 5)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch, i, city): i for i, city in enumerate(cities)}
        for future in as_completed(futures):
            index, result = future.result()
            results[index] = result

    return results
