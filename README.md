# Overseer AI

A production-ready AI-powered oversight and monitoring platform built with Next.js, FastAPI, Supabase, Twilio, and ElevenLabs. Overseer AI enables real-time voice and text agent interactions, session management, live WebSocket streaming, and telephony integrations — all wired through a strict Clean Architecture.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend API | FastAPI (Python) |
| Realtime | WebSockets (native FastAPI) |
| Database | PostgreSQL via Supabase |
| Auth | Supabase Auth |
| Voice/Telephony | Twilio, ElevenLabs |
| Containerisation | Docker / Docker Compose |

---

## Project Structure

```
overseer-ai/
├── src/
│   ├── domain/             # Entities, Value Objects, Repository Interfaces, Domain Services
│   ├── application/        # Use Cases, DTOs, Port Interfaces, Application Services
│   ├── infrastructure/     # DB, Supabase, Twilio, ElevenLabs, WebSocket adapters
│   └── interfaces/         # FastAPI routers, WebSocket handlers, Next.js API routes
├── frontend/               # Next.js application (App Router)
├── docker/                 # Dockerfile variants
├── migrations/             # SQL migration files
├── tests/                  # Unit & integration tests
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Clean Architecture Layers

### `src/domain/`
The core of the system. Contains **zero** external dependencies.

- **Entities** — `Agent`, `Session`, `Message`, `Call` with identity and self-enforcing invariants.
- **Value Objects** — `AgentStatus`, `MessageRole`, `PhoneNumber`, `VoiceSettings` — immutable, equality-by-value.
- **Repository Interfaces** — `IAgentRepository`, `ISessionRepository`, `IMessageRepository`, `ICallRepository` — describe *what*, not *how*.
- **Domain Services** — `SessionOrchestrator` — logic that spans multiple entities.

> `domain/` imports **nothing** outside itself.

### `src/application/`
Orchestrates domain objects into executable use cases.

- **Use Cases** — one class per operation (`CreateAgentUseCase`, `StartSessionUseCase`, `SendMessageUseCase`, `InitiateCallUseCase`, `StreamAudioUseCase`).
- **DTOs** — typed input/output contracts for every use case.
- **Port Interfaces** — `IVoiceService`, `ITelephonyService`, `IRealtimePublisher` — application-level abstractions over infrastructure.
- **Mappers** — domain entity ↔ DTO transformations.

> `application/` imports only from `domain/`.

### `src/infrastructure/`
All I/O lives here. Implements interfaces from `domain/` and `application/`.

- **Supabase / PostgreSQL** — `SupabaseAgentRepository`, `SupabaseSessionRepository`, etc.
- **ElevenLabs** — `ElevenLabsVoiceService` implementing `IVoiceService`.
- **Twilio** — `TwilioTelephonyService` implementing `ITelephonyService`.
- **WebSockets** — `WebSocketRealtimePublisher` implementing `IRealtimePublisher`.
- **Clients** — low-level SDK wrappers (`SupabaseClient`, `ElevenLabsClient`, `TwilioClient`).

> Infrastructure errors are caught and re-thrown as domain exceptions.

### `src/interfaces/`
Thin entry points — validate input → call use case → serialize output.

- **FastAPI Routers** — `/agents`, `/sessions`, `/messages`, `/calls`.
- **WebSocket Handler** — `/ws/session/{session_id}` for realtime streaming.
- **Next.js API Routes** — frontend BFF routes under `frontend/app/api/`.
- **Dependency Injection** — `container.py` wires every layer together.

> Controllers never contain business logic. They never call repositories directly.

---

## Getting Started

### Prerequisites

- Docker & Docker Compose v2+
- Node.js 20+
- Python 3.11+

### 1. Clone & configure environment

```bash
cp .env.example .env
# Fill in all values in .env
```

### 2. Start all services with Docker

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| FastAPI backend | http://localhost:8000 |
| Next.js frontend | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### 3. Run database migrations

```bash
docker compose exec api python -m migrations.run
```

### 4. Frontend development (standalone)

```bash
cd frontend
npm install
npm run dev
```

### 5. Backend development (standalone)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.interfaces.api.main:app --reload --port 8000
```

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `DATABASE_URL` | Direct PostgreSQL connection string |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number |
| `ELEVENLABS_API_KEY` | ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | Default ElevenLabs voice ID |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase URL (exposed to browser) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key (exposed to browser) |
| `SECRET_KEY` | FastAPI JWT signing secret |

---

## Testing

```bash
# Python tests
pytest tests/ -v --cov=src

# Frontend tests
cd frontend && npm run test
```

## Linting & Formatting

```bash
# Python
ruff check src/ && mypy src/

# Frontend
cd frontend && npm run lint && npm run format
```

---

## License

MIT
