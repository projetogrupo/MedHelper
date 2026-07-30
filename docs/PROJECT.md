# MedHelper — project documentation

Clinic scheduling and attendance system, built for **MAC0350 — Introducao a Desenvolvimento de Sistemas de Software** (IME-USP).

This is the main documentation for the project.

| Topic | Where |
|---|---|
| AI usage, in development and inside the product | [AI_Usage.md](../AI_Usage.md) |
| Code metrics per milestone | [metrics.md](metrics.md) |
| Raw metric snapshots | [`metrics/`](../metrics/) |

---

## 1. What the system does

**Patients** pick a specialty, see which days the doctors actually have free,
book a slot and follow their appointments. They also have a chat assistant
whose only subject is which medical specialty to look for.

**Doctors** define a weekly availability grid with per-day exceptions, see
their agenda, run the appointment (notes and attached documents), consult the
patient's history, and can generate a structured medical document from the
audio of the appointment.

**Admins** have full CRUD over appointments, with search and pagination.

---

## 2. Running it

With Docker Desktop running:

```bash
docker compose up
```

Open http://localhost:8000. The stack starts Postgres, waits for it to accept connections, applies migrations
and seeds demo accounts.

Demo accounts, all with password `medhelper123`:

| Account | Role |
|---|---|
| `admin@medhelper.local` | admin |
| `cardio@medhelper.local` | doctor — Cardiologia |
| `derma@medhelper.local` | doctor — Dermatologia |
| `ana@medhelper.local` | patient |
| `zeca@medhelper.local` | patient |

Useful commands:

```bash
docker compose up --build     # rebuild after changing requirements.txt
docker compose down           # stop, keeping the database
docker compose down -v        # stop and wipe database and cached model
docker compose exec web pytest
```

### Enabling the AI features

Both AI features need an Anthropic API key. Create a `.env` next to
`docker-compose.yaml`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Without it the rest of the application works normally and those two features
show a configuration message instead.

### Without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then set SECRET_KEY
python manage.py migrate
python manage.py seed_demo    # optional: the demo accounts above
python manage.py runserver
```

This path uses SQLite. PostgreSQL is only wired up in the Docker setup — the
choice is made by environment variable in `settings.py`, and no domain code
changes between them.


## 3. AI features

Both are documented in detail in [AI_Usage.md](../AI_Usage.md), including the
prompts and the privacy note. In short:

**Appointment document generation.** The doctor uploads the audio of an
appointment. Transcription runs locally with faster-whisper — the recording
never leaves the machine — and only the resulting text is sent to Claude, which
organises it into fixed clinical sections. `reportlab` renders the PDF.

The pipeline runs in a background thread while the page polls for progress, and
the percentage is measured rather than estimated: faster-whisper yields
segments carrying their end timestamps, so the transcription share of the bar
is the real position within the audio.

**Specialty guidance chatbot.** Patients get a chat assistant restricted to a
single subject — which medical specialty to look for. It refuses anything else,
never gives diagnoses, prefers the specialties actually registered in the
clinic, and directs the patient to emergency services when red-flag symptoms
appear. It is deliberately *not* told which doctors work at the clinic, so it
cannot invent a professional's name.

---

## 4. Quality

### Tests

192 tests in 19 files, run in CI on every push and pull request.

| Kind | Count |
|---|---|
| Integration (through the HTTP client) | ~157 |
| Touching the database without HTTP | ~30 |
| Pure unit | ~5 |

That distribution is the inverse of the classic test pyramid, and it is a
consequence of the Active Record pattern: in Django the domain object *is* the
persistence object, so testing a rule needs a database. The trade-off is
deliberate — these tests do not break when the internals are refactored.

Test doubles are used only at the system boundary (the AI calls), with stubs
for return values and one spy asserting that the view passes the right
transcript to the note generator. The suite therefore needs no API key, no
network and no credit.

`test_pagination.py` includes a performance regression test that fails if
anyone reintroduces the N+1 problem.

### Metrics

radon and pylint run per milestone; the progression and the interpretation of
each movement are in [metrics.md](metrics.md). A general analysis is also presented at the end of [metrics.md](metrics.md).

### CI

GitHub Actions runs two jobs on every push and pull request: the test suite,
and the metrics collection, which uploads the snapshot as an artifact.

---