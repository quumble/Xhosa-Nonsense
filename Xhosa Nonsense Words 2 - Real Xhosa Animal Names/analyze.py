"""
Analyzer for the real-Xhosa control study.

Same as pilot analyzer, plus:
- Adds factual_description to ALL_CODES
- Adds codes_by_familiarity.csv (famous vs. obscure breakdown)
- Adds codes_by_familiarity_framing.csv
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ALL_CODES = [
    "factual_description",
    "refusal_clean",
    "clarification_request",
    "disclaim_then_produce",
    "misidentification_offer",
    "meta_test_comment",
    "conditional_invitation",
    "compliant_invention",
    "uncoded",
    "empty",
    "error",
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

    # By framing
    by_framing = defaultdict(Counter)
    for r in rows:
        by_framing[r["framing"]][r["code"]] += 1
    write_crosstab(outdir / "codes_by_framing.csv", by_framing, "framing")

    # By word
    by_word = defaultdict(Counter)
    for r in rows:
        by_word[r["word"]][r["code"]] += 1
    write_crosstab(outdir / "codes_by_word.csv", by_word, "word")

    # By familiarity (famous vs obscure)
    by_fam = defaultdict(Counter)
    for r in rows:
        by_fam[r.get("familiarity", "unknown")][r["code"]] += 1
    write_crosstab(outdir / "codes_by_familiarity.csv", by_fam, "familiarity")

    # By familiarity x framing
    by_fam_fr = defaultdict(Counter)
    for r in rows:
        key = f"{r.get('familiarity','unknown')}|{r['framing']}"
        by_fam_fr[key][r["code"]] += 1
    write_crosstab(
        outdir / "codes_by_familiarity_framing.csv", by_fam_fr, "familiarity|framing"
    )

    # By word x framing
    by_wf = defaultdict(Counter)
    for r in rows:
        by_wf[(r["word"], r["framing"])][r["code"]] += 1
    with open(outdir / "codes_by_word_framing.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "framing", *ALL_CODES, "total"])
        for (w, fr) in sorted(by_wf.keys()):
            counts = by_wf[(w, fr)]
            row = [w, fr] + [counts.get(c, 0) for c in ALL_CODES]
            row.append(sum(counts.values()))
            writer.writerow(row)

    # Summary text
    overall = Counter(r["code"] for r in rows)
    total = sum(overall.values())
    lines = []
    lines.append(f"Total trials: {total}")
    lines.append("")
    lines.append("Overall code distribution:")
    for code in ALL_CODES:
        c = overall.get(code, 0)
        if c:
            lines.append(f"  {code:<28} {c:>5} ({100*c/total:5.1f}%)")
    lines.append("")
    lines.append("Code distribution by framing:")
    for framing in sorted(by_framing.keys()):
        lines.append(f"  [{framing}]")
        sub = by_framing[framing]
        sub_total = sum(sub.values())
        for code in ALL_CODES:
            c = sub.get(code, 0)
            if c:
                lines.append(f"    {code:<26} {c:>4} ({100*c/sub_total:5.1f}%)")
    lines.append("")
    lines.append("Code distribution by familiarity:")
    for fam in sorted(by_fam.keys()):
        lines.append(f"  [{fam}]")
        sub = by_fam[fam]
        sub_total = sum(sub.values())
        for code in ALL_CODES:
            c = sub.get(code, 0)
            if c:
                lines.append(f"    {code:<26} {c:>4} ({100*c/sub_total:5.1f}%)")

    summary = "\n".join(lines)
    print(summary)
    (outdir / "summary.txt").write_text(summary + "\n")
    print(f"\nWrote: {outdir.resolve()}/")


if __name__ == "__main__":
    main()
