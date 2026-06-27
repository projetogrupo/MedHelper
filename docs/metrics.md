# Code Metrics

Evolution of the backend's code-quality metrics across project milestones,
collected with [radon](https://radon.readthedocs.io/) (complexity,
maintainability, size) and [pylint](https://pylint.readthedocs.io/) over
`src/core` and `src/medhelper` (excluding migrations and tests).

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

_A new column is added for each completed milestone._

## Metrics glossary

| Metric | Meaning |
|---|---|
| Cyclomatic complexity (CC) | Independent paths through a block; lower is simpler. Rank A (1–5) is ideal. |
| Maintainability index (MI) | 0–100 score; higher is more maintainable. Rank A is ≥ 20. |
| LOC / SLOC | Total lines / source lines of code. |
| Pylint score | 0–10 static-analysis rating. |

## Milestone notes

### Milestone 0 — Baseline

State of the backend when metrics tooling was set up (initial models, HTMX
CRUD endpoints, Docker/Postgres).

- Complexity very low: every block ranks **A**, average **1.35**, max **2**.
- Maintainability strong: all files rank **A**; lowest is `views.py` at
  **51.35**, as it holds most of the request-handling logic.
- Pylint **8.06/10** — mostly `models.py` indentation and a few over-length
  lines (formatting, not logic).
