# Hallucination-by-Framing Study (Study 3)

Targeted follow-up to the [real-Xhosa control](../xhosa_real_control/),
which surfaced an unexpected confabulation pattern under
`false_presupposition` framing for partially-familiar words.

## Question

Does `false_presupposition` framing ("I've heard X is an animal")
cause Claude to produce confidently wrong factual claims more often
than neutral or permission-granted framings, when the word is
partially familiar?

The control study showed Ihlosi (Xhosa for *cheetah*) generated
0/20 recognition under `neutral` but 19/20 confident-but-wrong "Zulu
word for meerkat" claims under `false_presupposition`. This study
characterizes that pattern at scale.

## Design

- **10 words**: 4 carry-overs from control (Ihlosi, Ingqawa, Inyhwagi,
  Ixhwili) + 6 new partially-familiar Xhosa animal terms
- **3 framings**: same as prior studies
- **N=50/cell**: 1,500 trials total (up from 600)

## What's new in the coder

New code: **`confabulation`** — Claude makes a recognition-phrase
factual claim AND names a specific animal AND that animal is **not**
in the word's locked truth set.

`code_responses.py` includes a per-word `TRUTH` dict mapping each Xhosa
word to its valid English referents (cross-language ambiguity reflected:
Ihlosi accepts cheetah/serval; Iqaqa accepts polecat/civet/skunk).

A comparator filter prevents "size of a large dog" from triggering
"dog" recognition.

## Running

```bash
export ANTHROPIC_API_KEY=sk-...

python run_experiment.py --dry-run                      # check
python run_experiment.py --limit 5 --out smoke.jsonl    # smoke
python run_experiment.py --out results.jsonl            # full (~9 min)

# Resume any failures:
python run_experiment.py --out results.jsonl --resume

python code_responses.py results.jsonl --out results_coded.jsonl
python analyze.py results_coded.jsonl --outdir analysis/
```

The runtime estimate (~9 min) is a clean throttled run. Plus another
minute for coding and analysis.

## Headline metrics

The summary.txt highlights:
- **Confabulation rate by framing** (the H1 test)
- **Confabulation rate by word × framing** (which words drive it)

Look at `analysis/codes_by_framing.csv` and `codes_by_word_framing.csv`
for the cross-tabs.

## Files

| File | Purpose |
|---|---|
| `PREREG.md` | Locked predictions (H1–H5) |
| `run_experiment.py` | 1,500-trial runner with resume |
| `code_responses.py` | v2 coder with confabulation detection |
| `analyze.py` | Cross-tabs + headline confabulation breakdown |
| `test_coder.py` | 9 unit tests for v2 coder |
