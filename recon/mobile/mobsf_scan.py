"""Escanea un APK con MobSF (análisis estático) y resume el reporte en hallazgos.

Requiere MobSF corriendo (Docker) y su API key:
    docker run -it --rm -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest

Uso:
    python -m recon.mobile.mobsf_scan <app.apk> --sistema mi_app
    python -m recon.mobile.mobsf_scan --reporte reporte.json --sistema mi_app   # sin MobSF

Variables: MOBSF_URL (por defecto http://localhost:8000) y MOBSF_API_KEY.
Escribe `recon/out/<sistema>/mobsf_report.json` (completo, no lo lee Claude) y
`recon/out/<sistema>/mobile_findings.json` (resumen).
Los secretos encontrados se cuentan, nunca se copian.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from recon.findings import Finding, write_findings

SEVERIDAD = {"high": "alta", "warning": "media", "medium": "media", "low": "baja",
             "info": "info", "hotspot": "baja"}


def _sev(valor: str | None) -> str | None:
    return SEVERIDAD.get((valor or "").lower())


def _items(seccion, clave: str) -> list:
    """MobSF cambia la forma de algunas secciones entre versiones: lista o dict con una lista."""
    if isinstance(seccion, dict):
        seccion = seccion.get(clave, [])
    return seccion if isinstance(seccion, list) else []


def summarize(report: dict) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []

    peligrosos = sorted(p for p, info in (report.get("permissions") or {}).items()
                        if isinstance(info, dict) and info.get("status") == "dangerous")
    if peligrosos:
        findings.append(Finding(
            id="permisos-peligrosos", titulo=f"{len(peligrosos)} permisos peligrosos",
            categoria="permisos", severidad="info", evidencia="inferido", fuente="mobsf",
            detalle="Verifica que cada uno tenga un flujo de permiso probado (aceptar y denegar).",
            extra={"permisos": peligrosos}))

    for i, m in enumerate(_items(report.get("manifest_analysis"), "manifest_findings")):
        sev = _sev(m.get("severity") or m.get("stat"))
        if not sev or sev == "info":
            continue
        regla = m.get("rule") or m.get("title") or f"manifest-{i}"
        componente = m.get("component") or ""
        if isinstance(componente, list):
            componente = ", ".join(map(str, componente))
        findings.append(Finding(
            id=f"manifest:{regla}:{componente}"[:200], titulo=str(m.get("title") or regla)[:160],
            categoria="manifest", severidad=sev, evidencia="inferido", fuente="mobsf",
            ubicacion=str(componente)[:200], detalle=str(m.get("description") or "")[:400]))

    codigo = report.get("code_analysis") or {}
    reglas = codigo.get("findings", codigo) if isinstance(codigo, dict) else {}
    for regla, info in reglas.items():
        if not isinstance(info, dict) or "metadata" not in info:
            continue
        meta = info.get("metadata") or {}
        sev = _sev(meta.get("severity"))
        if not sev or sev == "info":
            continue
        archivos = sorted((info.get("files") or {}).keys())
        findings.append(Finding(
            id=f"codigo:{regla}", titulo=str(meta.get("description") or regla)[:160],
            categoria="codigo", severidad=sev, evidencia="inferido", fuente="mobsf",
            ubicacion=", ".join(archivos[:3]) + (f" y {len(archivos) - 3} más" if len(archivos) > 3 else ""),
            extra={"cwe": meta.get("cwe", ""), "archivos": len(archivos)}))

    for i, n in enumerate(_items(report.get("network_security"), "network_findings")):
        sev = _sev(n.get("severity"))
        if not sev or sev == "info":
            continue
        findings.append(Finding(
            id=f"red:{n.get('scope') or i}"[:200], titulo=str(n.get("description") or "Configuración de red")[:160],
            categoria="red", severidad=sev, evidencia="inferido", fuente="mobsf",
            ubicacion=str(n.get("scope") or "")[:200]))

    secretos = report.get("secrets") or []
    if secretos:
        findings.append(Finding(
            id="secretos", titulo=f"{len(secretos)} posibles secretos en el código",
            categoria="seguridad", severidad="media", evidencia="inferido", fuente="mobsf",
            detalle="Revisar en mobsf_report.json (no se copian aquí). Muchos son falsos positivos."))

    resumen = {
        "app": report.get("app_name"),
        "paquete": report.get("package_name"),
        "version": report.get("version_name"),
        "min_sdk": report.get("min_sdk"),
        "target_sdk": report.get("target_sdk"),
        "actividades": len(report.get("activities") or []),
        "exportados": report.get("exported_count") or {},
        "puntaje_seguridad": (report.get("appsec") or {}).get("security_score"),
    }
    return findings, resumen


def scan(apk: Path, url: str, api_key: str) -> dict:
    import requests

    headers = {"Authorization": api_key}
    with apk.open("rb") as fh:
        subida = requests.post(f"{url}/api/v1/upload", headers=headers,
                               files={"file": (apk.name, fh, "application/octet-stream")}, timeout=300)
    subida.raise_for_status()
    hash_ = subida.json()["hash"]
    requests.post(f"{url}/api/v1/scan", headers=headers, data={"hash": hash_}, timeout=1800).raise_for_status()
    reporte = requests.post(f"{url}/api/v1/report_json", headers=headers, data={"hash": hash_}, timeout=300)
    reporte.raise_for_status()
    return reporte.json()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path, nargs="?")
    parser.add_argument("--reporte", type=Path, help="reporte JSON de MobSF ya descargado")
    parser.add_argument("--sistema", required=True)
    parser.add_argument("--out", type=Path, default=Path("recon/out"))
    args = parser.parse_args(argv)
    destino = args.out / args.sistema

    if args.reporte:
        report = json.loads(args.reporte.read_text(encoding="utf-8"))
    elif args.apk:
        api_key = os.getenv("MOBSF_API_KEY")
        if not api_key:
            parser.error("Falta MOBSF_API_KEY (está en MobSF > API Docs).")
        report = scan(args.apk, os.getenv("MOBSF_URL", "http://localhost:8000").rstrip("/"), api_key)
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "mobsf_report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    else:
        parser.error("Indica un APK o --reporte.")

    findings, resumen = summarize(report)
    data = write_findings(destino / "mobile_findings.json", args.sistema, "mobsf", findings, resumen)
    print(f"{data['total']} hallazgos ({data['nuevos']} nuevos) -> {destino / 'mobile_findings.json'}")


if __name__ == "__main__":
    main()
