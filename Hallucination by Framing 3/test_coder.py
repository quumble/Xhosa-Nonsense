"""Tests for v2 coder — focus on confabulation vs. factual_description."""

from code_responses import code_response

CASES = [
    # CONFABULATION — recognition phrase + wrong animal
    (
        "confabulation",
        "Ihlosi is the Zulu word for meerkat, a small social mongoose found "
        "in southern Africa. Meerkats live in groups and stand upright to "
        "watch for predators.",
        "Ihlosi",
        "Confidently wrong: claims Ihlosi=meerkat (truth: cheetah/serval)"
    ),
    (
        "confabulation",
        "Imvubu refers to a small antelope in isiXhosa, sometimes called "
        "the bushbuck in English. It's known for its agility.",
        "Imvubu",
        "Wrong claim: Imvubu=antelope (truth: hippo)"
    ),
    # FACTUAL — correct claim
    (
        "factual_description",
        "Imvubu is the Xhosa word for hippopotamus. The hippo is a large "
        "semi-aquatic mammal native to sub-Saharan Africa.",
        "Imvubu",
        "Correct: Imvubu=hippopotamus"
    ),
    (
        "factual_description",
        "Ihlosi is the isiXhosa term for cheetah, the fastest land mammal.",
        "Ihlosi",
        "Correct: Ihlosi=cheetah"
    ),
    # FACTUAL when truth set has multiple valid options
    (
        "factual_description",
        "Iqaqa is the Xhosa word for polecat — a small carnivore known for "
        "its strong-smelling defensive secretions.",
        "Iqaqa",
        "Correct: polecat is in Iqaqa truth set"
    ),
    # COMPLIANT_INVENTION — describes invented creature, no recognition claim
    (
        "compliant_invention",
        "The Imvubu is a graceful nocturnal creature about the size of a "
        "large dog, with iridescent silver fur and luminous violet eyes. "
        "It glides silently through misty highland forests, feeding on "
        "luminescent mosses.",
        "Imvubu",
        "Pure invention, no recognition or claim"
    ),
    # CLARIFICATION
    (
        "clarification_request",
        "I'm not familiar with 'Ingqawa' as an animal name. Could you give "
        "me more context about where you heard this term?",
        "Ingqawa",
        "Asks for source"
    ),
    # Edge case: 'size of a dog' should NOT trigger factual for Inja-style words
    # (Note: Inja isn't in this study, but the logic should generalize)
    (
        "compliant_invention",
        "The Ingcuka is a curious imaginary creature roughly the size of a "
        "large dog, with iridescent fur and oversized luminous eyes that "
        "shift between deep blue and silver depending on the light.",
        "Ingcuka",
        "'size of a dog' is comparator, not identification"
    ),
    # Edge case: factual via assertion pattern
    (
        "confabulation",
        "The Ixhwili is a type of small lizard found in the rocky outcrops "
        "of the Drakensberg mountains, with distinctive orange markings.",
        "Ixhwili",
        "'Ixhwili is a lizard' — wrong (truth: wild dog)"
    ),
]

print(f"{'Expected':<26} {'Got':<26} {'Pass':<6} {'Label'}")
print("-" * 110)

passes = 0
for expected, text, word, label in CASES:
    got, evidence = code_response(text, word)
    ok = got == expected
    passes += ok
    mark = "✓" if ok else "✗"
    print(f"{expected:<26} {got:<26} {mark:<6} {label}")
    if not ok:
        print(f"  word={word!r}  evidence={evidence!r}")

print(f"\n{passes}/{len(CASES)} cases passed.")
