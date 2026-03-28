import logging
from colorama import init, Fore, Style
from utils.geocoding import get_coordinates, get_coordinates_many
from utils.weather import get_weather, get_weather_batch, get_forecast
from utils.display import print_weather, print_forecast

init(autoreset=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    raw = input("Inserisci una o più città (separate da virgola): ").strip()
    if not raw:
        print(Style.BRIGHT + Fore.RED + "Errore:" + Style.RESET_ALL + " inserisci almeno un nome di città.")
        return

    cities = [c.strip() for c in raw.split(",") if c.strip()]

    # ── Scelta modalità ───────────────────────────────────────────
    modalita   = input("Vuoi [1] Meteo attuale o [2] Previsione 5 giorni? ").strip()
    previsione = modalita == "2" or (modalita.isdigit() and int(modalita) > 1)

    # ── Città singola ─────────────────────────────────────────────
    if len(cities) == 1:
        coords = get_coordinates(cities[0])
        if coords is None:
            print(Style.BRIGHT + Fore.RED + f"Città '{cities[0]}' non trovata." + Style.RESET_ALL)
            return
        lat, lon = coords
        if previsione:
            forecast = get_forecast(lat, lon, days=5)
            print_forecast(cities[0], forecast)
        else:
            data = get_weather(lat, lon)
            print_weather(cities[0], data)
        return

    # ── Più città: geocoding parallelo ────────────────────────────
    print("\n" + Style.DIM + f"Recupero coordinate per {len(cities)} città in parallelo...")
    geo_results = get_coordinates_many(cities)

    found     = [r for r in geo_results if r["lat"] is not None]
    not_found = [r for r in geo_results if r["lat"] is None]

    for r in not_found:
        print("  " + Fore.YELLOW + f"⚠ '{r['city']}' non trovata — saltata.")

    if not found:
        print(Style.BRIGHT + Fore.RED + "Nessuna città valida trovata." + Style.RESET_ALL)
        return

    print()
    if previsione:
        for r in found:
            forecast = get_forecast(r["lat"], r["lon"], days=5)
            print_forecast(r["city"], forecast)
    else:
        coords_list  = [(r["lat"], r["lon"]) for r in found]
        weather_list = get_weather_batch(coords_list)
        for r, data in zip(found, weather_list):
            print_weather(r["city"], data)


if __name__ == "__main__":
    main()
