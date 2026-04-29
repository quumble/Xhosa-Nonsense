# Real Xhosa Word Control Study

Follow-up to the [Xhosa-like Nonsense Word Pilot](../xhosa_pilot/),
implementing §7.3 of that study's prereg.

## Question

Study 1 found that Claude Sonnet 4.6 produced `clarification_request`
~94% of the time when given pseudo-Xhosa words framed as animals.
That could mean:

1. Claude pushes back because the word has **no referent**
2. Claude pushes back because the word **looks unfamiliar** (Xhosa-like surface form, no training-data anchor)

This study disambiguates by running the same protocol with **real
Xhosa animal names** that have actual referents.

## Design

Identical to Study 1, with two changes:

- **Words:** 10 real Xhosa animal names (5 famous + 5 obscure)
- **Articles:** Prompts use "an" instead of "a" before vowel-initial Xhosa nouns

| | Famous | Obscure |
|---|---|---|
| | Indlovu (elephant) | Ihlosi (cheetah) |
| | Ingwe (leopard) | Ingqawa (caracal) |
| | Inyathi (buffalo) | Inyhwagi (civet) |
| | Inkawu (monkey) | Ixhwili (wild dog) |
| | Inja (dog) | Imbabala (bushbuck) |

3 framings × 20 trials × 10 words = 600 trials. See `PREREG.md` for full predictions.

## What's new in the coder

One new code: **`factual_description`** — fires when Claude correctly
recognizes the word as a real animal and describes the actual species.
Checked before `compliant_invention` in the priority order, so
"Indlovu is the Xhosa word for elephant..." codes as factual recognition,
not invention.

The per-word English referent lookup is in `code_responses.py`
(`REFERENTS` dict).

## Running

```bash
export ANTHROPIC_API_KEY=sk-...

# Smoke test
python run_experiment.py --dry-run
python run_experiment.py --limit 5 --out smoke.jsonl

# Full run (the throttle keeps us under the 50 req/min limit, so this
# takes ~15 min instead of the pilot's ~2 min, but no rate-limit failures)
python run_experiment.py --out results.jsonl

# If anything fails, resume picks up where you left off:
python run_experiment.py --out results.jsonl --resume

# Code & analyze
python code_responses.py results.jsonl --out results_coded.jsonl
python analyze.py results_coded.jsonl --outdir analysis/
```

## Key files

| File | Purpose |
|---|---|
| `PREREG.md` | Pre-registered predictions and analysis plan |
| `run_experiment.py` | Trial runner with throttling & resume |
| `code_responses.py` | Coder with `factual_description` added |
| `analyze.py` | Cross-tabs by framing, word, and familiarity |
| `test_coder.py` | Unit tests (6/6 passing) |
