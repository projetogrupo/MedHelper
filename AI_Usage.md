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
* implementing the appointment document generation feature described below;
* general development support and debugging assistance.

## AI Inside the Product

Beyond assisting development, the application itself uses AI in one feature:
generating a structured medical document from the audio of an appointment.

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

Privacy note: only the transcribed text is sent to an external service; the
recording stays local. The generated PDF carries a notice that it was produced
with AI assistance and must be reviewed by the responsible professional before
clinical use.

The automated tests mock both the transcription and the model call, so the test
suite requires no API key, no network access, and consumes no API credit.

## Human Oversight

All AI-assisted outputs are reviewed and validated by the project members before integration into the codebase.
