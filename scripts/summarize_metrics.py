#!/usr/bin/env python3
"""Summarize radon/pylint JSON output for one checkpoint into a Markdown report."""
import json
import statistics
import sys
from pathlib import Path


def load(path):
    with open(path) as f:
        return json.load(f)


def iter_blocks(cc_data):
    for blocks in cc_data.values():
        for block in blocks:
            yield block
            for method in block.get("methods", []):
                yield method


def main():
    out_dir = Path(sys.argv[1])
    checkpoint = out_dir.name

    cc_data = load(out_dir / "cc.json")
    mi_data = load(out_dir / "mi.json")
    raw_data = load(out_dir / "raw.json")
    try:
        pylint_data = load(out_dir / "pylint.json")
    except (json.JSONDecodeError, FileNotFoundError):
        pylint_data = []

    complexities = [b["complexity"] for b in iter_blocks(cc_data)]
    mi_scores = [v["mi"] for v in mi_data.values()]
    total_loc = sum(v["loc"] for v in raw_data.values())
    total_sloc = sum(v["sloc"] for v in raw_data.values())

    # pylint's JSON output is just the list of findings; the overall score
    # is only printed in the plain-text report, so we scrape it from there.
    pylint_score = None
    score_path = out_dir / "pylint.txt"
    if score_path.exists():
        for line in score_path.read_text().splitlines():
            if "Your code has been rated at" in line:
                pylint_score = line.split("rated at")[1].split("(")[0].strip()

    print(f"## Metrics — checkpoint `{checkpoint}`\n")
    print("| Metric | Value |")
    print("|---|---|")
    print(f"| Blocks analyzed (CC) | {len(complexities)} |")
    print(f"| Avg cyclomatic complexity | {statistics.mean(complexities):.2f} |" if complexities else "| Avg cyclomatic complexity | n/a |")
    print(f"| Max cyclomatic complexity | {max(complexities)} |" if complexities else "| Max cyclomatic complexity | n/a |")
    print(f"| Avg maintainability index | {statistics.mean(mi_scores):.2f} |" if mi_scores else "| Avg maintainability index | n/a |")
    print(f"| Min maintainability index | {min(mi_scores):.2f} |" if mi_scores else "| Min maintainability index | n/a |")
    print(f"| Total LOC / SLOC | {total_loc} / {total_sloc} |")
    print(f"| Pylint findings | {len(pylint_data)} |")
    print(f"| Pylint score | {pylint_score or 'n/a'} |")


if __name__ == "__main__":
    main()
