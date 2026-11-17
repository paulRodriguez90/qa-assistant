# Reglas de reconocimiento (`recon/`)

Complementan el `CLAUDE.md` raíz. `recon/` tiene los scripts que analizan una app por dentro
(estático) y por fuera (dinámico) para **encontrar bugs**. Los usa el agente `app_recon`.

## Límites
- Solo apps propias, de un cliente con autorización escrita, o apps de práctica hechas para
  pruebas. Sin autorización clara, no se analiza.
- Solo entornos de prueba (staging, QA, emulador). Nunca producción.
- El objetivo son hallazgos y tests. No se copia código, assets ni diseño de la app.

## Estructura
```
recon/
├── findings.py            # formato común de hallazgos (findings.json)
├── web/
│   ├── har_plugin.py      # pytest -p recon.web.har_plugin --recon-har <ruta>
│   └── har_summary.py     # HAR -> web_findings.json
├── mobile/
│   ├── mobsf_scan.py      # APK -> MobSF -> mobile_findings.json
│   ├── layouts.py         # salida de apktool -> layout_findings.json
│   └── logcat_summary.py  # logcat -> logcat_findings.json (crashes, ANR)
├── tests/                 # tests de los scripts, sin red ni dispositivo
└── out/<sistema>/         # salidas. En .gitignore, nunca se versiona
```

## Convenciones
- Cada script escribe un `*_findings.json` corto con `recon.findings.write_findings`.
  Es lo único que debe leer un agente.
- Cada hallazgo lleva `evidencia`: `visto`, `inferido` o `desconocido`.
- Nunca se guardan cuerpos de respuesta, valores de headers, secretos ni datos personales
  en un findings.json. Los parámetros sensibles de una URL se enmascaran.
- Variables: `MOBSF_URL`, `MOBSF_API_KEY` (documentadas en `.env.example`).

## Herramientas externas (fuera de requirements.txt)
MobSF (Docker), jadx, apktool, adb, mitmproxy, schemathesis, frida-tools y objection.
Los scripts que las usan fallan con un mensaje claro si no están.
