# Code Metrics

This document records the evolution of the backend's code-quality metrics
across project milestones, as required by the course.

Metrics cover the backend Python code (`src/core`, `src/medhelper`),
excluding migrations and tests. They are collected with
[radon](https://radon.readthedocs.io/) (complexity, maintainability, raw
size) and [pylint](https://pylint.readthedocs.io/) (static-analysis score).

## How to collect

```bash
# Run from the project root, with the virtualenv active.
./scripts/metrics.sh milestone-<N>
```

This writes a snapshot to `metrics/milestone-<N>/` (one JSON file per radon
metric — `cc`, `mi`, `raw`, `hal` — plus `pylint.json`/`pylint.txt` and a
human-readable `summary.md`). The same collection runs automatically in CI
on every push/PR, where the snapshot is uploaded as a build artifact.

After collecting a milestone, copy its numbers into the progression table
below and commit the `metrics/milestone-<N>/` folder as the permanent record.

## Metrics glossary

| Metric | Tool | Meaning |
|---|---|---|
| Cyclomatic complexity (CC) | radon `cc` | Number of independent paths through a block; lower is simpler. Rank A (1–5) is ideal. |
| Maintainability index (MI) | radon `mi` | 0–100 score combining complexity, volume, and size; higher is more maintainable. Rank A is ≥ 20. |
| LOC / SLOC | radon `raw` | Total lines / source lines of code. |
| Pylint score | pylint | 0–10 static-analysis rating. |

## Progression

| Metric | Milestone 0 (baseline) |
|---|---|
| Blocks analyzed (CC) | 26 |
| Avg cyclomatic complexity | 1.35 |
| Max cyclomatic complexity | 2 |
| Avg maintainability index | 92.26 |
| Min maintainability index | 51.35 |
| Total LOC / SLOC | 471 / 321 |
| Pylint findings | 55 |
| Pylint score | 8.06/10 |

_Add a new column for each milestone as it is completed._

## Milestone notes

### Milestone 0 — Metrics tooling baseline

First snapshot, taken when the radon/pylint collection and CI pipeline were
set up (Setup & Infrastructure milestone). Captures the state of the backend
after the initial models, HTMX CRUD endpoints, and Docker/Postgres setup.

- Complexity is very low: every block ranks **A**, average **1.35**, max **2**.
- Maintainability is strong: all files rank **A**; the lowest is `views.py`
  at **51.35** (still well within the maintainable range), as it holds most
  of the request-handling logic.
- Pylint sits at **8.06/10**. The bulk of the findings are indentation
  warnings in `models.py` (1–2 space indents instead of 4) plus a few
  over-length lines — formatting issues rather than logic problems.
