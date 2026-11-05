# Reglas para pruebas de API

Complementan el `CLAUDE.md` raíz. Aplican a todo lo que está bajo `api/`.
Todavía no hay servicios aquí; el primero que se agregue debe servir de ejemplo de referencia.

## Stack
- Pytest + `APIRequestContext` de Playwright (`playwright.request.new_context(base_url=...)`),
  para no sumar dependencias. Si un servicio necesita otra librería, se discute en el PR.

## Estructura de un servicio
```
api/<nombre>/
├── __init__.py
├── conftest.py          # BASE_URL del servicio + fixture del cliente/contexto y auth
├── clients/             # Un cliente por recurso: <recurso>_client.py
│   └── __init__.py
├── schemas/             # (opcional) contratos esperados de las respuestas
└── tests/
    ├── __init__.py
    ├── features/<recurso>.feature
    └── api/
        ├── __init__.py
        └── test_<recurso>.py
```

## Convenciones
- Los tests no arman URLs ni headers a mano: llaman métodos del cliente
  (`users.create(payload)`), igual que los Page Objects en web.
- Cada test verifica, en este orden: código de estado, contrato/forma del cuerpo y valores clave.
- Cubre el camino feliz y los negativos relevantes: 400 (datos inválidos), 401/403 (sin
  permisos), 404 (recurso inexistente).
- Los tests son independientes: crean sus datos y los limpian en un fixture con `yield`.
  Nada de depender del orden de ejecución ni de datos dejados por otro test.
- Tokens y API keys solo por variables de entorno (`<NOMBRE>_API_TOKEN`); nunca en el código
  ni en los logs.
- Nada de llamadas destructivas contra entornos productivos.

## Comandos
- Todos los servicios: `pytest api`
- Un servicio: `pytest api/<nombre>`
