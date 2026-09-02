"""
prompts.py — Four prompting strategies for the MP1 job-extraction task.

Each strategy is a function that accepts a job-posting snippet (str)
and returns a messages list suitable for the OpenAI chat API.

All four extract the same three fields:
  • company                    — the hiring company
  • role                       — the job title
  • years_experience_required  — minimum years (integer, or null if unstated)
"""


# ---------------------------------------------------------------------------
# Strategy 1 — Zero-shot
# Just ask. No examples, no persona, no chain-of-thought.
# ---------------------------------------------------------------------------

def prompt_zero_shot(snippet_text: str) -> list[dict]:
    """Strategy 1 — zero-shot. One sentence, no examples, no persona."""
    return [
        {
            "role": "user",
            "content": (
                "Extract the following fields from the job posting below and return them "
                "as a JSON object with exactly these keys: "
                '"company", "role", "years_experience_required".\n'
                "Use null for years_experience_required if no specific number is stated.\n\n"
                f"Job posting:\n{snippet_text}\n\n"
                "Return only the JSON object, no extra text."
            ),
        }
    ]


# ---------------------------------------------------------------------------
# Strategy 2 — Few-shot
# Show 3 worked examples so the model learns the expected format + edge cases.
# ---------------------------------------------------------------------------

FEW_SHOT_EXAMPLES = """
Example 1:
Posting: "TechCorp is looking for a Backend Engineer with at least 3 years of Python experience."
Output: {"company": "TechCorp", "role": "Backend Engineer", "years_experience_required": 3}

Example 2:
Posting: "BrightHealth needs a Data Scientist. Fresh graduates welcome — no experience required."
Output: {"company": "BrightHealth", "role": "Data Scientist", "years_experience_required": 0}

Example 3:
Posting: "We're hiring. The role is a Product Lead. We're a fast-moving team and don't specify a years requirement."
Output: {"company": null, "role": "Product Lead", "years_experience_required": null}
""".strip()


def prompt_few_shot(snippet_text: str) -> list[dict]:
    """Strategy 2 — few-shot. Three worked examples before the actual snippet."""
    return [
        {
            "role": "user",
            "content": (
                "Extract three fields from a job posting: "
                '"company", "role", and "years_experience_required".\n'
                "Return a JSON object with exactly those keys.\n"
                "Use null for years_experience_required if no specific number is stated.\n"
                "Use the integer value (e.g. 5, not '5+') for years.\n\n"
                f"{FEW_SHOT_EXAMPLES}\n\n"
                f"Now extract from this posting:\n{snippet_text}\n\n"
                "Output:"
            ),
        }
    ]


# ---------------------------------------------------------------------------
# Strategy 3 — Structured / role-based
# System-level persona + explicit JSON schema description.
# ---------------------------------------------------------------------------

STRUCTURED_SYSTEM = (
    "You are an expert recruiter and data extraction specialist. "
    "Your job is to parse job posting text and return structured data. "
    "You always return valid JSON — nothing else. "
    "You are precise: you never infer or fabricate data that is not explicitly stated."
)

STRUCTURED_SCHEMA = (
    "Return a JSON object with exactly these fields:\n"
    "  company (string | null)                — the name of the hiring company\n"
    "  role (string | null)                   — the exact job title\n"
    "  years_experience_required (int | null)  — the minimum years of experience as an integer;\n"
    "                                            use the lower bound of a range (e.g. '3-5 years' → 3);\n"
    "                                            strip '+' and use the number (e.g. '7+' → 7);\n"
    "                                            use 0 if the posting says no experience is required;\n"
    "                                            use null ONLY if no years figure is mentioned at all.\n"
    "Do not include any explanation, markdown, or text outside the JSON object."
)


def prompt_structured(snippet_text: str) -> list[dict]:
    """Strategy 3 — structured/role-based. System persona + explicit JSON schema."""
    return [
        {"role": "system", "content": STRUCTURED_SYSTEM},
        {
            "role": "user",
            "content": (
                f"{STRUCTURED_SCHEMA}\n\n"
                f"Job posting:\n{snippet_text}"
            ),
        },
    ]


# ---------------------------------------------------------------------------
# Strategy 4 — Chain-of-thought (CoT)
# Ask the model to reason step by step, then output JSON.
# ---------------------------------------------------------------------------

def prompt_cot(snippet_text: str) -> list[dict]:
    """Strategy 4 — chain-of-thought. Reason step by step, then emit JSON."""
    return [
        {
            "role": "user",
            "content": (
                "Read the job posting below and extract three fields: "
                '"company", "role", and "years_experience_required".\n\n'
                "Think step by step:\n"
                "  1. Identify the company name. If it is not stated, note that.\n"
                "  2. Identify the job title / role.\n"
                "  3. Find any mention of years of experience. "
                "If a range is given, take the lower bound. "
                "If '0' or 'no experience required' is stated, use 0. "
                "If nothing is mentioned, the value is null.\n"
                "  4. Write your final answer as a JSON object with keys "
                '"company", "role", "years_experience_required".\n\n'
                f"Job posting:\n{snippet_text}\n\n"
                "Work through the steps above, then end with the JSON object."
            ),
        }
    ]


# ---------------------------------------------------------------------------
# Registry — used by the main notebook/script
# ---------------------------------------------------------------------------

STRATEGIES: dict[str, callable] = {
    "zero_shot":  prompt_zero_shot,
    "few_shot":   prompt_few_shot,
    "structured": prompt_structured,
    "cot":        prompt_cot,
}
