# Reglas para pruebas web (E2E de navegador)

Complementan el `CLAUDE.md` raíz. Aplican a todo lo que está bajo `web/`.

## Stack
- `pytest-playwright` (API síncrona), Chromium por defecto.

## Estructura de un sitio
```
web/<nombre>/
├── __init__.py
├── conftest.py          # BASE_URL del sitio + fixtures (base_url, credentials...)
├── pages/               # Page Objects del sitio
│   ├── __init__.py
│   └── <pagina>_page.py
└── tests/
    ├── __init__.py
    ├── features/<flujo>.feature
    └── e2e/
        ├── __init__.py
        └── test_<flujo>.py
```
- `web/core/base_page.py` es la base compartida por todos los sitios. No dupliques `BasePage`.
- El `conftest.py` del sitio sobrescribe la fixture `base_url`:
  `BASE_URL = os.getenv("<NOMBRE>_BASE_URL", "<url por defecto>")`.

## Page Object Model
- Cada página vive en `web/<nombre>/pages/<pagina>_page.py`, hereda de `BasePage`
  y expone acciones de negocio (`login(user, pwd)`), no clics sueltos.
- Los tests nunca usan selectores directamente: solo llaman a métodos del Page Object.
- Un sitio no importa Page Objects de otro sitio.

## Selectores y esperas
- Orden de preferencia: `get_by_role`, `get_by_label`, `get_by_test_id`, `get_by_text`.
  CSS solo si no hay alternativa. Nunca XPath absoluto.
- Aserciones con `expect(...)` de Playwright (tienen espera automática).

## Ejemplos de referencia
Antes de escribir código nuevo, copia el estilo de:
- `web/core/base_page.py` y `web/saucedemo/pages/login_page.py`
- `web/saucedemo/conftest.py`
- `web/saucedemo/tests/e2e/test_login.py`
- `web/saucedemo/tests/features/login.feature`

## Comandos
- Todos los sitios: `pytest web`
- Un sitio: `pytest web/<nombre>`
- Con navegador visible: `pytest web --headed`
