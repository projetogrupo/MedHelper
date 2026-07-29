# AI Usage

During the development of this project, generative AI tools have been used as support tools in parts of the development workflow.

## Tools Used

* Anthropic Claude models
* OpenAI GPT models

Additional tools or models may be incorporated during later stages of development.

## Current Usage

So far, AI assistance has primarily been used for:

* generation of the initial Django project skeleton and boilerplate structure;
* drafting the HTMX-based CRUD endpoints for patients, doctors, and
  appointments (views, forms, and templates);
* setting up pytest-django and drafting test coverage for these endpoints;
* drafting the Dockerfile and docker-compose configuration with a PostgreSQL
  service, and the environment-variable-driven settings;
* setting up the radon/pylint code-metrics tooling, the CI pipeline, and the
  per-milestone metrics documentation;
* building the accounts, scheduling, and attendance features (custom user with
  patient/doctor/admin roles, doctor availability, patient booking, and the
  attendance flow with notes and documents), including their screens and tests;
* implementing the two AI features described below (appointment document
  generation and the specialty guidance chatbot), including their prompts,
  screens and tests;
* fixing the Docker setup so the stack runs from a clean clone: passing the
  required environment through compose, adding a Postgres healthcheck, writing
  the `seed_demo` command, and slimming the image;
* translating code artifacts (URL paths, comments, docstrings) to English;
* redesigning the frontend (design system, loading and progress states,
  responsive layout) and adding the progress reporting to the appointment
  document generation;
* general development support and debugging assistance.

## AI Inside the Product

Beyond assisting development, the application itself uses AI in two features.

### Specialty guidance chatbot

Patients have a chat assistant ("Orientação") that helps them decide which
medical specialty to pursue based on what they describe. The conversation runs
on Anthropic's Claude (`claude-opus-4-8`) with a system prompt that restricts
it to this single topic: it refuses anything else, never gives diagnoses or
treatment advice, prefers the specialties actually registered in the clinic,
and directs the patient to emergency services (192) when red-flag symptoms
appear. Conversation history is kept in the server-side session only.

### Appointment document generation

Generates a structured medical document from the audio of an appointment.

The pipeline has three stages:

1. **Transcription (audio to text)** — runs locally with
   [faster-whisper](https://github.com/SYSTRAN/faster-whisper). The audio file
   never leaves the machine.
2. **Structuring (text to clinical note)** — the transcript is sent to
   Anthropic's Claude (`claude-opus-4-8`) via the official SDK, which organizes
   it into fixed sections (chief complaint, history, findings, diagnostic
   hypothesis, plan, follow-up). The prompt instructs the model to rely only on
   what the transcript contains and to write "Não relatado" for sections with no
   information, to avoid fabricating clinical data.
3. **Rendering (note to PDF)** — `reportlab` produces the final document. This
   step involves no AI.

The three stages can take minutes, so they run in a background thread while
the page polls for progress. The percentage is measured, not estimated:
faster-whisper yields segments with their end timestamps, so the transcription
share of the bar is the position within the real audio duration.

Privacy note: only the transcribed text is sent to an external service; the
recording stays local. The generated PDF carries a notice that it was produced
with AI assistance and must be reviewed by the responsible professional before
clinical use.

The automated tests mock both the transcription and the model call, so the test
suite requires no API key, no network access, and consumes no API credit.

## Human Oversight

All AI-assisted outputs are reviewed and validated by the project members before integration into the codebase.
