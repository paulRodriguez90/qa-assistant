"""Plugin de pytest que graba el tráfico de los tests E2E de Playwright en un HAR mínimo.

No toca los conftest de los sitios. Se activa solo cuando se pide:
    pytest -p recon.web.har_plugin --recon-har recon/out/saucedemo/e2e.har web/saucedemo
    python -m recon.web.har_summary recon/out/saucedemo/e2e.har --sistema saucedemo

Guarda método, URL, status, tiempo, tipo de contenido y NOMBRES de headers de respuesta.
También guarda los errores de consola y excepciones JS de la página.
No guarda cuerpos ni valores de headers (cookies, tokens) y enmascara parámetros sensibles de la URL.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from recon.web.har_summary import mask_url

_entries: list[dict] = []
_consola: list[dict] = []


def pytest_addoption(parser):
    parser.addoption("--recon-har", default=None, help="ruta del HAR a escribir con el tráfico de los tests")


def _entry(request, test_id: str) -> dict | None:
    try:
        response = request.response()
    except Exception:
        return None
    if response is None:
        return None
    timing = request.timing or {}
    inicio, fin = timing.get("startTime", 0), timing.get("responseEnd", -1)
    try:
        headers = response.all_headers()
    except Exception:
        headers = {}
    return {
        "request": {"method": request.method, "url": mask_url(request.url)},
        "response": {
            "status": response.status,
            "headers": [{"name": n, "value": ""} for n in headers],
            "content": {"mimeType": headers.get("content-type", "")},
        },
        "time": fin if fin and fin > 0 else 0,
        "_test": test_id,
        "_inicio": inicio,
    }


@pytest.fixture(autouse=True)
def _recon_har(request):
    if not request.config.getoption("--recon-har") or "page" not in request.fixturenames:
        yield
        return
    context = request.getfixturevalue("context")
    pendientes = []

    def guardar(req):
        pendientes.append(req)

    def consola(msg):
        if msg.type == "error":
            _consola.append({"tipo": "console", "texto": msg.text[:300], "url": mask_url(page.url),
                             "_test": request.node.nodeid})

    def excepcion(error):
        _consola.append({"tipo": "pageerror", "texto": str(error)[:300], "url": mask_url(page.url),
                         "_test": request.node.nodeid})

    context.on("requestfinished", guardar)
    page = request.getfixturevalue("page")
    page.on("console", consola)
    page.on("pageerror", excepcion)
    yield
    for req in pendientes:
        entry = _entry(req, request.node.nodeid)
        if entry:
            _entries.append(entry)


def pytest_sessionfinish(session):
    destino = session.config.getoption("--recon-har")
    if not destino:
        return
    path = Path(destino)
    path.parent.mkdir(parents=True, exist_ok=True)
    har = {"log": {"version": "1.2", "creator": {"name": "qa-assistant recon"}, "entries": _entries,
                   "_consola": _consola}}
    path.write_text(json.dumps(har, ensure_ascii=False), encoding="utf-8")
