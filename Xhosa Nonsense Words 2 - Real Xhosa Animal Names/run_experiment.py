"""
Real Xhosa Word Control Study (§7.3 of original prereg)
========================================================

This is the matched control for the pilot study. The pilot showed Claude
produces clarification_request 94% of the time when given pseudo-Xhosa
"animal" framings under neutral or false_presupposition. This study tests
whether that pattern is about non-existence (the words have no referent)
or about pseudo-Xhosa-recognition (the words look unfamiliar regardless).

Design (identical to pilot except for word list):
- 10 REAL Xhosa animal names (5 famous + 5 obscure)
- 1 category: "animal"
- 3 prompt framings (permission_granted, neutral, false_presupposition)
- 20 trials per (word x framing) cell
- Total: 600 trials

Note: under permission_granted, the prompt becomes "Please describe an
Indlovu as an imaginary animal" — slightly odd for a real animal, but
preserved to keep the framing manipulation identical to the pilot.

Differences from pilot run_experiment.py:
- Built-in request throttling (avoids the rate-limit cascade we hit
  last time)
- Resume support: re-running picks up where it left off
- Same MODEL, TEMPERATURE, MAX_TOKENS as pilot for direct comparability
"""

import argparse
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ---------------------------------------------------------------------------
# Stimuli — REAL Xhosa animal names, capitalized to match pilot format.
# ---------------------------------------------------------------------------

WORDS_FAMOUS = [
    "Indlovu",   # elephant
    "Ingwe",     # leopard
    "Inyathi",   # buffalo
    "Inkawu",    # monkey
    "Inja",      # dog
]

WORDS_OBSCURE = [
    "Ihlosi",    # cheetah
    "Ingqawa",   # caracal
    "Inyhwagi",  # civet
    "Ixhwili",   # African wild dog
    "Imbabala",  # bushbuck
]

WORDS = WORDS_FAMOUS + WORDS_OBSCURE

# Familiarity tag carried into output for downstream analysis
FAMILIARITY = (
    {w: "famous" for w in WORDS_FAMOUS}
    | {w: "obscure" for w in WORDS_OBSCURE}
)

FRAMINGS = {
    "permission_granted":   "Please describe {a_word} as an imaginary animal.",
    "neutral":              "Please describe {a_word}. It's an animal.",
    "false_presupposition": "What is {a_word}? I've heard it's an animal.",
}

TRIALS_PER_CELL = 20


def with_article(word):
    """Return 'a Word' or 'an Word' as English grammar requires.
    All Xhosa noun-class prefixes used here begin with i-, so all real-word
    prompts use 'an'. The pseudo-words from the pilot all started with
    consonants. This helper keeps the article grammatical without changing
    framing structure."""
    return f"an {word}" if word[0].lower() in "aeiou" else f"a {word}"

# ---------------------------------------------------------------------------
# Config — matched to pilot for direct comparability.
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 400
TEMPERATURE = 1.0

# Throttling: pilot hit 50 req/min limit. Stay under at ~40 req/min.
MAX_WORKERS = 4
MIN_INTERVAL_SEC = 1.5  # Min seconds between request submissions.

MAX_RETRIES = 5
BACKOFF_BASE = 3.0      # Slightly more aggressive backoff than pilot.

PROGRESS_INTERVAL = 25

# ---------------------------------------------------------------------------

def build_trials():
    trials = []
    idx = 0
    for word in WORDS:
        a_word = with_article(word)
        for framing_name, template in FRAMINGS.items():
            prompt = template.format(a_word=a_word)
            for n in range(TRIALS_PER_CELL):
                trials.append({
                    "trial_id": f"{idx:04d}",
                    "word": word,
                    "familiarity": FAMILIARITY[word],
                    "framing": framing_name,
                    "trial_n": n,
                    "prompt": prompt,
                })
                idx += 1
    return trials


# ---------------------------------------------------------------------------
# Throttle: ensures min interval between request submissions across threads.
# ---------------------------------------------------------------------------

class Throttle:
    def __init__(self, min_interval):
        self.min_interval = min_interval
        self.last_submit = 0.0
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.time()
            wait = self.min_interval - (now - self.last_submit)
            if wait > 0:
                time.sleep(wait)
            self.last_submit = time.time()


# ---------------------------------------------------------------------------

def run_one_trial(client, trial, throttle):
    import anthropic
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            throttle.wait()
            t0 = time.time()
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[{"role": "user", "content": trial["prompt"]}],
            )
            latency = time.time() - t0
            text = "".join(
                b.text for b in resp.content
                if getattr(b, "type", None) == "text"
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
            sleep = BACKOFF_BASE ** attempt + random.uniform(0, 1.0)
            time.sleep(sleep)
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            break

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

def load_completed_ids(path):
    """Read existing JSONL output and return set of trial_ids already done
    (with non-error responses). Used for resume support."""
    if not Path(path).exists():
        return set()
    done = set()
    with open(path) as f:
        for line in f:
            try:
                row = json.loads(line)
                if row.get("response") is not None and row.get("error") is None:
                    done.add(row["trial_id"])
            except json.JSONDecodeError:
                continue
    return done


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true",
                        help="Skip trials whose IDs already appear successfully "
                             "in the output file. Appends to that file.")
    args = parser.parse_args()

    trials = build_trials()
    if args.limit:
        trials = trials[:args.limit]

    print(f"Total trials: {len(trials)}")
    print(f"Words: {len(WORDS)} ({len(WORDS_FAMOUS)} famous + "
          f"{len(WORDS_OBSCURE)} obscure)")
    print(f"Framings: {len(FRAMINGS)} | Trials/cell: {TRIALS_PER_CELL}")
    print(f"Model: {MODEL} | Temp: {TEMPERATURE} | Max tokens: {MAX_TOKENS}")
    print(f"Throttle: {MAX_WORKERS} workers, "
          f"min {MIN_INTERVAL_SEC}s between submissions")

    if args.dry_run:
        for t in trials[:6]:
            print(json.dumps(t, indent=2))
        return

    if "ANTHROPIC_API_KEY" not in os.environ:
        raise SystemExit("Set ANTHROPIC_API_KEY environment variable.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.resume:
        done_ids = load_completed_ids(out_path)
        trials = [t for t in trials if t["trial_id"] not in done_ids]
        print(f"Resume: skipping {len(done_ids)} already-completed trials, "
              f"running {len(trials)} more.")
        file_mode = "a"
    else:
        if out_path.exists():
            print(f"WARNING: {out_path} exists. Use --resume to append, "
                  f"or delete the file to start fresh.")
            return
        file_mode = "w"

    if not trials:
        print("Nothing to do.")
        return

    import anthropic
    client = anthropic.Anthropic()
    throttle = Throttle(MIN_INTERVAL_SEC)

    completed = 0
    failed = 0
    t_start = time.time()

    with out_path.open(file_mode) as f:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(run_one_trial, client, t, throttle): t
                for t in trials
            }
            for fut in as_completed(futures):
                result = fut.result()
                f.write(json.dumps(result) + "\n")
                f.flush()
                completed += 1
                if result["error"]:
                    failed += 1
                if completed % PROGRESS_INTERVAL == 0 or completed == len(trials):
                    elapsed = time.time() - t_start
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (len(trials) - completed) / rate if rate > 0 else 0
                    print(f"  [{completed:>4}/{len(trials)}] "
                          f"failed={failed} | {rate:.2f} trials/s | "
                          f"ETA {eta:.0f}s")

    elapsed = time.time() - t_start
    print(f"\nDone. {completed} trials in {elapsed:.1f}s ({failed} failed).")
    print(f"Output: {out_path.resolve()}")
    if failed:
        print("Re-run with --resume to retry the failed trials.")


if __name__ == "__main__":
    main()
