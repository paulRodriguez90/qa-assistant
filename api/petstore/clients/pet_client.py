"""Cliente del recurso /pet (solo GET)."""
from urllib.parse import quote, urlencode

from playwright.sync_api import APIRequestContext, APIResponse, Error

# Reintento acotado solo para fallos transitorios de red o de gateway.
# El 500 no se reintenta: en esta API es un bug real (findByTags) y no debe ocultarse.
RETRY_STATUSES = (502, 503, 504)
MAX_ATTEMPTS = 2


class PetClient:
    def __init__(self, request: APIRequestContext):
        self._request = request

    def get(self, pet_id, headers: dict | None = None) -> APIResponse:
        return self._get(f"pet/{quote(str(pet_id), safe='')}", headers)

    def find_by_status(self, status=None, headers: dict | None = None) -> APIResponse:
        """`status` puede ser str, lista de str o None (parámetro ausente)."""
        return self._get(self._with_query("pet/findByStatus", "status", status), headers)

    def find_by_tags(self, tags=None, headers: dict | None = None) -> APIResponse:
        return self._get(self._with_query("pet/findByTags", "tags", tags), headers)

    def _get(self, url: str, headers: dict | None) -> APIResponse:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            last = attempt == MAX_ATTEMPTS
            try:
                resp = self._request.get(url, headers=headers)
            except Error:  # red o timeout
                if last:
                    raise
                continue
            if resp.status not in RETRY_STATUSES or last:
                return resp

    @staticmethod
    def _with_query(path: str, name: str, value) -> str:
        """Arma el query con parámetro repetido (explode=true) cuando `value` es lista."""
        if value is None:
            return path
        values = value if isinstance(value, (list, tuple)) else [value]
        return f"{path}?{urlencode([(name, v) for v in values])}"
