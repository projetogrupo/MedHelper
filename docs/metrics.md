# Code Metrics

Evolution of the backend's code-quality metrics across project milestones,
collected with [radon](https://radon.readthedocs.io/) (complexity,
maintainability, size) and [pylint](https://pylint.readthedocs.io/) over
`src/core` and `src/medhelper` (excluding migrations and tests).

## Progression

| Metric | 0 — Baseline | 1 — Backend | 2 — AI | 3 — Infra | 4 — Frontend |
|---|---|---|---|---|---|
| Blocks analyzed (CC) | 26 | 110 | 125 | 130 | 144 |
| Avg cyclomatic complexity | 1.35 | 2.46 | 2.55 | 2.72 | 2.68 |
| Max cyclomatic complexity | 2 | 10 | 10 | 12 | 12 |
| Avg maintainability index | 92.26 | 79.54 | 77.84 | 80.12 | 82.29 |
| Min maintainability index | 51.35 | 3.49 | 4.40 | 4.40 | 6.89 |
| Total LOC / SLOC | 471 / 321 | 1343 / 1061 | 1712 / 1338 | 1796 / 1401 | 2047 / 1565 |
| Pylint findings | 55 | 266 | 288 | 289 | 187 |
| Pylint score | 8.06/10 | 8.03/10 | 8.28/10 | 8.34/10 | 9.09/10 |

_A new column is added for each completed milestone. The raw snapshot behind
each column lives in `metrics/milestone-<n>-<name>/`._

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

### Milestone 1 — Accounts, scheduling and attendance

Backend after the accounts/roles, doctor availability, patient booking, and
attendance features landed (PR #58). The backend roughly tripled in size
(321 → 1061 SLOC).

- Complexity rose but stays reasonable: average **2.46**, with the most complex
  block at **10** (still rank B/C, not alarming).
- Maintainability dropped, driven by `views.py` — now ~635 lines and MI **3.49**
  (rank C). It carries most of the scheduling/attendance logic and is the main
  candidate for splitting into smaller modules.
- Pylint held roughly steady at **8.03/10** despite the 5x growth in findings,
  which scale with the added code.

### Milestone 2 — AI features

Backend after the two AI features landed: appointment document generation from
audio (PR #62) and the specialty guidance chatbot (PR #65), plus the English
cleanup of code artifacts (PR #66). Grew ~26% (1061 → 1338 SLOC).

- Complexity essentially flat: average **2.55** (from 2.46) and the same peak
  of **10**. The new code is mostly linear I/O and rendering, so it added
  volume without adding branching.
- Pylint **improved** to **8.28/10**. The new `ai.py` scores 10.00/10 on its
  own and the English cleanup removed some long-line warnings, which more than
  offset the extra findings that come with more code.
- `views.py` remains the one real problem: **MI 4.40, rank C**, against 42.76
  for the next worst file (`models.py`). It is now 641 SLOC and holds every
  view in the project.

⚠️ Read the min-MI improvement (3.49 → 4.40) with care: it is a **formula
artifact, not a real gain**. Radon's MI rewards comment density, and `views.py`
went from 0 to 4 comment lines in this milestone — enough to offset the ~95
extra source lines. The file did not get easier to maintain; it got bigger.
Splitting it into modules (booking, availability, attendance, chat) is the
clear next refactor, and would be the honest way to move this number.

### Milestone 3 — Setup & Infrastructure

Backend after the infrastructure milestone closed: `docker compose up` works
from a clean clone, with a Postgres healthcheck, environment defaults, a
slimmer image, and the `seed_demo` command that makes a fresh install usable
(PR #70). Grew ~5% (1338 → 1401 SLOC) — the smallest milestone so far, since
most of the work landed in `Dockerfile`, `docker-compose.yaml` and the README,
which radon and pylint do not measure.

- **Max complexity rose 10 → 12**, and for the first time the peak is *not* in
  `views.py`: it is `seed_demo.Command.handle` (rank C). The command loops over
  doctors and over weekday/time pairs to build the availability grid, and
  guards each step so a second run changes nothing. The complexity buys
  idempotence, which the Docker entrypoint depends on — it runs `seed_demo` on
  every container start.
- Pylint edged up to **8.34/10**.
- `views.py` is unchanged at **MI 4.40**, still an order of magnitude worse
  than the next file (`models.py`, 42.76). This milestone did not touch it.

⚠️ The average MI *rose* (77.84 → 80.12), which looks like the codebase got
more maintainable. It did not. Radon averages per file, and this milestone
added one small, well-documented file — `seed_demo.py` at **69.93** — which
pulls the mean up without improving a single existing file. Read the **minimum**
MI, not the average, when asking whether the worst code got better: it sat
still at 4.40, and it is the number that matters.

### Milestone 4 — Frontend redesign and performance

The last milestone: the interface redesign with progress reporting for the AI
document (PR #72), the specialty field closed to a fixed list, and the
pagination plus N+1 fix (PR #73). Grew ~12% (1401 → 1565 SLOC).

**The real gain is pylint: 8.34 → 9.09/10**, and it is traceable to a single
cause. Findings fell from 289 to 187 — a drop of 102 *while the code grew* —
because `models.py` was converted from tabs to spaces, eliminating **126
`bad-indentation` warnings** at a stroke. Partly offset by 21 new warnings in
the test suite (`protected-access` and `redefined-outer-name`, both inherent to
pytest fixtures and to tests that reach for private helpers).

Average complexity also **fell** (2.72 → 2.68) despite 164 extra source lines,
which is a genuine structural improvement: the listing logic was factored into
`_by_patient_name()` and `_page()` instead of being repeated per role.

⚠️ **The min-MI jump 4.40 → 6.89 is not real.** This is the third milestone in
a row where radon's MI misleads, and this time it was measured directly:

| `views.py` | MI |
|---|---|
| as committed | **6.89** |
| with full-line comments stripped | **3.68** |

Radon's MI includes a comment-density term, so the 12 comment lines added this
milestone more than offset the growth. Structurally the file got **worse**: it
went from 641 to 758 SLOC and is still the only rank-C file in the project,
against 46.07 for the next worst (`models.py`).

The lesson worth carrying: read the **minimum** MI rather than the average, and
treat any MI movement under 10 points as noise unless the comment ratio held
steady. Splitting `views.py` into modules per context (booking, availability,
attendance, AI) remains the one refactor that would move this number honestly.

## Overall progression

Across the five milestones the backend grew almost fivefold, from 321 to 1565
SLOC, and complexity did not follow: average cyclomatic complexity went from
1.35 to 2.68 and stayed rank **A** throughout, because most of what was added
is linear I/O and rendering rather than branching. Pylint rose from 8.06 to
**9.09/10**, the largest single jump coming from converting `models.py` from
tabs to spaces, which removed 126 warnings at once.

The one genuine degradation is concentration: `views.py` fell from MI 51.35 to
**6.89** — the only rank-C file — because every view in the project lives in it.
Splitting it per context is the outstanding refactor, since radon rewards comment density and averages per file.
