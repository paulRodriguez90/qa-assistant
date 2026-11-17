"""Resume un archivo HAR (tráfico capturado con mitmproxy o Playwright) en hallazgos.

Uso:
    python -m recon.web.har_summary <archivo.har> --sistema saucedemo

Escribe `recon/out/<sistema>/web_findings.json`. Nunca copia cuerpos ni valores de headers:
solo método, ruta, status y tiempos.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from recon.findings import Finding, write_findings

LENTO_MS = 2000
PARAMS_SENSIBLES = {"password", "pass", "pwd", "token", "access_token", "api_key", "apikey",
                    "secret", "session", "sessionid", "auth", "card", "cvv"}
HEADERS_SEGURIDAD = ("content-security-policy", "strict-transport-security", "x-content-type-options")
HOSTS_LOCALES = ("localhost", "127.0.0.1", "10.0.2.2")


def mask_url(url: str) -> str:
    """Reemplaza el valor de los parámetros sensibles de la URL por ***."""
    partes = urlsplit(url)
    if not partes.query:
        return url
    query = [(k, "***" if k.lower() in PARAMS_SENSIBLES else v)
             for k, v in parse_qsl(partes.query, keep_blank_values=True)]
    return urlunsplit(partes._replace(query=urlencode(query, safe="*")))


def _ruta(url: str) -> tuple[str, str, str]:
    partes = urlsplit(url)
    return partes.scheme, partes.netloc, partes.path or "/"


def summarize(har: dict) -> tuple[list[Finding], dict]:
    entries = har.get("log", {}).get("entries", [])
    endpoints: dict[str, dict] = defaultdict(lambda: {"llamadas": 0, "status": set()})
    findings: dict[str, Finding] = {}
    hosts_https: set[str] = set()
    hosts_sin_headers: dict[str, list[str]] = {}

    for e in entries:
        req, resp = e.get("request", {}), e.get("response", {})
        metodo = req.get("method", "GET").upper()
        esquema, host, ruta = _ruta(req.get("url", ""))
        status = int(resp.get("status") or 0)
        clave = f"{metodo} {host}{ruta}"
        endpoints[clave]["llamadas"] += 1
        endpoints[clave]["status"].add(status)

        if status >= 500:
            fid = f"http-5xx:{clave}"
            findings.setdefault(fid, Finding(
                id=fid, titulo=f"{clave} respondió {status}", categoria="error-servidor",
                severidad="alta", evidencia="visto", fuente="har", ubicacion=clave,
                detalle="Error del servidor durante el flujo capturado."))
        elif 400 <= status < 500 and status not in (401, 403, 404):
            fid = f"http-4xx:{clave}:{status}"
            findings.setdefault(fid, Finding(
                id=fid, titulo=f"{clave} respondió {status}", categoria="error-cliente",
                severidad="media", evidencia="visto", fuente="har", ubicacion=clave,
                detalle="La app envió una petición que el servidor rechazó en un flujo normal."))

        tiempo = float(e.get("time") or 0)
        if tiempo > LENTO_MS:
            fid = f"lento:{clave}"
            previo = findings.get(fid)
            if previo is None or tiempo > previo.extra.get("ms", 0):
                findings[fid] = Finding(
                    id=fid, titulo=f"{clave} tardó {int(tiempo)} ms", categoria="rendimiento",
                    severidad="baja", evidencia="visto", fuente="har", ubicacion=clave,
                    detalle=f"Supera el umbral de {LENTO_MS} ms.", extra={"ms": int(tiempo)})

        sensibles = sorted({k for k, _ in parse_qsl(urlsplit(req.get("url", "")).query)
                            if k.lower() in PARAMS_SENSIBLES})
        if sensibles:
            fid = f"dato-sensible-url:{clave}"
            findings.setdefault(fid, Finding(
                id=fid, titulo=f"Parámetros sensibles en la URL de {clave}", categoria="seguridad",
                severidad="media", evidencia="visto", fuente="har", ubicacion=clave,
                detalle="Quedan en logs y en el historial. Parámetros: " + ", ".join(sensibles)))

        if esquema == "http" and host and host.split(":")[0] not in HOSTS_LOCALES:
            fid = f"http-plano:{host}"
            findings.setdefault(fid, Finding(
                id=fid, titulo=f"Tráfico sin cifrar hacia {host}", categoria="seguridad",
                severidad="media", evidencia="visto", fuente="har", ubicacion=host))
        if esquema == "https" and host and host not in hosts_https:
            hosts_https.add(host)
            mime = (resp.get("content", {}) or {}).get("mimeType", "")
            if "html" in mime:
                presentes = {h.get("name", "").lower() for h in resp.get("headers", [])}
                faltan = [h for h in HEADERS_SEGURIDAD if h not in presentes]
                if faltan:
                    hosts_sin_headers[host] = faltan

    for host, faltan in hosts_sin_headers.items():
        fid = f"headers-seguridad:{host}"
        findings[fid] = Finding(
            id=fid, titulo=f"Faltan headers de seguridad en {host}", categoria="seguridad",
            severidad="baja", evidencia="visto", fuente="har", ubicacion=host,
            detalle="Faltan: " + ", ".join(faltan))

    for c in har.get("log", {}).get("_consola", []):
        _, host, ruta = _ruta(c.get("url", ""))
        texto = c.get("texto", "")
        fid = f"consola:{host}{ruta}:{texto[:80]}"
        findings.setdefault(fid, Finding(
            id=fid, titulo=f"Error JS en {host}{ruta}", categoria="error-consola",
            severidad="alta" if c.get("tipo") == "pageerror" else "media", evidencia="visto",
            fuente="har", ubicacion=f"{host}{ruta}", detalle=texto[:300],
            extra={"test": c.get("_test", "")}))

    resumen = {
        "peticiones": len(entries),
        "endpoints": {k: {"llamadas": v["llamadas"], "status": sorted(v["status"])}
                      for k, v in sorted(endpoints.items())},
    }
    return list(findings.values()), resumen


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("har", type=Path)
    parser.add_argument("--sistema", required=True)
    parser.add_argument("--out", type=Path, default=Path("recon/out"))
    args = parser.parse_args(argv)
    har = json.loads(args.har.read_text(encoding="utf-8"))
    findings, resumen = summarize(har)
    data = write_findings(args.out / args.sistema / "web_findings.json", args.sistema, "har",
                          findings, resumen)
    print(f"{data['total']} hallazgos ({data['nuevos']} nuevos) -> "
          f"{args.out / args.sistema / 'web_findings.json'}")


if __name__ == "__main__":
    main()
