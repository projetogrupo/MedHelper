#!/usr/bin/env bash
# Collects backend code metrics for a named checkpoint (e.g. a milestone tag,
# "main", or "before"/"after" a refactor), following the checkpoint convention
# from https://gitlab.com/cortext-usp/metrics: one JSON file per radon metric
# (cc, mi, raw, hal) plus pylint JSON+text, all under metrics/<checkpoint>/.
#
# Usage: ./scripts/metrics.sh [checkpoint-name]
# Defaults to the current git ref (branch or tag) as the checkpoint name.
set -euo pipefail

cd "$(dirname "$0")/.."

TARGETS="src/core src/medhelper"
EXCLUDE="*/migrations/*,*/tests/*"
CHECKPOINT="${1:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo snapshot)}"
OUT_DIR="metrics/${CHECKPOINT}"

mkdir -p "$OUT_DIR"

radon cc $TARGETS -j -e "$EXCLUDE" > "$OUT_DIR/cc.json"
radon mi $TARGETS -j -e "$EXCLUDE" > "$OUT_DIR/mi.json"
radon raw $TARGETS -j -e "$EXCLUDE" > "$OUT_DIR/raw.json"
radon hal $TARGETS -j -e "$EXCLUDE" > "$OUT_DIR/hal.json"
pylint $TARGETS --exit-zero --output-format=json > "$OUT_DIR/pylint.json" || true
pylint $TARGETS --exit-zero > "$OUT_DIR/pylint.txt" || true

echo "[checkpoint: $CHECKPOINT] $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> RUN

python3 scripts/summarize_metrics.py "$OUT_DIR" | tee "$OUT_DIR/summary.md"

echo "Metrics written to $OUT_DIR/" >&2
