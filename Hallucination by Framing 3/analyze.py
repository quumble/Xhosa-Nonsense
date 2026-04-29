"""
Analyzer for hallucination study.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ALL_CODES = [
    "factual_description",
    "confabulation",
    "refusal_clean",
    "clarification_request",
    "disclaim_then_produce",
    "misidentification_offer",
    "meta_test_comment",
    "conditional_invitation",
    "compliant_invention",
    "uncoded", "empty", "error",
]


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def write_crosstab(path, by_key, key_name):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([key_name, *ALL_CODES, "total"])
        for key in sorted(by_key.keys(), key=lambda x: str(x)):
            counts = by_key[key]
            row = [key] + [counts.get(c, 0) for c in ALL_CODES]
            row.append(sum(counts.values()))
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--outdir", default=".")
    args = parser.parse_args()

    rows = load(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    by_framing = defaultdict(Counter)
    by_word = defaultdict(Counter)
    by_origin = defaultdict(Counter)
    by_word_framing = defaultdict(Counter)

    for r in rows:
        by_framing[r["framing"]][r["code"]] += 1
        by_word[r["word"]][r["code"]] += 1
        by_origin[r.get("origin", "unknown")][r["code"]] += 1
        by_word_framing[(r["word"], r["framing"])][r["code"]] += 1

    write_crosstab(outdir / "codes_by_framing.csv", by_framing, "framing")
    write_crosstab(outdir / "codes_by_word.csv", by_word, "word")
    write_crosstab(outdir / "codes_by_origin.csv", by_origin, "origin")

    with open(outdir / "codes_by_word_framing.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "framing", *ALL_CODES, "total"])
        for (w, fr) in sorted(by_word_framing.keys()):
            counts = by_word_framing[(w, fr)]
            row = [w, fr] + [counts.get(c, 0) for c in ALL_CODES]
            row.append(sum(counts.values()))
            writer.writerow(row)

    overall = Counter(r["code"] for r in rows)
    total = sum(overall.values())
    lines = [f"Total trials: {total}", "", "Overall code distribution:"]
    for code in ALL_CODES:
        c = overall.get(code, 0)
        if c:
            lines.append(f"  {code:<28} {c:>5} ({100*c/total:5.1f}%)")

    lines += ["", "By framing:"]
    for framing in sorted(by_framing.keys()):
        lines.append(f"  [{framing}]")
        sub = by_framing[framing]
        sub_total = sum(sub.values())
        for code in ALL_CODES:
            c = sub.get(code, 0)
            if c:
                lines.append(f"    {code:<26} {c:>4} ({100*c/sub_total:5.1f}%)")

    # Headline: confabulation rates by framing
    lines += ["", "═" * 50, "HEADLINE: Confabulation rate by framing", "═" * 50]
    for framing in sorted(by_framing.keys()):
        sub = by_framing[framing]
        sub_total = sum(sub.values())
        confab = sub.get("confabulation", 0)
        lines.append(f"  {framing:<24} {confab:>4}/{sub_total} "
                     f"({100*confab/sub_total:5.1f}%)")

    lines += ["", "Confabulation rate by word × framing:"]
    for w in sorted(set(r["word"] for r in rows)):
        for framing in sorted(set(r["framing"] for r in rows)):
            counts = by_word_framing[(w, framing)]
            ct = sum(counts.values())
            confab = counts.get("confabulation", 0)
            if ct:
                lines.append(f"  {w:<12} {framing:<22} "
                             f"{confab:>3}/{ct} ({100*confab/ct:5.1f}%)")

    summary = "\n".join(lines)
    print(summary)
    (outdir / "summary.txt").write_text(summary + "\n")
    print(f"\nWrote: {outdir.resolve()}/")


if __name__ == "__main__":
    main()
