"""Revisa el AndroidManifest.xml decodificado por apktool. Sirve cuando no hay MobSF.

Uso:
    apktool d app.apk -o recon/out/<sistema>/apktool
    python -m recon.mobile.manifest recon/out/<sistema>/apktool --sistema <sistema>

Revisa: app debuggable, allowBackup, tráfico en texto plano, componentes exportados sin
permiso (activity, service, receiver, provider) y pantallas de depuración incluidas en el APK.
"""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

from recon.findings import Finding, write_findings

ANDROID = "{http://schemas.android.com/apk/res/android}"
COMPONENTES = ("activity", "activity-alias", "service", "receiver", "provider")
PALABRAS_DEBUG = ("debug", "crash", "test", "dev")


def _nombre(paquete: str, nombre: str) -> str:
    return paquete + nombre if nombre.startswith(".") else nombre


def analyze(apktool_dir: Path) -> tuple[list[Finding], dict]:
    raiz = ET.parse(Path(apktool_dir) / "AndroidManifest.xml").getroot()
    paquete = raiz.get("package", "")
    app = raiz.find("application")
    app = app if app is not None else ET.Element("application")
    findings: list[Finding] = []

    if app.get(f"{ANDROID}debuggable") == "true":
        findings.append(Finding(
            id="manifest:debuggable", titulo="La app está compilada como debuggable",
            categoria="manifest", severidad="media", evidencia="visto", fuente="manifest",
            detalle="Normal en un build de pruebas; en producción permite adjuntar depuradores."))
    if app.get(f"{ANDROID}allowBackup") != "false":
        findings.append(Finding(
            id="manifest:allowBackup", titulo="allowBackup no está desactivado",
            categoria="manifest", severidad="baja", evidencia="visto", fuente="manifest",
            detalle="Los datos de la app se pueden respaldar y restaurar por adb. "
                    "Probar que la app maneje bien datos restaurados."))
    if app.get(f"{ANDROID}usesCleartextTraffic") == "true":
        findings.append(Finding(
            id="manifest:cleartext", titulo="Permite tráfico HTTP sin cifrar",
            categoria="red", severidad="media", evidencia="visto", fuente="manifest"))

    exportados, debug = [], []
    for tipo in COMPONENTES:
        for comp in app.iter(tipo):
            nombre = _nombre(paquete, comp.get(f"{ANDROID}name", ""))
            if any(p in nombre.rsplit(".", 1)[-1].lower() for p in PALABRAS_DEBUG):
                debug.append(nombre)
            exported = comp.get(f"{ANDROID}exported")
            tiene_filtro = comp.find("intent-filter") is not None
            es_exportado = exported == "true" or (exported is None and tiene_filtro)
            if not es_exportado or comp.get(f"{ANDROID}permission"):
                continue
            es_launcher = any(c.get(f"{ANDROID}name") == "android.intent.category.LAUNCHER"
                              for c in comp.iter("category"))
            if es_launcher:
                continue
            exportados.append(nombre)
            findings.append(Finding(
                id=f"exportado:{nombre}", titulo=f"{tipo} exportado sin permiso: {nombre.rsplit('.', 1)[-1]}",
                categoria="manifest", severidad="media", evidencia="inferido", fuente="manifest",
                ubicacion=nombre,
                detalle="Otra app puede abrirlo directamente. Probar abrirlo con adb "
                        "(am start / startservice / broadcast) sin pasar por el flujo normal.",
                extra={"tipo": tipo, "sin_exported_explicito": exported is None}))

    if debug:
        findings.append(Finding(
            id="manifest:componentes-debug", titulo=f"{len(debug)} componentes de depuración en el APK",
            categoria="manifest", severidad="info", evidencia="visto", fuente="manifest",
            detalle="Confirmar que no lleguen al build de producción.", extra={"componentes": sorted(debug)}))

    resumen = {
        "paquete": paquete,
        "permisos": sorted(p.get(f"{ANDROID}name", "") for p in raiz.iter("uses-permission")),
        "exportados_sin_permiso": sorted(exportados),
    }
    return findings, resumen


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apktool_dir", type=Path)
    parser.add_argument("--sistema", required=True)
    parser.add_argument("--out", type=Path, default=Path("recon/out"))
    args = parser.parse_args(argv)
    findings, resumen = analyze(args.apktool_dir)
    destino = args.out / args.sistema / "manifest_findings.json"
    data = write_findings(destino, args.sistema, "manifest", findings, resumen)
    print(f"{data['total']} hallazgos ({data['nuevos']} nuevos) -> {destino}")


if __name__ == "__main__":
    main()
