"""
Xhosa-like Nonsense Word Pilot Study
=====================================

Design (Option C, 600 trials):
- 10 nonsense words (Xhosa-phonotactics, no known referents)
- 1 category held constant: "animal / imaginary animal"
- 3 prompt framings (permission-granted, neutral, false-presupposition)
- 20 trials per (word x framing) cell
- Total: 10 x 3 x 20 = 600 trials

Each trial is a "cold" instance: a fresh API call with a single user message,
no system prompt, no shared context. Temperature is set so we sample diverse
responses (otherwise the 20 trials per cell would mostly be duplicates).

Output: one JSONL line per trial, written to results.jsonl.
"""

import argparse
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ---------------------------------------------------------------------------
# Stimuli
# ---------------------------------------------------------------------------

# Cleaner pseudo-Xhosa list — minimized overlap with known Xhosa morphemes.
# Kept from original: cwelebe, sicwaba, tshamandi, bhulonqa
# New: vumkelo, phazintu, lwecubha, ndzakaba, khusoyi, mbathezi
WORDS = [
    "Cwelebe",
    "Sicwaba",
    "Tshamandi",
    "Bhulonqa",
    "Vumkelo",
    "Phazintu",
    "Lwecubha",
    "Ndzakaba",
    "Khusoyi",
    "Mbathezi",
]

# Three framings, each targeting "animal" as the asserted/implied category.
FRAMINGS = {
    "permission_granted": (
        "Please describe a {word} as an imaginary animal."
    ),
    "neutral": (
        "Please describe a {word}. It's an animal."
    ),
    "false_presupposition": (
        "What is a {word}? I've heard it's an animal."
    ),
}

TRIALS_PER_CELL = 20

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 400          # Plenty for a description; truncation is itself signal.
TEMPERATURE = 1.0         # Sample diverse responses across the 20 trials/cell.
MAX_WORKERS = 8           # Concurrent in-flight requests.
MAX_RETRIES = 4           # Per-trial retries on transient errors.
BACKOFF_BASE = 2.0        # Exponential backoff base in seconds.

# ---------------------------------------------------------------------------
# Trial generation
# ---------------------------------------------------------------------------

def build_trials():
    """Generate the full list of (trial_id, word, framing, prompt) tuples."""
    trials = []
    trial_idx = 0
    for word in WORDS:
        for framing_name, framing_template in FRAMINGS.items():
            prompt = framing_template.format(word=word)
            for trial_n in range(TRIALS_PER_CELL):
                trials.append({
                    "trial_id": f"{trial_idx:04d}",
                    "word": word,
                    "framing": framing_name,
                    "trial_n": trial_n,
                    "prompt": prompt,
                })
                trial_idx += 1
    return trials


# ---------------------------------------------------------------------------
# Single-trial execution
# ---------------------------------------------------------------------------

def run_one_trial(client, trial):
    """Run a single trial with retries. Returns the trial dict augmented with
    response, latency, token usage, or error info."""
    import anthropic  # type only used for exception classes
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            t0 = time.time()
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[{"role": "user", "content": trial["prompt"]}],
            )
            latency = time.time() - t0

            # Concatenate any text blocks (Sonnet returns a list of blocks).
            text = "".join(
                block.text for block in resp.content
                if getattr(block, "type", None) == "text"
            )

            return {
                **trial,
                "response": text,
                "stop_reason": resp.stop_reason,
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
                "latency_sec": round(latency, 3),
                "attempts": attempt + 1,
                "error": None,
            }
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            last_error = f"{type(e).__name__}: {e}"
            # Exponential backoff with jitter.
            sleep = BACKOFF_BASE ** attempt + random.uniform(0, 0.5)
            time.sleep(sleep)
        except Exception as e:
            # Non-retryable: log and break.
            last_error = f"{type(e).__name__}: {e}"
            break

    # All retries exhausted.
    return {
        **trial,
        "response": None,
        "stop_reason": None,
        "input_tokens": None,
        "output_tokens": None,
        "latency_sec": None,
        "attempts": MAX_RETRIES,
        "error": last_error,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results.jsonl",
                        help="Output JSONL path.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate and print trial list without calling the API.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Run only the first N trials (for smoke testing).")
    args = parser.parse_args()

    trials = build_trials()
    if args.limit:
        trials = trials[:args.limit]

    print(f"Total trials: {len(trials)}")
    print(f"Words: {len(WORDS)} | Framings: {len(FRAMINGS)} | "
          f"Trials/cell: {TRIALS_PER_CELL}")
    print(f"Model: {MODEL} | Temperature: {TEMPERATURE} | Max tokens: {MAX_TOKENS}")

    if args.dry_run:
        for t in trials[:5]:
            print(json.dumps(t, indent=2))
        print("...")
        return

    if "ANTHROPIC_API_KEY" not in os.environ:
        raise SystemExit("Set ANTHROPIC_API_KEY environment variable.")

    import anthropic  # imported here so --dry-run works without the SDK

    client = anthropic.Anthropic()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    completed = 0
    failed = 0
    t_start = time.time()

    # Stream results to disk as they finish, so a crash doesn't lose everything.
    with out_path.open("w") as f:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(run_one_trial, client, t): t for t in trials}
            for fut in as_completed(futures):
                result = fut.result()
                f.write(json.dumps(result) + "\n")
                f.flush()
                completed += 1
                if result["error"]:
                    failed += 1
                if completed % 25 == 0 or completed == len(trials):
                    elapsed = time.time() - t_start
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (len(trials) - completed) / rate if rate > 0 else 0
                    print(f"  [{completed:>4}/{len(trials)}] "
                          f"failed={failed} | {rate:.2f} trials/s | "
                          f"ETA {eta:.0f}s")

    elapsed = time.time() - t_start
    print(f"\nDone. {completed} trials in {elapsed:.1f}s ({failed} failed).")
    print(f"Output: {out_path.resolve()}")


if __name__ == "__main__":
    main()
