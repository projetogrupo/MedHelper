# MedHelper
Project for MAC0350 that serves as an auxiliary tool for medical professionals. Allows scheduling and monitoring of patients

## General Project overview
This section will describe AI usage throughout development.

## AI Usage Overview
This section will describe AI usage throughout development.

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