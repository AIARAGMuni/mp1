# ── Load .env so OPENAI_API_KEY is available ────────────────────────────────
from dotenv import load_dotenv
from pathlib import Path

# Walk up from src/ to find the project-root .env
_here = Path().resolve()
_env_path = next(
    (p / '.env' for p in [_here, *_here.parents] if (p / '.env').exists()),
    None
)
load_dotenv(_env_path, override=True)
print(f'Environment loaded from: {_env_path}')

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
from openai import AsyncOpenAI

# Read credentials loaded from .env
api_key  = os.getenv('OPEN_API_KEY')
api_base = os.getenv('OPEN_API_BASE')

#assert api_key,  'OPENAI_API_KEY not set — check your .env'
#assert api_base, 'OPENAI_API_BASE not set — check your .env'

client = AsyncOpenAI(api_key=api_key, base_url=api_base)

MODEL       = 'gpt-4o-mini'
JUDGE_MODEL = 'gpt-4o'
TEMPERATURE = 0.0

# Cost rates ($ per token) — from W4 cost.py
RATES = {
    'gpt-4o-mini': {'in': 0.15 / 1_000_000, 'out': 0.60 / 1_000_000},
    'gpt-4o':      {'in': 2.50 / 1_000_000, 'out': 10.00 / 1_000_000},
}

print('Setup complete.')

import json
from pathlib import Path

# Anchor all paths to the project root (one level above this script's src/ dir)
_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _ROOT / 'data'

snippets = [
    json.loads(line)
    for line in (DATA_DIR / 'job_snippets.jsonl').read_text(encoding='utf-8').splitlines()
    if line.strip()
]

golden = {
    row['id']: row
    for row in (
        json.loads(line)
        for line in (DATA_DIR / 'golden_set.jsonl').read_text(encoding='utf-8').splitlines()
        if line.strip()
    )
}

print(f'Loaded {len(snippets)} snippets, {len(golden)} golden entries.')
print('Sample snippet:', snippets[0])

# Add src/ to path so prompts.py is importable
import sys

_src = Path(__file__).resolve().parent   # always the actual src/ dir
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from prompts import (
    prompt_zero_shot,
    prompt_few_shot,
    prompt_structured,
    prompt_cot,
    STRATEGIES,
)

# Quick sanity check — verify each strategy returns a non-empty messages list
sample_text = snippets[0]['snippet']
for name, fn in STRATEGIES.items():
    msgs = fn(sample_text)
    assert isinstance(msgs, list) and len(msgs) > 0, f'{name} returned empty messages'
    print(f'  {name}: {len(msgs)} message(s), first role = {msgs[0]["role"]}')

print('\nAll four strategies verified.')

def parse_response(text: str) -> dict | None:
    """
    Extract and parse a JSON object from a model response.

    Handles:
      • Pure JSON string
      • JSON wrapped in ```json ... ``` or ``` ... ``` fences
      • JSON embedded after chain-of-thought prose
    """
    if not text or not text.strip():
        return None

    # Strip markdown code fences
    cleaned = re.sub(r'```(?:json)?\s*', '', text)
    cleaned = cleaned.replace('```', '')

    # Try direct parse first (handles pure JSON or fenced JSON)
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass

    # Find the last JSON object in the text (handles CoT preamble)
    # Use last match so we skip any reasoning and grab the final answer
    matches = list(re.finditer(r'\{[^{}]*\}', cleaned, re.DOTALL))
    if matches:
        try:
            return json.loads(matches[-1].group())
        except json.JSONDecodeError:
            pass

    return None


def compute_cost(usage, model: str) -> float:
    """Compute USD cost from a usage object and model name."""
    rates = RATES.get(model, RATES['gpt-4o-mini'])
    return (
        usage.prompt_tokens     * rates['in'] +
        usage.completion_tokens * rates['out']
    )


print('Helper functions defined.')

async def run_one(strategy_name: str, snippet: dict) -> dict:
    """
    Run one strategy against one snippet.

    Returns a dict with:
      strategy, snippet_id, raw_response, parsed, cost_usd, latency_s
    """
    prompt_fn = STRATEGIES[strategy_name]
    messages  = prompt_fn(snippet['snippet'])

    t0 = time.perf_counter()
    response = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )
    latency_s = time.perf_counter() - t0

    raw_text = response.choices[0].message.content or ''
    parsed   = parse_response(raw_text)
    cost_usd = compute_cost(response.usage, MODEL)

    return {
        'strategy':     strategy_name,
        'snippet_id':   snippet['id'],
        'raw_response': raw_text,
        'parsed':       parsed,
        'cost_usd':     cost_usd,
        'latency_s':    latency_s,
    }


async def run_all() -> list[dict]:
    """
    Run all 10 × 4 = 40 calls concurrently using asyncio.gather.
    Returns a flat list of result dicts.
    """
    tasks = [
        run_one(strategy_name, snippet)
        for strategy_name in STRATEGIES
        for snippet in snippets
    ]
    print(f'Launching {len(tasks)} concurrent LLM calls …')
    results = await asyncio.gather(*tasks)
    print(f'Done. Got {len(results)} results.')
    return list(results)


print('Async functions defined.')


def normalise_str(value) -> str:
    """Lowercase, strip whitespace from a string field."""
    if value is None:
        return ''
    return str(value).strip().lower()


def normalise_years(value) -> int | None:
    """
    Coerce years_experience_required to int or None.
    Handles: int, float, '5', '5+', '3-5' (→ 3), null/None.
    """
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in ('null', 'none', ''):
        return None
    s = s.strip('+')
    m = re.match(r'(\d+)', s)
    if m:
        return int(m.group(1))
    return None


def score_accuracy(extracted: dict | None, gold: dict) -> int:
    """
    Compare three fields against the golden record.
    Returns 0–3 (one point per correct field).

    Rules:
      company / role  — case-insensitive string match after whitespace trim
      years           — integer match; None must match null in golden
    """
    if extracted is None:
        return 0

    score = 0

    # company
    if normalise_str(extracted.get('company')) == normalise_str(gold.get('company')):
        score += 1

    # role
    if normalise_str(extracted.get('role')) == normalise_str(gold.get('role')):
        score += 1

    # years_experience_required
    extracted_years = normalise_years(extracted.get('years_experience_required'))
    gold_years      = gold.get('years_experience_required')  # already int or None
    if extracted_years == gold_years:
        score += 1

    return score


print('Scoring functions defined.')


# LLM-as-judge rubric — holistic 1–25 score
JUDGE_SYSTEM = (
    'You are an evaluation judge assessing how accurately an AI model extracted '
    'structured data from a job posting. You will be given the source text, the '
    'reference (correct) extraction, and the model\'s extraction. '
    'Score the model\'s extraction from 1 to 25 using this rubric:\n\n'
    '  21–25 — All three fields correct, exact or near-exact match.\n'
    '  15–20 — Two of three fields correct, no fabricated data.\n'
    '   8–14 — One field correct, or minor field errors.\n'
    '   1– 7 — No fields correct, response unparsable, or significant hallucination.\n\n'
    'Penalise heavily if the model fabricates a years figure when the posting does not state one.\n'
    'Reply with a single integer and nothing else.'
)


async def score_llm_judge(
    snippet_text: str,
    extracted: dict | None,
    gold: dict,
) -> int:
    """
    Ask gpt-4o to judge how well the extraction matches the golden record.
    Returns an integer 1–25.
    """
    user_msg = (
        f'Source text:\n{snippet_text}\n\n'
        f'Reference extraction:\n'
        f'{json.dumps({k: gold[k] for k in ("company", "role", "years_experience_required")}, indent=2)}\n\n'
        f'Model extraction:\n'
        f'{json.dumps(extracted, indent=2) if extracted else "null (failed to parse)"}\n\n'
        'Score (1–25):'
    )

    try:
        response = await client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {'role': 'system', 'content': JUDGE_SYSTEM},
                {'role': 'user',   'content': user_msg},
            ],
            temperature=0.0,
        )
        raw = response.choices[0].message.content.strip()
        return int(re.search(r'\d+', raw).group())
    except Exception as e:
        print(f'  Judge error: {e}')
        return 1


print('LLM judge function defined.')


async def main():
    # ── Run all 40 calls (or load from cache) ────────────────────────────────
    RAW_CACHE = _ROOT / 'results_raw.json'

    if RAW_CACHE.exists():
        print(f'Loading cached raw results from {RAW_CACHE}')
        results = json.loads(RAW_CACHE.read_text(encoding='utf-8'))
    else:
        results = await run_all()
        RAW_CACHE.write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(f'Raw results cached to {RAW_CACHE}')

    print(f'Got {len(results)} results.')

    # ── Apply scoring to all 40 results ──────────────────────────────────────
    SCORED_CACHE = _ROOT / 'results_scored.json'

    if SCORED_CACHE.exists():
        print(f'Loading cached scored results from {SCORED_CACHE}')
        scored = json.loads(SCORED_CACHE.read_text(encoding='utf-8'))
    else:
        # Build snippet text lookup
        snippet_lookup = {s['id']: s['snippet'] for s in snippets}

        # Step 4a — deterministic scores (no API call)
        for row in results:
            gold = golden[row['snippet_id']]
            row['parse_success'] = row['parsed'] is not None
            row['accuracy']      = score_accuracy(row['parsed'], gold)

        # Step 4b — LLM judge (fire all 40 concurrently)
        print('Running LLM judge on all 40 results …')
        judge_tasks = [
            score_llm_judge(
                snippet_lookup[row['snippet_id']],
                row['parsed'],
                golden[row['snippet_id']],
            )
            for row in results
        ]
        judge_scores = await asyncio.gather(*judge_tasks)

        for row, js in zip(results, judge_scores):
            row['llm_judge_score'] = js

        scored = results
        SCORED_CACHE.write_text(json.dumps(scored, indent=2), encoding='utf-8')
        print(f'Scored results cached to {SCORED_CACHE}')

    print(f'Scored {len(scored)} results.')

    df = pd.DataFrame(scored)

    summary = df.groupby('strategy').agg(
        accuracy        =('accuracy',        'mean'),
        parse_rate      =('parse_success',   'mean'),
        judge_score     =('llm_judge_score', 'mean'),
        total_cost_usd  =('cost_usd',        'sum'),
        latency_p50_s   =('latency_s',       'median'),
    ).round(3)

    # Re-order rows in logical display order
    _order = ['zero_shot', 'few_shot', 'structured', 'cot']
    summary = summary.reindex([s for s in _order if s in summary.index])
    summary.index = ['Zero-shot', 'Few-shot', 'Structured', 'Chain-of-thought']
    summary.columns = ['Accuracy (mean/3)', 'Parse rate', 'Judge score (mean/25)',
                       'Total cost ($)', 'Latency p50 (s)']

    # ── Write comparison table to mp1_comparison.md ──────────────────────────
    COMPARISON_PATH = _ROOT / 'mp1_comparison.md'

    md_lines = [
        '# MP1 — Prompt Strategy Comparison Table',
        '',
        f'Model: `{MODEL}` · Temperature: `{TEMPERATURE}` · 10 job snippets × 4 strategies = 40 calls',
        '',
        summary.to_markdown(),
        '',
        '> **Accuracy** — mean number of correctly extracted fields out of 3 (company, role, years).',
        '> **Parse rate** — proportion of responses that parsed cleanly as JSON.',
        '> **Judge score** — mean score from `gpt-4o`-as-judge (1–25 rubric).',
        '> **Total cost** — USD spend for all 10 snippets of that strategy.',
        '> **Latency p50** — median call latency in seconds.',
    ]

    COMPARISON_PATH.write_text('\n'.join(md_lines), encoding='utf-8')
    print(f'Comparison table written to {COMPARISON_PATH}')
    print()
    print(summary.to_string())

    # ── Cost summary ─────────────────────────────────────────────────────────
    total_main  = sum(r['cost_usd'] for r in scored)
    n_judge     = len(scored)
    est_judge   = n_judge * (RATES['gpt-4o']['in'] * 300 + RATES['gpt-4o']['out'] * 10)

    print(f'Main-strategy spend  (gpt-4o-mini, 40 calls): ${total_main:.5f}')
    print(f'Est. judge spend     (gpt-4o,       40 calls): ~${est_judge:.5f}')
    print(f'Estimated total:                               ~${total_main + est_judge:.5f}')


if __name__ == '__main__':
    asyncio.run(main())
