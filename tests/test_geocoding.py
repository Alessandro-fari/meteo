from unittest.mock import MagicMock, patch

import pytest
import requests

from utils.geocoding import get_coordinates


# ─────────────────────────────────────────────
# Helper: costruisce una risposta HTTP fasulla
# ─────────────────────────────────────────────
def make_response(json_data, status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status.return_value = None  # nessun errore di default
    return mock_resp


# ─────────────────────────────────────────────
# Test 1 — Città valida → restituisce (lat, lon)
# ─────────────────────────────────────────────
@patch("utils.geocoding.requests.get")
def test_citta_valida_restituisce_coordinate(mock_get):
    mock_get.return_value = make_response({
        "results": [{"latitude": 41.89474, "longitude": 12.48232, "name": "Roma"}]
    })

    risultato = get_coordinates("Roma")

    assert risultato == (41.89474, 12.48232)
    mock_get.assert_called_once()  # verifica che l'API sia stata chiamata


# ─────────────────────────────────────────────
# Test 2 — Città non trovata (chiave "results" assente) → None
# ─────────────────────────────────────────────
@patch("utils.geocoding.requests.get")
def test_citta_non_trovata_senza_chiave_results(mock_get):
    mock_get.return_value = make_response({})  # API restituisce oggetto vuoto

    risultato = get_coordinates("CittàInesistente")

    assert risultato is None


# ─────────────────────────────────────────────
# Test 3 — Città non trovata (results lista vuota) → None
# ─────────────────────────────────────────────
@patch("utils.geocoding.requests.get")
def test_citta_non_trovata_con_results_vuoto(mock_get):
    mock_get.return_value = make_response({"results": []})

    risultato = get_coordinates("xyz123")

    assert risultato is None


# ─────────────────────────────────────────────
# Test 4 — Errore HTTP 500 → propaga HTTPError
# ─────────────────────────────────────────────
@patch("utils.geocoding.requests.get")
def test_errore_http_propaga_eccezione(mock_get):
    mock_resp = make_response({}, status_code=500)
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mock_get.return_value = mock_resp

    with pytest.raises(requests.exceptions.HTTPError):
        get_coordinates("Roma")


# ─────────────────────────────────────────────
# Test 5 — Errore di rete → propaga ConnectionError
# ─────────────────────────────────────────────
@patch("utils.geocoding.requests.get")
def test_errore_di_rete_propaga_eccezione(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("Nessuna connessione")

    with pytest.raises(requests.exceptions.ConnectionError):
        get_coordinates("Roma")
