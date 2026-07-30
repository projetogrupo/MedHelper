# MedHelper

Clinic scheduling and attendance system.

Patients browse a doctor's real availability and book a slot; doctors manage
their weekly schedule, run the appointment, record notes and attach documents.
Two features use AI (Claude API) inside the product: an appointment audio can be turned into
a structured medical document, and patients have a chat assistant that helps
them decide which specialty to look for.

Django 5.2 · HTMX · PostgreSQL · Docker

## Running it

With Docker Desktop running:

```bash
docker compose up
```

Open http://localhost:8000. The stack starts Postgres, applies the migrations and seeds demo accounts.

Log in with any of these (password `medhelper123`):

| Account | Role |
|---|---|
| `ana@medhelper.local` | patient |
| `cardio@medhelper.local` | doctor — Cardiologia |
| `admin@medhelper.local` | admin |

The AI features need an `ANTHROPIC_API_KEY` in a `.env` file; everything else
works without it.

## Documentation

**[docs/PROJECT.md](docs/PROJECT.md) is the source of truth.** 
| Document | What is there |
|---|---|
| [docs/PROJECT.md](docs/PROJECT.md) | Architecture, data model, AI features, testing, structure, known limitations |
| [AI_Usage.md](AI_Usage.md) | How AI was used in development and inside the product |
| [docs/metrics.md](docs/metrics.md) | radon and pylint progression per milestone |
