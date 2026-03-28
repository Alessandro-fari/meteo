from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)  # abilita ANSI su Windows

WMO_CODES = {
    0:  ("Sereno",                "☀️ "),
    1:  ("Prev. sereno",          "🌤️ "),
    2:  ("Parz. nuvoloso",        "⛅ "),
    3:  ("Coperto",               "☁️ "),
    45: ("Nebbia",                "🌫️ "),
    48: ("Nebbia con brina",      "🌫️ "),
    51: ("Pioggerella leggera",   "🌦️ "),
    53: ("Pioggerella moderata",  "🌦️ "),
    55: ("Pioggerella intensa",   "🌧️ "),
    61: ("Pioggia leggera",       "🌧️ "),
    63: ("Pioggia moderata",      "🌧️ "),
    65: ("Pioggia intensa",       "🌧️ "),
    71: ("Neve leggera",          "❄️ "),
    73: ("Neve moderata",         "❄️ "),
    75: ("Neve intensa",          "❄️ "),
    80: ("Rovesci leggeri",       "🌦️ "),
    81: ("Rovesci moderati",      "🌧️ "),
    82: ("Rovesci violenti",      "⛈️ "),
    95: ("Temporale",             "⛈️ "),
    99: ("Temporale con grandine","⛈️ "),
}

DAYS_IT   = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
MONTHS_IT = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
             "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]


# ── Helpers colore ─────────────────────────────────────────────────────────────

def _temp_color(temp: float) -> str:
    if temp <= 0:   return Style.BRIGHT + Fore.BLUE
    if temp <= 10:  return Fore.CYAN
    if temp <= 20:  return Fore.GREEN
    if temp <= 30:  return Fore.YELLOW
    return Style.BRIGHT + Fore.RED

def _wind_color(speed: float) -> str:
    if speed <= 15: return Fore.GREEN
    if speed <= 30: return Fore.YELLOW
    return Style.BRIGHT + Fore.RED

def _rain_color(mm: float) -> str:
    if mm == 0:   return Style.DIM + Fore.WHITE
    if mm <= 2:   return Fore.CYAN
    if mm <= 10:  return Fore.BLUE
    return Style.BRIGHT + Fore.BLUE

def _format_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{DAYS_IT[dt.weekday()]} {dt.day:02d} {MONTHS_IT[dt.month - 1]}"

# Costante per il bordo del pannello (larghezza interna)
_PANEL_INNER = 60
_B = Fore.CYAN  # colore bordi


# ── Meteo attuale ──────────────────────────────────────────────────────────────

def print_weather(city: str, data: dict) -> None:
    """Stampa il meteo attuale in un pannello colorato con Colorama.

    Args:
        city (str):  Nome della città.
        data (dict): Dizionario con temperature, humidity, wind_speed, precipitation.
    """
    temp_code = _temp_color(data["temperature"])
    wind_code = _wind_color(data["wind_speed"])
    rain_code = _rain_color(data["precipitation"])

    W = _PANEL_INNER

    # ── Bordo superiore con titolo ─────────────────────────────────────────
    title_plain = f" 🌍 {city} "
    # stima larghezza visiva: emoji conta come 2 colonne
    title_vis = len(title_plain) + 1  # +1 per compensazione emoji
    dashes = max(0, W - title_vis - 2)
    left_d  = dashes // 2
    right_d = dashes - left_d
    print()
    print(_B + "╭" + "─" * left_d + Style.RESET_ALL
          + Style.BRIGHT + Fore.WHITE + title_plain + Style.RESET_ALL
          + _B + "─" * right_d + "╮" + Style.RESET_ALL)

    # ── Riga vuota ─────────────────────────────────────────────────────────
    print(_B + "│" + " " * W + "│" + Style.RESET_ALL)

    # ── Temperatura centrata ───────────────────────────────────────────────
    temp_plain = f"  {data['temperature']:.1f}°C  "
    temp_pad   = temp_plain.center(W)
    print(_B + "│" + Style.RESET_ALL
          + temp_code + Style.BRIGHT + temp_pad + Style.RESET_ALL
          + _B + "│" + Style.RESET_ALL)

    # ── Riga vuota ─────────────────────────────────────────────────────────
    print(_B + "│" + " " * W + "│" + Style.RESET_ALL)

    # ── Griglia 2x2 ───────────────────────────────────────────────────────
    COL = (W - 4) // 2  # larghezza di ogni metà (plain)

    hum_plain  = f"Umidità   {data['humidity']}%"
    rain_plain = f"Pioggia   {data['precipitation']:.1f} mm"
    wind_plain = f"Vento     {data['wind_speed']:.1f} km/h"
    app_plain  = f"Percepita {data['temperature']:.1f}°C"

    row1_left  = ("💧 " + hum_plain).ljust(COL)
    row1_right = "🌧️  " + rain_code + rain_plain + Style.RESET_ALL
    row2_left  = "💨 " + wind_code + wind_plain.ljust(COL - 3) + Style.RESET_ALL
    row2_right = "🌡️  " + temp_code + app_plain + Style.RESET_ALL

    print(_B + "│" + Style.RESET_ALL + "  " + row1_left + "  " + row1_right)
    print(_B + "│" + Style.RESET_ALL + "  " + row2_left + "  " + row2_right)

    # ── Riga vuota ─────────────────────────────────────────────────────────
    print(_B + "│" + " " * W + "│" + Style.RESET_ALL)

    # ── Bordo inferiore con sottotitolo ────────────────────────────────────
    sub_plain = " Meteo attuale "
    sub_vis   = len(sub_plain)
    dashes2   = max(0, W - sub_vis - 2)
    left_d2   = dashes2 // 2
    right_d2  = dashes2 - left_d2
    print(_B + "╰" + "─" * left_d2 + Style.RESET_ALL
          + Style.DIM + sub_plain + Style.RESET_ALL
          + _B + "─" * right_d2 + "╯" + Style.RESET_ALL)


# ── Previsione N giorni ────────────────────────────────────────────────────────

# Larghezze colonne (plain text, senza ANSI)
_COL_W = [13, 3, 19, 6, 6, 9, 9]


def _sep(left: str, mid: str, right: str, fill: str = "─") -> str:
    return _B + left + mid.join(fill * (w + 2) for w in _COL_W) + right + Style.RESET_ALL


def _cell(text_plain: str, width: int, align: str = "left", color: str = "") -> str:
    """Cella con padding calcolato su plain text, poi colore applicato."""
    padded = text_plain.ljust(width) if align == "left" else text_plain.rjust(width)
    return (color + padded + Style.RESET_ALL) if color else padded


def print_forecast(city: str, forecast: list) -> None:
    """Stampa la previsione meteo a N giorni come tabella colorata con Colorama.

    Args:
        city (str):            Nome della città.
        forecast (list[dict]): Lista di dati giornalieri da get_forecast().
    """
    headers = ["Data", "", "Condizione", "Min", "Max", "Pioggia", "Vento"]
    title   = f"🌍 {city}  —  Previsione {len(forecast)} giorni"

    total_inner = sum(_COL_W) + 3 * (len(_COL_W) - 1) + 2  # colonne + separatori + padding

    # ── Bordo superiore + titolo ───────────────────────────────────────────
    print()
    print(_B + "╭" + "─" * total_inner + "╮" + Style.RESET_ALL)
    # stima larghezza visiva titolo (emoji = +1 per compensazione)
    title_vis   = len(title) + 1
    title_pad   = title.center(total_inner - 2)
    print(_B + "│ " + Style.RESET_ALL
          + Style.BRIGHT + Fore.WHITE + title_pad + Style.RESET_ALL
          + _B + " │" + Style.RESET_ALL)

    # ── Separatore + header ────────────────────────────────────────────────
    print(_sep("├", "┬", "┤"))

    h_cells = []
    for i, h in enumerate(headers):
        align = "right" if i >= 3 else "left"
        h_cells.append(_cell(h, _COL_W[i], align, Style.BRIGHT + Fore.WHITE))
    print(_B + "│ " + Style.RESET_ALL
          + (_B + " │ " + Style.RESET_ALL).join(h_cells)
          + _B + " │" + Style.RESET_ALL)

    # ── Righe dati ─────────────────────────────────────────────────────────
    for day in forecast:
        print(_sep("├", "┼", "┤"))
        label, icon = WMO_CODES.get(day["weather_code"], ("Sconosciuto", "❓"))

        # Plain text per ogni cella (allineamento corretto)
        date_plain  = _format_date(day["date"])
        icon_plain  = icon.strip()
        cond_plain  = label
        min_plain   = f"{day['temp_min']:.0f}°C"
        max_plain   = f"{day['temp_max']:.0f}°C"
        rain_plain  = f"{day['precipitation']:.1f} mm"
        wind_plain  = f"{day['wind_speed']:.0f} km/h"

        cells = [
            _cell(date_plain, _COL_W[0], "left",  Style.BRIGHT),
            _cell(icon_plain, _COL_W[1], "left"),
            _cell(cond_plain, _COL_W[2], "left"),
            _cell(min_plain,  _COL_W[3], "right", _temp_color(day["temp_min"])),
            _cell(max_plain,  _COL_W[4], "right", _temp_color(day["temp_max"]) + Style.BRIGHT),
            _cell(rain_plain, _COL_W[5], "right", _rain_color(day["precipitation"])),
            _cell(wind_plain, _COL_W[6], "right", _wind_color(day["wind_speed"])),
        ]
        print(_B + "│ " + Style.RESET_ALL
              + (_B + " │ " + Style.RESET_ALL).join(cells)
              + _B + " │" + Style.RESET_ALL)

    # ── Bordo inferiore ────────────────────────────────────────────────────
    print(_sep("╰", "┴", "╯"))
