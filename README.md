# Warden

Agente autónomo de detección y remediación de degradación de servicios para
Plataformas Internas de Desarrollo (Internal Developer Platforms).

Warden recibe señales de degradación de servicios mediante webhooks, analiza la
situación utilizando un LLM y ejecuta una acción de remediación de forma autónoma o
la escala a un humano cuando es necesario.

## Requisitos

- Docker y Docker Compose (para correr el servicio completo)
- [uv](https://docs.astral.sh/uv/) y Python 3.14 (para desarrollo local y tests)
- API Key de Groq (https://console.groq.com)

## Configuración

1. Clonar el repositorio:
   ```bash
   git clone <repo-url>
   cd warden
   ```

2. Crear el archivo de entorno:
   ```bash
   cp .env.example .env
   ```
   Configura tu `GROQ_API_KEY` en el archivo `.env`.

3. Iniciar los servicios:
   ```bash
   docker compose up --build
   ```
   El servicio estará disponible en `http://localhost:9000`.

4. Desarrollo local con `uv` (sin Docker):
   ```bash
   uv sync
   uv run alembic upgrade head   # requiere DATABASE_URL apuntando a un Postgres
   uv run granian --interface asgi --reload --port 9000 src.main:app
   ```

5. Ejecutar las pruebas:
   ```bash
   uv run pytest -v
   ```
   Las pruebas no requieren Postgres ni una `GROQ_API_KEY` real: usan SQLite en
   memoria y un proveedor LLM falso (`FakeReasoningProvider`) inyectado vía
   `app.dependency_overrides`.

## API

| Método | Ruta                   | Descripción                                       |
| ------ | ---------------------- | -------------------------------------------------- |
| GET    | /health                | Verificación del estado del servicio                |
| POST   | /events                | Ingesta de una señal de degradación                 |
| GET    | /events                | Listar eventos recibidos                            |
| GET    | /events/:id            | Detalle de un evento junto con la decisión tomada   |
| GET    | /approvals             | Solicitudes de aprobación pendientes                |
| POST   | /approvals/:id/approve | Aprobar y ejecutar una acción (body opcional `{"feedback": "..."}`) |
| POST   | /approvals/:id/reject  | Rechazar una acción pendiente (body opcional `{"feedback": "..."}`) |

## Arquitectura

```
src/
  config.py        Settings único (pydantic-settings), sin os.getenv disperso
  main.py           App factory FastAPI, lifespan, /health, manejo global de errores
  domain/           Modelos puros (DegradationEvent, RemediationDecision, HistoryEntry, enums)
  db/               Engine/Session de SQLAlchemy + modelos ORM (*Record)
  repositories/     Una clase por agregado; encapsulan todas las queries SQLAlchemy
  llm/              Protocol ReasoningProvider + GroqProvider + prompt_builder + response_parser
  policies/         SafetyPolicy aplica una lista de SafetyRule (Chain of Responsibility)
  actions/          Strategy: un ActionHandler por acción + ActionRegistry
  history/          HistoryService arma el historial de un proyecto desde los repos
  reasoning/        ReasoningEngine orquesta provider + prompt + parser + policy + historial
  services/         EventIngestionService y ApprovalService (orquestación de caso de uso)
  api/              deps.py (composition root), schemas.py (DTOs HTTP), routers delgados
mocks/              orchestrator.py y notifications.py — ahora sí invocados por actions/
```

### Decisiones de diseño

- **Repository** (`repositories/`) aísla SQLAlchemy del resto del dominio y elimina
  la duplicación de queries que existía en routers y en el módulo de historial.
- **Protocol-based DIP** (`llm/provider.py`, `actions/base.py`): el motor de
  razonamiento no depende de Groq concretamente, y la app no depende de un
  orquestador real. Soportar otro proveedor LLM solo requiere una clase nueva que
  cumpla `ReasoningProvider`.
- **Chain of Responsibility simplificado** (`policies/safety_policy.py`): cada
  restricción de `safe_to_auto` es una clase `SafetyRule` independiente y testeable;
  agregar una restricción nueva no toca las demás.
- **Strategy** (`actions/`): cada acción de remediación es un `ActionHandler`
  intercambiable; `ActionRegistry` los despacha por `ActionType`. Los handlers ahora
  sí invocan `mocks/orchestrator.py` y `mocks/notifications.py` (en el diseño
  original estos mocks existían pero nunca se llamaban).
- **Composition root manual** (`api/deps.py`): un solo lugar ensambla repos,
  provider, policy, registry y servicios concretos con sus dependencias. No se
  introduce un framework de DI adicional — FastAPI `Depends` ya resuelve el grafo,
  y agregar uno sería sobre-ingeniería para este alcance.
- `RemediationDecision` es inmutable (`frozen=True`); aplicar restricciones de
  seguridad devuelve una copia (`with_safe_to_auto`) en lugar de mutar el dict
  original.

## Suposiciones

- El campo `context` es opcional y extensible.
- El único entorno considerado como producción es `prod`.
- El límite de historial es configurable mediante la variable de entorno
  `HISTORY_LIMIT` (valor predeterminado: `5`).
- El feedback humano en `approve`/`reject` es texto libre opcional. El `HistoryEntry`
  que se envía al LLM incluye tanto el resultado de la aprobación (`approved` /
  `rejected`) como ese texto libre, para que decisiones futuras sobre el mismo
  proyecto puedan tener en cuenta por qué una acción anterior fue aprobada o
  rechazada.
- Las pruebas usan SQLite en memoria en vez de Postgres real: son más rápidas, no
  requieren infraestructura levantada y no aportan valor adicional para este
  alcance (el contrato de SQLAlchemy/Alembic es el mismo).

### Restricciones de `safe_to_auto`

| Condición                                           | Efecto                         |
| ---------------------------------------------------- | ------------------------------- |
| `severity == critical`                               | `safe_to_auto = false` siempre  |
| `confidence < 0.7`                                   | `safe_to_auto = false`          |
| `env == prod` y `action` en `rollback`, `scale_up`    | `safe_to_auto = false`          |
