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


# Layouts que traen AndroidX, Material y otras librerías: no son pantallas de la app.
PREFIJOS_LIBRERIA = ("abc_", "notification_", "mtrl_", "design_", "material_", "m3_",
                     "select_dialog_", "support_simple_spinner", "fingerprint_", "browser_actions_",
                     "preference_", "exo_", "com_facebook_", "common_google_", "custom_dialog",
                     "ime_", "test_", "leak_canary_")


def es_de_libreria(nombre: str) -> bool:
    return nombre.startswith(PREFIJOS_LIBRERIA)


def analyze(res_root: Path, incluir_librerias: bool = False) -> tuple[list[Finding], dict]:
    """Recorre res/layout*/ y devuelve hallazgos únicos por layout + elemento.

    Las variantes de un mismo layout (layout/, layout-v22/, layout-land/...) se juntan en un
    solo hallazgo, con las carpetas en `extra["variantes"]`.
    """
    findings: dict[str, Finding] = {}
    inventario: dict[str, dict] = {}
    omitidos = 0
    for xml in sorted(Path(res_root).glob("res/layout*/*.xml")):
        nombre = xml.stem
        if not incluir_librerias and es_de_libreria(nombre):
            omitidos += 1
            continue
        try:
            arbol = ET.parse(xml)
        except ET.ParseError:
            continue
        variante = xml.parent.name
        pantalla = inventario.setdefault(nombre, {"ids": set(), "content_desc": set()})
        sin_id: dict[str, int] = {}
        for el in arbol.iter():
            tag = el.tag.rsplit(".", 1)[-1]
            rid = _id(el.get(f"{ANDROID}id"))
            desc = el.get(f"{ANDROID}contentDescription")
            texto = el.get(f"{ANDROID}text")
            if rid:
                pantalla["ids"].add(rid)
            if desc:
                pantalla["content_desc"].add(desc)
            clicable = el.get(f"{ANDROID}clickable") == "true" or tag in ("ImageButton", "FloatingActionButton")
            imagen = any(tag.endswith(t) for t in SIN_TEXTO)
            importante = el.get(f"{ANDROID}importantForAccessibility") != "no"
            if not (imagen and importante and not desc and not texto and (clicable or rid)):
                continue
            if rid:
                elemento = rid
            else:
                # Sin id: tag + orden dentro del layout, estable entre variantes y corridas.
                sin_id[tag] = sin_id.get(tag, 0) + 1
                elemento = f"{tag}#{sin_id[tag]}"
            fid = f"a11y:{nombre}:{elemento}"
            if fid in findings:
                variantes = findings[fid].extra.setdefault("variantes", [])
                if variante not in variantes:
                    variantes.append(variante)
                continue
            findings[fid] = Finding(
                id=fid, titulo=f"{tag} sin contentDescription en {nombre}",
                categoria="accesibilidad", severidad="baja" if not clicable else "media",
                evidencia="inferido", fuente="apktool", ubicacion=f"res/{variante}/{xml.name}",
                detalle="Sin texto ni descripción: TalkBack no lo anuncia y Appium no tiene "
                        "accessibility id. Puede que el código lo asigne en ejecución.",
                extra={"variantes": [variante]})
    pantallas = {n: {"ids": sorted(v["ids"]), "content_desc": sorted(v["content_desc"])}
                 for n, v in sorted(inventario.items()) if v["ids"] or v["content_desc"]}
    resumen = {"layouts": len(pantallas), "omitidos_de_librerias": omitidos, "pantallas": pantallas}
    return list(findings.values()), resumen


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apktool_dir", type=Path)
    parser.add_argument("--sistema", required=True)
    parser.add_argument("--out", type=Path, default=Path("recon/out"))
    parser.add_argument("--incluir-librerias", action="store_true",
                        help="no omitir layouts de AndroidX/Material (abc_, mtrl_, ...)")
    args = parser.parse_args(argv)
    findings, resumen = analyze(args.apktool_dir, args.incluir_librerias)
    destino = args.out / args.sistema / "layout_findings.json"
    data = write_findings(destino, args.sistema, "apktool", findings, resumen)
    print(f"{resumen['layouts']} layouts ({resumen['omitidos_de_librerias']} de librerías omitidos), {data['total']} hallazgos ({data['nuevos']} nuevos) -> {destino}")


if __name__ == "__main__":
    main()
