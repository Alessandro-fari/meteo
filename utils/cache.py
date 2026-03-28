import time
import json
import os
from pathlib import Path


class PersistentTTLCache:
    """Cache con scadenza TTL che persiste su file JSON tra un avvio e l'altro.

    A differenza di TTLCache (in-memory), questa classe salva i dati su disco
    in formato JSON. Al prossimo avvio dell'app, i dati precedenti vengono
    ricaricati e le voci ancora valide sono immediatamente disponibili senza
    nuove chiamate API.

    Usa `time.time()` (Unix timestamp assoluto) invece di `time.monotonic()`,
    perché i timestamp monotonic non hanno significato tra sessioni diverse.

    Attributes:
        ttl (float):        Secondi di validità per ogni voce.
        path (Path):        Percorso del file JSON su disco.
        offline_ttl (float): TTL esteso usato in modalità offline (default: 7 giorni).
        _store (dict):      Dizionario interno { chiave: (valore, saved_at) }.

    Example:
        >>> cache = PersistentTTLCache(ttl=600, path="weather_cache.json")
        >>> cache.set("roma", 22.4)
        >>> cache.get("roma")
        22.4
        >>> # dopo riavvio dell'app, i dati sono ancora disponibili se non scaduti
    """

    def __init__(self, ttl: float, path: str | Path, offline_ttl: float = 604_800):
        """Inizializza e carica la cache dal file se esiste.

        Args:
            ttl (float):          Secondi di validità in condizioni normali.
            path (str | Path):    Percorso del file JSON. Viene creato se assente.
            offline_ttl (float):  TTL esteso per modalità offline. Default: 7 giorni.
        """
        self.ttl         = ttl
        self.offline_ttl = offline_ttl
        self.path        = Path(path)
        self._store: dict = {}
        self._load()

    # ── Persistenza ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Carica la cache dal file JSON. Ignora silenziosamente file corrotti."""
        if not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._store = json.load(f)
        except (json.JSONDecodeError, OSError):
            self._store = {}

    def _save(self) -> None:
        """Salva la cache su file JSON. Ignora silenziosamente errori di I/O."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._store, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ── Operazioni CRUD ──────────────────────────────────────────────────────

    def set(self, key: str, value) -> None:
        """Salva un valore con timestamp Unix corrente e persiste su disco.

        Args:
            key (str): Chiave univoca.
            value:     Valore serializzabile in JSON (float, str, list, dict...).

        Example:
            >>> cache.set("coords_roma", [41.89, 12.48])
        """
        self._store[key] = {"value": value, "saved_at": time.time()}
        self._save()

    def get(self, key: str, offline: bool = False):
        """Recupera un valore se non scaduto, con supporto modalità offline.

        In modalità offline usa `offline_ttl` (più lungo) per permettere
        all'app di mostrare dati anche senza connessione, marcandoli come stale.

        Args:
            key (str):      Chiave da cercare.
            offline (bool): Se True, usa TTL esteso e ritorna anche dati scaduti.

        Returns:
            dict | None: {"value": ..., "stale": bool} se trovato, altrimenti None.
                - stale=False → dato fresco, dentro il TTL normale
                - stale=True  → dato scaduto ma servito in offline mode

        Example:
            >>> result = cache.get("coords_roma")
            >>> if result:
            ...     print(result["value"], "stale:", result["stale"])
            [41.89, 12.48] stale: False
        """
        entry = self._store.get(key)
        if entry is None:
            return None

        age = time.time() - entry["saved_at"]

        # Dato fresco: dentro il TTL normale
        if age <= self.ttl:
            return {"value": entry["value"], "stale": False}

        # Dato scaduto in modalità offline: servi con flag stale
        if offline and age <= self.offline_ttl:
            return {"value": entry["value"], "stale": True}

        # Dato scaduto in modalità online: rimuovi e considera cache miss
        if not offline:
            del self._store[key]
            self._save()

        return None

    def invalidate(self, key: str) -> None:
        """Rimuove manualmente una voce e aggiorna il file.

        Example:
            >>> cache.invalidate("coords_roma")
        """
        if key in self._store:
            del self._store[key]
            self._save()

    def clear(self) -> None:
        """Svuota la cache in memoria e cancella il file su disco.

        Example:
            >>> cache.clear()
        """
        self._store.clear()
        try:
            os.remove(self.path)
        except OSError:
            pass

    def purge_expired(self) -> int:
        """Rimuove le voci scadute dal file e ritorna il numero eliminato.

        Returns:
            int: Numero di voci rimosse.

        Example:
            >>> cache.purge_expired()
            3
        """
        now = time.time()
        expired = [k for k, v in self._store.items()
                   if now - v["saved_at"] > self.offline_ttl]
        for key in expired:
            del self._store[key]
        if expired:
            self._save()
        return len(expired)

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"PersistentTTLCache(ttl={self.ttl}s, path='{self.path}', entries={len(self._store)})"
