# MP1 — Prompt Strategy Comparison Table

Model: `gpt-4o-mini` · Temperature: `0.0` · 10 job snippets × 4 strategies = 40 calls

|                  |   Accuracy (mean/3) |   Parse rate |   Judge score (mean/25) |   Cost ($) |   Latency p50 (s) |
|:-----------------|--------------------:|-------------:|------------------------:|-----------:|------------------:|
| Zero-shot        |                 2.7 |            1 |                    24.2 |      0     |             2.022 |
| Few-shot         |                 2.9 |            1 |                    25   |      0.001 |             1.934 |
| Structured       |                 2.9 |            1 |                    25   |      0.001 |             1.84  |
| Chain-of-thought |                 2.8 |            1 |                    25   |      0.001 |             2.447 |

> **Accuracy** — mean number of correctly extracted fields out of 3 (company, role, years).
> **Parse rate** — proportion of responses that parsed cleanly as JSON.
> **Judge score** — mean score from `gpt-4o`-as-judge (1–25 rubric).
> **Cost** — USD spend for all 10 snippets of that strategy.
> **Latency p50** — median call latency in seconds.