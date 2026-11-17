"""Busca crashes, ANR y excepciones de la app en un volcado de logcat.

Uso típico, mientras corren los tests de Appium o una exploración:
    adb logcat -c
    pytest mobile/<sistema>
    adb logcat -d -v threadtime > recon/out/<sistema>/logcat.txt
    python -m recon.mobile.logcat_summary recon/out/<sistema>/logcat.txt --paquete com.ejemplo.app --sistema <sistema>

Todo lo que reporta es evidencia `visto`: pasó en el dispositivo.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from recon.findings import Finding, write_findings

FATAL = re.compile(r"FATAL EXCEPTION")
PROCESO = re.compile(r"Process:\s*([\w.:]+)")
ANR = re.compile(r"ANR in (\S+)")
EXCEPCION = re.compile(r"((?:[a-zA-Z_$][\w$]*\.)+[A-Z][\w$]*(?:Exception|Error))(?::\s*(.*))?")
FRAME = re.compile(r"\bat\s+([\w$.]+)\(([^)]*)\)")


def analyze(texto: str, paquete: str) -> tuple[list[Finding], dict]:
    lineas = texto.splitlines()
    findings: dict[str, Finding] = {}
    conteo = {"crashes": 0, "anr": 0}

    for i, linea in enumerate(lineas):
        if FATAL.search(linea):
            bloque = []
            for b in lineas[i + 1:i + 60]:
                if FATAL.search(b) or "AndroidRuntime" not in b:
                    break
                bloque.append(b)
            proceso = next((m.group(1) for b in bloque[:3] if (m := PROCESO.search(b))), "")
            if proceso != paquete and not proceso.startswith(paquete + ":"):
                continue
            conteo["crashes"] += 1
            excepcion, mensaje, frame = "desconocida", "", ""
            for b in bloque:
                m = EXCEPCION.search(b)
                if m and excepcion == "desconocida":
                    excepcion, mensaje = m.group(1), (m.group(2) or "").strip()
                f = FRAME.search(b)
                if f and f.group(1).startswith(paquete):
                    frame = f"{f.group(1)}({f.group(2)})"
                    break
            fid = f"crash:{excepcion}:{frame}"
            previo = findings.get(fid)
            veces = (previo.extra.get("veces", 0) if previo else 0) + 1
            findings[fid] = Finding(
                id=fid, titulo=f"Crash: {excepcion.rsplit('.', 1)[-1]}", categoria="crash",
                severidad="alta", evidencia="visto", fuente="logcat", ubicacion=frame,
                detalle=mensaje[:300], extra={"excepcion": excepcion, "veces": veces})
        m = ANR.search(linea)
        if m and m.group(1).startswith(paquete):
            conteo["anr"] += 1
            fid = f"anr:{m.group(1)}"
            previo = findings.get(fid)
            veces = (previo.extra.get("veces", 0) if previo else 0) + 1
            findings[fid] = Finding(
                id=fid, titulo=f"ANR en {m.group(1)}", categoria="anr", severidad="alta",
                evidencia="visto", fuente="logcat", ubicacion=m.group(1),
                detalle="La app dejó de responder (hilo principal bloqueado).", extra={"veces": veces})
    return list(findings.values()), conteo


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logcat", type=Path)
    parser.add_argument("--paquete", required=True)
    parser.add_argument("--sistema", required=True)
    parser.add_argument("--out", type=Path, default=Path("recon/out"))
    args = parser.parse_args(argv)
    texto = args.logcat.read_text(encoding="utf-8", errors="replace")
    findings, resumen = analyze(texto, args.paquete)
    destino = args.out / args.sistema / "logcat_findings.json"
    data = write_findings(destino, args.sistema, "logcat", findings, resumen)
    print(f"{resumen['crashes']} crashes, {resumen['anr']} ANR -> {destino} ({data['nuevos']} nuevos)")


if __name__ == "__main__":
    main()
