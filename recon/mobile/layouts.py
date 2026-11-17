"""Lee los layouts XML de un APK decompilado con apktool y saca ids y problemas de accesibilidad.

Uso:
    apktool d app.apk -o recon/out/<sistema>/apktool
    python -m recon.mobile.layouts recon/out/<sistema>/apktool --sistema <sistema>

Sirve para dos cosas:
- Inventario de `resource-id` y `content-desc` por pantalla, para los Screen Objects de Appium.
- Botones o imágenes clicables sin texto ni contentDescription: un lector de pantalla no
  puede anunciarlos y Appium no tiene accessibility id para encontrarlos.

Apps hechas con Jetpack Compose casi no tienen layouts XML: ahí este script dice poco y
conviene usar el árbol de Appium en ejecución.
"""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

from recon.findings import Finding, write_findings

ANDROID = "{http://schemas.android.com/apk/res/android}"
SIN_TEXTO = ("ImageButton", "ImageView", "FloatingActionButton")


def _id(valor: str | None) -> str | None:
    if not valor:
        return None
    return valor.split("/", 1)[-1]


def analyze(res_root: Path) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    inventario: dict[str, dict] = {}
    for xml in sorted(Path(res_root).glob("res/layout*/*.xml")):
        try:
            arbol = ET.parse(xml)
        except ET.ParseError:
            continue
        nombre = xml.stem
        ids, descs = [], []
        for el in arbol.iter():
            tag = el.tag.rsplit(".", 1)[-1]
            rid = _id(el.get(f"{ANDROID}id"))
            desc = el.get(f"{ANDROID}contentDescription")
            texto = el.get(f"{ANDROID}text")
            if rid:
                ids.append(rid)
            if desc:
                descs.append(desc)
            clicable = el.get(f"{ANDROID}clickable") == "true" or tag in ("ImageButton", "FloatingActionButton")
            imagen = any(tag.endswith(t) for t in SIN_TEXTO)
            importante = el.get(f"{ANDROID}importantForAccessibility") != "no"
            if imagen and importante and not desc and not texto and (clicable or rid):
                elemento = rid or tag
                findings.append(Finding(
                    id=f"a11y:{nombre}:{elemento}", titulo=f"{tag} sin contentDescription en {nombre}",
                    categoria="accesibilidad", severidad="baja" if not clicable else "media",
                    evidencia="inferido", fuente="apktool", ubicacion=f"res/{xml.parent.name}/{xml.name}",
                    detalle="Sin texto ni descripción: TalkBack no lo anuncia y Appium no tiene "
                            "accessibility id. Puede que el código lo asigne en ejecución."))
        if ids or descs:
            inventario[nombre] = {"ids": sorted(set(ids)), "content_desc": sorted(set(descs))}
    resumen = {"layouts": len(inventario), "pantallas": inventario}
    return findings, resumen


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apktool_dir", type=Path)
    parser.add_argument("--sistema", required=True)
    parser.add_argument("--out", type=Path, default=Path("recon/out"))
    args = parser.parse_args(argv)
    findings, resumen = analyze(args.apktool_dir)
    destino = args.out / args.sistema / "layout_findings.json"
    data = write_findings(destino, args.sistema, "apktool", findings, resumen)
    print(f"{resumen['layouts']} layouts, {data['total']} hallazgos ({data['nuevos']} nuevos) -> {destino}")


if __name__ == "__main__":
    main()
