# Reglas para pruebas mobile

Complementan el `CLAUDE.md` raíz. Aplican a todo lo que está bajo `mobile/`.
Todavía no hay apps aquí; el primero que se agregue debe servir de ejemplo de referencia.

## Stack
- Pytest + Appium (`Appium-Python-Client`). Aún no está en `requirements.txt`:
  agrégalo en el mismo PR que la primera app.
- El servidor Appium y el dispositivo/emulador se configuran por variables de entorno
  (`<NOMBRE>_APPIUM_URL`, `<NOMBRE>_PLATFORM`, `<NOMBRE>_DEVICE`, `<NOMBRE>_APP_PATH`).

## Estructura de una app
```
mobile/<nombre>/
├── __init__.py
├── conftest.py          # capabilities + fixture `driver` (se cierra con yield)
├── screens/             # Screen Objects: <pantalla>_screen.py
│   ├── __init__.py
│   └── base_screen.py
└── tests/
    ├── __init__.py
    ├── features/<flujo>.feature
    └── e2e/
        ├── __init__.py
        └── test_<flujo>.py
```

## Screen Object Model
- Cada pantalla es una clase en `screens/` que hereda de `BaseScreen` y expone acciones de
  negocio, no taps sueltos. Los tests nunca usan localizadores directamente.
- Si la app es Android e iOS, un Screen Object por plataforma o localizadores por plataforma
  dentro del mismo, pero la API pública es la misma.

## Localizadores y esperas
- Orden de preferencia: accessibility id, id de recurso (Android) / name (iOS),
  UiAutomator / predicate string. XPath solo si no hay alternativa, y nunca absoluto.
- Esperas explícitas (`WebDriverWait` + condiciones) dentro de `BaseScreen`.
  Nada de esperas implícitas globales altas.

## Datos y entorno
- Cada test arranca la app en un estado conocido (reinstalar o limpiar datos en el fixture).
- Nunca usar cuentas o dispositivos personales.

## Comandos
- Todas las apps: `pytest mobile`
- Una app: `pytest mobile/<nombre>`
