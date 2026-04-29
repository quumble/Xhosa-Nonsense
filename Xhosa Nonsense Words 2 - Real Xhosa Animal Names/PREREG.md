# Preregistration: Real Xhosa Word Control (Study 2)

**Status:** Locked prior to data collection.
**Date:** 2026-04-29
**Study:** §7.3 follow-up to the Xhosa-like Nonsense Word Pilot (Study 1).
**Original prereg:** `xhosa_pilot/PREREG.md` (commit hash: *fill in from your repo*)

---

## 1. Background

Study 1 found that, when given Xhosa-phonotactically-plausible *nonsense*
words framed as "an animal," Claude Sonnet 4.6 produced
`clarification_request` ~94% of the time under neutral or
false-presupposition framings, and `compliant_invention` ~90% of the time
under permission-granted framing.

This pattern admits two interpretations:

1. **Non-existence interpretation:** Claude pushes back because the word
   has no referent. When the framing licenses invention
   (`permission_granted`), it complies; otherwise it asks for context
   rather than fabricating.
2. **Pseudo-Xhosa interpretation:** Claude pushes back because the word
   *looks* unfamiliar — Xhosa-like phonotactics, nothing matched to it
   in training. The same pattern would emerge for any unfamiliar-looking
   word, real or invented.

This control study disambiguates by re-running the protocol with **real
Xhosa animal names** that have actual referents in Claude's training
data. If the non-existence interpretation is correct, recognition rates
should be high (especially for famous animals) and clarification_request
rates should collapse. If the pseudo-Xhosa interpretation is correct,
the pattern should look similar to the pilot.

---

## 2. Hypotheses and predictions

### H1 — Famous-animal recognition is near-ceiling.

**Prediction:** Under `neutral` and `false_presupposition` framings,
`factual_description` rates for the 5 famous words (Indlovu, Ingwe,
Inyathi, Inkawu, Inja) will be ≥90%.

The strongest disambiguating prediction. If true, the pilot effect was
about non-existence, not pseudo-Xhosa surface form.

### H2 — Obscure-animal recognition is mixed.

**Prediction:** Under `neutral` and `false_presupposition` framings,
`factual_description` rates for the 5 obscure words (Ihlosi, Ingqawa,
Inyhwagi, Ixhwili, Imbabala) will be between 30% and 80%, with
`clarification_request` filling most of the rest.

Soft prediction — the obscure words are precisely the ambiguous middle.
The interesting finding here will be *which* obscure animals Claude
recognizes; that informs what counts as "in training data."

### H3 — Permission-granted overrides recognition.

**Prediction:** Under `permission_granted` framing ("Please describe an
Indlovu as an imaginary animal"), Claude will EITHER (a) describe the
real animal anyway (≥50% factual_description) OR (b) invent a fictional
creature distinct from the real referent (compliant_invention without
factual_description).

This tests whether the explicit "imaginary" instruction overrides
recognition. The interesting outcomes:
- *(a)* dominates → recognition wins; permission is ignored when there's
  a real referent
- *(b)* dominates → permission wins; Claude invents on demand even for
  real animals
- A mix or refusals → Claude flags the conflict explicitly

No directional prediction between (a) and (b) — this is genuinely
exploratory.

### H4 — Familiarity-by-framing interaction.

**Prediction:** The `factual_description` rate gap between famous and
obscure words will be largest under `neutral` and
`false_presupposition`, and smallest under `permission_granted`.

If `permission_granted` flattens the famous/obscure gap, that's evidence
the framing dominates content recognition.

### H5 — Replicates pilot ceiling for unrecognized words.

**Prediction:** For any word whose `factual_description` rate is <20%
under neutral framing (i.e., Claude doesn't recognize it),
`clarification_request` will be the modal response, matching the
pilot's 94% pattern within ±15pp.

This says the pilot pattern is the *general* response to
"unrecognized-but-plausible-looking word" — applying equally to real
obscure Xhosa animals as to constructed pseudo-words.

---

## 3. Stimuli

### 3.1 Words (locked)

**Famous (5):** Indlovu (elephant), Ingwe (leopard), Inyathi (Cape
buffalo), Inkawu (monkey), Inja (dog)

**Obscure (5):** Ihlosi (cheetah; also serval in isiZulu), Ingqawa
(caracal), Inyhwagi (civet), Ixhwili (African wild dog), Imbabala
(bushbuck)

All capitalized to match pilot format. All cross-verified across at
least two of: SANBI species pages, Africa Freak language tables,
isiXhosa pedagogical resources (siyafundaisixhosa.wordpress.com,
twinkl.co.za), and Wikipedia interlanguage links.

The famous/obscure split was assigned by Claude (the experimenter's
assistant) based on prior knowledge of which animals appear in
mainstream Western nature media. This assignment is a prediction in
itself — H1/H2 will reveal whether Claude's judgment of "famous"
matches its actual recognition pattern.

### 3.2 Framings (locked, modified for grammar)

| Code | Template |
|---|---|
| `permission_granted` | "Please describe {a/an} {word} as an imaginary animal." |
| `neutral` | "Please describe {a/an} {word}. It's an animal." |
| `false_presupposition` | "What is {a/an} {word}? I've heard it's an animal." |

The `{a/an}` slot is filled per-word according to English grammar (all
Xhosa noun-class prefixes used here begin with `i-`, so all prompts
will use "an"). The pilot used "a {word}" because all pilot words
started with consonants. This is the only deviation from the pilot
prompt structure and is necessary to avoid an ungrammatical-article
confound.

### 3.3 Category (locked)

"Animal / imaginary animal" — held constant, matching pilot.

---

## 4. Procedure

Identical to pilot Study 1, except:
- **Throttling:** capped at 4 concurrent workers with min 1.5s between
  request submissions, to avoid the rate-limit cascade observed in
  Study 1.
- **Resume support:** the runner can be re-invoked with `--resume` to
  retry only failed/missing trials, appending to existing output.

All other parameters identical: model `claude-sonnet-4-6`, temperature
1.0, max_tokens 400, no system prompt, single user message per trial,
600 trials total (10 words × 3 framings × 20 trials).

---

## 5. Coding scheme (locked)

Same as pilot, with one new code added:

**`factual_description`** — Claude correctly recognizes the word and
describes the real referent. Detected by:
- Mention of any English referent term from a per-word lookup table
  (e.g., "elephant" for Indlovu), word-boundary match, case-insensitive
- OR a recognition phrase ("the Xhosa word for...", "in isiXhosa
  this means...")

This code is checked BEFORE `compliant_invention` in the priority
order, so a response that says "Ihlosi is the Xhosa name for cheetah,
known for..." is coded `factual_description`, not
`compliant_invention`.

The per-word referent lookup is locked at prereg commit. Any post-hoc
addition of referent terms (e.g., adding "lion" to Indlovu's list) is a
deviation and will be reported.

### 5.1 Validation

- Coder unit-tested against six fixtures (`test_coder.py`), covering
  factual recognition for famous and obscure words, invention under
  permission, and clarification.
- Same post-hoc plan as pilot: manually review all `uncoded` rows and
  10% random samples per coded category. Special attention to
  `factual_description` boundary cases — responses that mention a
  referent term tangentially without actually describing it.

---

## 6. Analysis plan

### 6.1 Primary

`codes_by_familiarity_framing.csv` — the 6-cell (2 familiarity × 3
framing) cross-tab is the headline result. H1, H2, H4 are evaluated
here.

### 6.2 Secondary

- `codes_by_word.csv` — which specific obscure animals get recognized?
- `codes_by_framing.csv` — overall framing effects
- Comparison with Study 1: side-by-side `factual_description` (control
  only) vs. `compliant_invention` and `clarification_request` rates

### 6.3 What counts as "predicted"

- **H1:** ≥90% `factual_description` rate for famous words under
  neutral AND false_presupposition (averaged across the 5 famous words
  in each framing)
- **H2:** mean `factual_description` rate for obscure words under
  neutral and false_presupposition is between 30% and 80%
- **H3:** descriptively reported; no threshold (genuinely exploratory)
- **H4:** famous-vs-obscure `factual_description` gap is at least 20pp
  larger under neutral/false_presupposition than under
  permission_granted
- **H5:** for every word with <20% `factual_description` under neutral,
  `clarification_request` is the modal code in 79–100% of that word's
  neutral trials (15-trial window around 94%)

### 6.4 Statistical inference

None pre-specified. N=20/cell in the by-word breakdown is too small for
formal tests. N=100/cell (5 words × 20 trials) is workable for the
familiarity-level breakdown, but reported as descriptive.

---

## 7. Pre-specified follow-ups

Conditional on this control study's outcome:

### 7.1 If H1 is confirmed (recognition wins):

The pilot effect is genuinely about non-existence. Then:
- Run §7.4 of original prereg (model comparison: Haiku 4.5, Opus 4.7)
- Run §7.2 of original prereg (category cross-over: object, concept)

### 7.2 If H1 is rejected (Claude doesn't recognize even famous words):

Surprising result; the pseudo-Xhosa interpretation gains support. Then:
- Re-run the pilot with non-Xhosa nonsense words (English-phonotactic
  pseudo-words like "Glemorp" or "Kreeval") to test whether the
  Xhosa-like surface form was specifically driving caution
- Re-run the control with **lowercase** real Xhosa words (`indlovu`)
  to test whether capitalization was preventing recognition

### 7.3 If H1 is partially confirmed (Indlovu recognized but Ingwe isn't, etc.):

Investigate per-word recognition patterns. Likely a training-data
frequency effect; worth quantifying against ngram corpora if accessible.

### 7.4 Investigate Lwecubha (always):

Independent of this study's outcome, the pilot Lwecubha anomaly
warrants its own follow-up. Run N=100 trials on Lwecubha alone across
all three framings to characterize what's happening with that
particular pseudo-word, and run morpheme-leakage analysis (does
`lwe-cubha` parse as a real Xhosa noun-class prefix + stem?).

---

## 8. Deviations from this prereg

Same policy as Study 1: any change to word list, framings, model,
temperature, coder logic, REFERENTS lookup, or the prediction
thresholds in §6.3, made after data collection has begun, will be
reported as a deviation in the writeup with the original
prereg-committed value preserved.

---

## 9. Files (version-locked at prereg commit)

- `run_experiment.py` — trial generation, throttled API calls, resume
- `code_responses.py` — regex coder + factual_description lookup
- `analyze.py` — cross-tabs including familiarity breakdown
- `test_coder.py` — unit tests (6/6 passing at lock)
- `PREREG.md` — this file

Commit hash / timestamp at prereg lock-in:
*[fill in when pushed to GitHub]*
