"""Formato común de hallazgos de reconocimiento.

Todos los scripts de `recon/` escriben un `findings.json` con esta forma. Es lo único que
lee el agente `app_recon`, así que debe ser corto: nada de cuerpos de respuesta, tokens,
secretos ni código descompilado completo.

Cada hallazgo lleva una `evidencia`:
- `visto`: se observó en ejecución (una respuesta 500, un crash).
- `inferido`: sale de análisis estático o de una regla; puede ser falso positivo.
- `desconocido`: no hay datos suficientes para afirmarlo.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

EVIDENCIAS = ("visto", "inferido", "desconocido")
SEVERIDADES = ("alta", "media", "baja", "info")


@dataclass
class Finding:
    id: str
    titulo: str
    categoria: str
    severidad: str
    evidencia: str
    fuente: str
    detalle: str = ""
    ubicacion: str = ""
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.evidencia not in EVIDENCIAS:
            raise ValueError(f"evidencia inválida: {self.evidencia!r}")
        if self.severidad not in SEVERIDADES:
            raise ValueError(f"severidad inválida: {self.severidad!r}")


def write_findings(path: Path, sistema: str, fuente: str, findings: list[Finding],
                   resumen: dict | None = None) -> dict:
    """Escribe el findings.json y marca qué hallazgos son nuevos respecto a la corrida previa."""
    path = Path(path)
    previos = set()
    if path.exists():
        try:
            previos = {f["id"] for f in json.loads(path.read_text(encoding="utf-8")).get("hallazgos", [])}
        except (json.JSONDecodeError, OSError):
            previos = set()
    orden = {s: i for i, s in enumerate(SEVERIDADES)}
    items = sorted(findings, key=lambda f: (orden[f.severidad], f.id))
    data = {
        "sistema": sistema,
        "fuente": fuente,
        "resumen": resumen or {},
        "total": len(items),
        "nuevos": sum(1 for f in items if f.id not in previos),
        "hallazgos": [{**asdict(f), "nuevo": f.id not in previos} for f in items],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
