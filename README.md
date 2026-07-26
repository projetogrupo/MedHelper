# MedHelper
Project for MAC0350 that serves as an auxiliary tool for medical professionals. Allows scheduling and monitoring of patients

## General Project overview
This section will describe AI usage throughout development.

## AI Usage Overview
This section will describe AI usage throughout development.

## Running with Docker

From a clean clone, with Docker Desktop running:

```bash
docker compose up
```

Open http://localhost:8000. That is the whole setup — no virtualenv, no
`.env`, no manual migration. The first build takes a few minutes; later starts
are fast.

The stack starts Postgres, waits until it accepts connections, applies the
migrations, and seeds demo accounts. Log in with any of these
(password `medhelper123`):

| Account | Role |
|---|---|
| `admin@medhelper.local` | admin |
| `cardio@medhelper.local` | doctor — Cardiologia |
| `derma@medhelper.local` | doctor — Dermatologia |
| `ana@medhelper.local` | patient |
| `zeca@medhelper.local` | patient |

Both doctors already have weekday availability, so a patient can book an
appointment right away.

Useful commands:

```bash
docker compose up --build     # rebuild after changing requirements.txt
docker compose down           # stop (keeps the database)
docker compose down -v        # stop and wipe the database and cached model
docker compose exec web python manage.py createsuperuser
docker compose exec web pytest
```

### Enabling the AI features under Docker

The AI features need an Anthropic API key. Create a `.env` next to
`docker-compose.yaml` with:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Compose picks it up automatically on the next `up`. Without the key everything
else works normally; only those two features are disabled, with a message in
the UI.

### Running without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then set SECRET_KEY
python manage.py migrate
python manage.py seed_demo    # optional: same demo accounts as above
python manage.py runserver
```

This path uses SQLite; Postgres is only wired up in the Docker setup.

## Code Metrics
Backend complexity and maintainability metrics (radon + pylint) are tracked
per milestone in [docs/metrics.md](docs/metrics.md).

## Appointment document generation (AI)

On the attendance screen, a doctor can upload the audio of an appointment and
the app generates a structured medical document in PDF. Transcription runs
locally (the audio never leaves the machine); only the resulting text is sent
to the model that organizes the clinical note. See [AI_Usage.md](AI_Usage.md).

To enable it, set `ANTHROPIC_API_KEY` in your `.env` (see `.env.example`) with a
key from [console.anthropic.com](https://console.anthropic.com). Without the
key the rest of the application works normally — only this feature is disabled.

The transcription model (~150 MB) is downloaded automatically on first use.
Set `WHISPER_MODEL_SIZE` to trade speed for accuracy (`tiny`, `base` (default),
`small`, `medium`).

## Specialty guidance chatbot (AI)

Patients get an "Orientação" page with a chat assistant that helps them decide
which medical specialty to pursue — its only allowed topic. It never gives
diagnoses or treatment advice, prefers the specialties registered in the
clinic, and points to emergency services when red-flag symptoms are described.
Uses the same `ANTHROPIC_API_KEY`; without it, the rest of the app works
normally and the chat shows a configuration message instead.