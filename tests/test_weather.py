from unittest.mock import MagicMock, patch

import pytest
import requests

from utils.weather import get_temperature


# ─────────────────────────────────────────────
# Helper: costruisce una risposta HTTP fasulla
# ─────────────────────────────────────────────
def make_response(json_data, status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status.return_value = None
    return mock_resp


# ─────────────────────────────────────────────
# Test 1 — Coordinate valide → restituisce temperatura
# ─────────────────────────────────────────────
@patch("utils.weather.requests.get")
def test_coordinate_valide_restituisce_temperatura(mock_get):
    mock_get.return_value = make_response({
        "current_weather": {"temperature": 22.4, "weathercode": 0, "windspeed": 10.2}
    })

    risultato = get_temperature(41.89, 12.48)

    assert risultato == 22.4
    mock_get.assert_called_once()


# ─────────────────────────────────────────────
# Test 2 — Temperatura negativa → valore corretto
# ─────────────────────────────────────────────
@patch("utils.weather.requests.get")
def test_temperatura_negativa(mock_get):
    mock_get.return_value = make_response({
        "current_weather": {"temperature": -5.0, "weathercode": 71, "windspeed": 20.0}
    })

    risultato = get_temperature(59.91, 10.75)  # Oslo

    assert risultato == -5.0


# ─────────────────────────────────────────────
# Test 3 — Errore HTTP 500 → propaga HTTPError
# ─────────────────────────────────────────────
@patch("utils.weather.requests.get")
def test_errore_http_propaga_eccezione(mock_get):
    mock_resp = make_response({}, status_code=500)
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mock_get.return_value = mock_resp

    with pytest.raises(requests.exceptions.HTTPError):
        get_temperature(41.89, 12.48)


# ─────────────────────────────────────────────
# Test 4 — Errore di rete → propaga ConnectionError
# ─────────────────────────────────────────────
@patch("utils.weather.requests.get")
def test_errore_di_rete_propaga_eccezione(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("Nessuna connessione")

    with pytest.raises(requests.exceptions.ConnectionError):
        get_temperature(41.89, 12.48)


# ─────────────────────────────────────────────
# Test 5 — Risposta malformata (manca current_weather) → KeyError
# ─────────────────────────────────────────────
@patch("utils.weather.requests.get")
def test_risposta_malformata_lancia_key_error(mock_get):
    mock_get.return_value = make_response({"hourly": {}})  # manca "current_weather"

    with pytest.raises(KeyError):
        get_temperature(41.89, 12.48)
