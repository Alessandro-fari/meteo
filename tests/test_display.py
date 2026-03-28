from utils.display import print_weather, print_forecast


# ── Fixture dati ───────────────────────────────────────────────────────────────

WEATHER_DATA = {
    "temperature":   22.4,
    "humidity":      60,
    "wind_speed":    18.0,
    "precipitation":  0.0,
}

FORECAST_DATA = [
    {
        "date":          "2026-03-28",
        "weather_code":  0,
        "temp_min":      10.0,
        "temp_max":      22.0,
        "precipitation":  0.0,
        "wind_speed":    12.0,
    }
]


# ─────────────────────────────────────────────
# Test 1 — Formato standard
# ─────────────────────────────────────────────
def test_output_formato_standard(capsys):
    print_weather("Roma", WEATHER_DATA)

    catturato = capsys.readouterr()
    assert "Roma" in catturato.out
    assert "22.4" in catturato.out
    assert "°C" in catturato.out


# ─────────────────────────────────────────────
# Test 2 — Temperatura negativa
# ─────────────────────────────────────────────
def test_output_temperatura_negativa(capsys):
    data = {**WEATHER_DATA, "temperature": -5.0}
    print_weather("Oslo", data)

    catturato = capsys.readouterr()
    assert "Oslo" in catturato.out
    assert "-5.0" in catturato.out
    assert "°C" in catturato.out


# ─────────────────────────────────────────────
# Test 3 — Temperatura zero
# ─────────────────────────────────────────────
def test_output_temperatura_zero(capsys):
    data = {**WEATHER_DATA, "temperature": 0.0}
    print_weather("Reykjavik", data)

    catturato = capsys.readouterr()
    assert "Reykjavik" in catturato.out
    assert "0.0" in catturato.out
    assert "°C" in catturato.out


# ─────────────────────────────────────────────
# Test 4 — print_forecast mostra città
# ─────────────────────────────────────────────
def test_forecast_mostra_citta(capsys):
    print_forecast("Milano", FORECAST_DATA)

    catturato = capsys.readouterr()
    assert "Milano" in catturato.out


# ─────────────────────────────────────────────
# Test 5 — print_forecast mostra temperature
# ─────────────────────────────────────────────
def test_forecast_mostra_temperature(capsys):
    print_forecast("Firenze", FORECAST_DATA)

    catturato = capsys.readouterr()
    assert "10" in catturato.out   # temp_min
    assert "22" in catturato.out   # temp_max
    assert "°C" in catturato.out
