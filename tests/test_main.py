from unittest.mock import patch

from main import main


# ─────────────────────────────────────────────
# Test 1 — Flusso completo OK
# ─────────────────────────────────────────────
@patch("main.print_weather")
@patch("main.get_temperature", return_value=22.4)
@patch("main.get_coordinates", return_value=(41.89, 12.48))
@patch("builtins.input", return_value="Roma")
def test_flusso_completo(mock_input, mock_coords, mock_temp, mock_display):
    main()

    mock_coords.assert_called_once_with("Roma")
    mock_temp.assert_called_once_with(41.89, 12.48)
    mock_display.assert_called_once_with("Roma", 22.4)


# ─────────────────────────────────────────────
# Test 2 — Città non trovata → messaggio errore, weather non chiamato
# ─────────────────────────────────────────────
@patch("main.get_temperature")
@patch("main.get_coordinates", return_value=None)
@patch("builtins.input", return_value="CittàInesistente")
def test_citta_non_trovata(mock_input, mock_coords, mock_temp, capsys):
    main()

    catturato = capsys.readouterr()
    assert "non trovata" in catturato.out
    mock_temp.assert_not_called()  # weather NON deve essere chiamato


# ─────────────────────────────────────────────
# Test 3 — Input vuoto → messaggio errore, nessuna API chiamata
# ─────────────────────────────────────────────
@patch("main.get_coordinates")
@patch("builtins.input", return_value="")
def test_input_vuoto(mock_input, mock_coords, capsys):
    main()

    catturato = capsys.readouterr()
    assert "valido" in catturato.out
    mock_coords.assert_not_called()  # geocoding NON deve essere chiamato
