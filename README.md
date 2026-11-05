# QA Assistant

Framework de agentes de QA construido sobre **Claude Code**. Cada agente es un archivo
markdown con un rol y una lista de herramientas; el código de tests que generan sigue
Pytest + Playwright con Page Object Model.

Hay 6 agentes de QA: crear tests E2E y de API, reparar tests rotos, analizar fallos,
generar datos de prueba y revisar la cobertura de un PR. Ver [Agentes disponibles](#4-agentes-disponibles).

---

## 1. Cómo se guarda un agente

Todo es texto versionado en Git, igual que un framework de tests:

```
qa-assistant/
├── CLAUDE.md                  # Reglas del proyecto. Las leen TODOS los agentes.
├── .mcp.json                  # Herramientas externas (Playwright MCP). Se declaran una vez.
├── .claude/
│   ├── settings.json          # Permisos: qué puede y qué no puede hacer Claude.
│   └── agents/                # Un agente = un archivo. Encabezado + instrucciones.
│       ├── explorer.md
│       ├── self_healing.md
│       ├── api_tester.md
│       ├── ci_failure_analyzer.md
│       ├── test_data_generator.md
│       └── pr_coverage_reviewer.md
├── conftest.py                # Común: solo carga .env
├── web/                       # Pruebas E2E de navegador
│   ├── CLAUDE.md              # Reglas web (POM, selectores, Playwright)
│   ├── core/base_page.py      # BasePage compartida por todos los sitios
│   └── saucedemo/             # Un sitio = una carpeta
│       ├── conftest.py        # BASE_URL y fixtures del sitio
│       ├── pages/             # Page Objects (ejemplo que el agente imita)
│       └── tests/
│           ├── features/      # Casos en Gherkin
│           └── e2e/           # Tests Pytest + Playwright
├── api/CLAUDE.md              # Reglas para pruebas de API
├── mobile/CLAUDE.md           # Reglas para pruebas mobile
├── .github/workflows/
│   ├── tests.yml              # Smoke de saucedemo en cada PR y push a main
│   └── explorer.yml           # Cómo correr el agente explorer en CI
└── .env.example               # Plantilla de variables. El .env real no se sube.
```

### Anatomía de `.claude/agents/explorer.md`

```markdown
---
name: explorer                       # cómo lo llamas
description: Explora una web y...    # Claude usa esto para decidir cuándo delegarle
tools: Read, Write, mcp__playwright__browser_navigate, ...   # mínimo privilegio
model: sonnet
---
Eres un QA Automation Engineer senior...   # el rol y el proceso paso a paso
```

Las tres capas y para qué sirve cada una:

| Archivo | Qué contiene | Analogía en tu framework de tests |
|---|---|---|
| `CLAUDE.md` | Reglas comunes, estructura, comandos | El README de convenciones del equipo |
| `web/`, `api/`, `mobile/` `CLAUDE.md` | Reglas de ese tipo de prueba | La guía de cada capa de tests |
| `.claude/agents/*.md` | Rol + proceso + herramientas de un agente | Una suite con su propósito |
| `.mcp.json` | Conexión a herramientas externas | Los drivers (WebDriver, Appium server) |

## 2. Cómo se usa

### En tu PC

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env            # completa los valores
npm install -g @anthropic-ai/claude-code
claude                          # abre Claude Code en esta carpeta
```

La primera vez Claude Code te pregunta si confías en el servidor `playwright` de `.mcp.json`.
Después le pides, en lenguaje natural:

```
Usa el agente explorer sobre https://www.saucedemo.com y cubre el flujo de carrito
```

Con `/agents` ves y editas los agentes disponibles. Al terminar tendrás un `.feature`,
Page Objects y tests nuevos dentro de `web/<sitio>/`; revisa el diff y corre `pytest`.

### En CI

`.github/workflows/tests.yml` corre en cada PR y en cada push a `main`: instala las
dependencias y Chromium y ejecuta `pytest web/saucedemo -m smoke`. Si algún test falla,
sube los screenshots y traces de `test-results/` como artifact del run (se guardan 14 días).
Para ver un trace descargado: `playwright show-trace <ruta>/trace.zip`.

El mismo agente corre sin interfaz con `claude -p "..."`. El workflow
`.github/workflows/explorer.yml` lo lanza a mano con una URL, y al final abre un PR con
los tests generados. En Jenkins o GitLab es igual: un paso que instala Claude Code, define
`ANTHROPIC_API_KEY` como credencial secreta y ejecuta el mismo comando.

### Correr los tests de ejemplo

```bash
pytest              # toda la suite
pytest web/saucedemo  # un solo sitio
pytest -m smoke     # solo smoke
pytest --headed     # viendo el navegador
```

## 3. Buenas prácticas aplicadas aquí

1. **Un agente, una responsabilidad.** El explorer solo explora y genera tests.
2. **Mínimo privilegio.** El agente lista exactamente qué herramientas usa; `settings.json`
   bloquea leer `.env` y hacer `git push`.
3. **Propone, no decide.** En CI abre un PR; un humano revisa y hace merge.
4. **Ejemplos en vez de explicaciones.** `web/saucedemo/pages/login_page.py` y
   `web/saucedemo/tests/e2e/test_login.py`
   son el estilo que el agente copia. Si cambias el ejemplo, cambias lo que genera.
5. **Secretos fuera del repo.** `.env` local y secretos del CI.
6. **Sin código hasta que haga falta.** Hoy todo es markdown. Si un agente necesita lógica
   propia (reintentos, integrar Jira con reglas específicas), se pasa al Claude Agent SDK
   en Python.
7. **Evaluar al agente.** Corre el explorer sobre la misma app varias veces y mide: ¿los
   tests pasan? ¿son estables en 3 corridas seguidas? ¿respetan el POM?

> Nota: `.mcp.json` usa `@playwright/mcp@latest` para empezar rápido. En un proyecto real
> fija una versión concreta para que el agente no cambie de comportamiento sin aviso.

## 4. Agentes disponibles

Se invocan en lenguaje natural desde Claude Code, nombrando el agente. Ninguno hace
commit, push ni merge: dejan los cambios para que una persona los revise.

| Agente | Para qué sirve | Ejemplo de pedido |
|---|---|---|
| `explorer` | Explora una web con Playwright MCP, propone casos en Gherkin y genera tests Pytest + Playwright con Page Object Model. | `Usa explorer sobre https://www.saucedemo.com y cubre el flujo de carrito` |
| `self_healing` | Repara tests E2E rotos por cambios de UI ("locator not found", timeouts, "strict mode violation"): mira la página real y corrige el Page Object. | `Usa self_healing para revisar que los selectores de web/saucedemo/pages/login_page.py sigan funcionando` |
| `api_tester` | Genera tests de API desde un OpenAPI/Swagger, una colección de Postman o una URL: camino feliz, contrato, negativos y seguridad básica. | `Usa api_tester sobre https://petstore3.swagger.io/api/v3/openapi.json. Servicio petstore, solo el recurso pet y solo GET` |
| `ci_failure_analyzer` | Analiza fallos de Pytest (consola, junit XML, logs de CI), separa flaky, bugs reales y errores del test, y redacta los tickets. | `Usa ci_failure_analyzer sobre pytest api/petstore` |
| `test_data_generator` | Genera datos de prueba sintéticos y casos límite como factories Python o JSON/CSV, listos para parametrizar tests. | `Usa test_data_generator para web/saucedemo: datos del checkout (nombre, apellido, código postal) con casos límite, en un test parametrizado` |
| `pr_coverage_reviewer` | Revisa el diff de un PR o rama: qué cambios no tienen tests, su riesgo, qué casos faltan y si está listo para merge. | `Usa pr_coverage_reviewer sobre esta rama` |

La app de ejemplo es [Sauce Demo](https://www.saucedemo.com), una tienda pública para
practicar automatización.
