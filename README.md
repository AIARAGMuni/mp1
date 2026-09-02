MP1 — Prompt Lab · Compare LLM Strategies on a Task

Author: P Munirathnam
 Email: ailearner.muni@gmail.com

        Overview

This project evaluates and compares four prompting strategies for a structured information extraction task using GPT-4o-mini:

Zero-shot Prompting
Few-shot Prompting
Structured Prompting
Chain-of-Thought (CoT) Prompting

The objective is to extract the following fields from job posting snippets:

"company": "",
"role": "",
"years_experience_required": ""


The experiment uses 10 job-posting snippets and evaluates model performance using:

Deterministic field-level accuracy
JSON parse success rate
GPT-4o-as-Judge evaluation rubric
Cost and latency measurements

        Project Structure

├── data/
│ ├── job_snippets.jsonl # Input job-posting snippets
│ └── golden_set.jsonl # Ground-truth labels
├── mp1/
├── mp1_prompt_lab.ipynb # Interactive notebook
├── mp1_comparison.md # Generated comparison report
├── mp1_writeup.md # Analysis and reflections
├── requirements.txt
└── .env # API credentials 


        Objective

Compare how different prompting strategies influence extraction quality for a simple entity extraction task.

Each prompt asks the model to extract:

company
role
years_experience_required

from unstructured job advertisements and return valid JSON output.

        Prerequisites
Python 3.10 or later
Access to the Vocareum OpenAI-compatible API

    Setup Instructions
1. Open the Project Directory
PowerShell cd "Week 5_Graded Mini Project_P_Munirathnam"

2. Install Dependencies
PowerShell pip install -r requirements.txt

3. Create the Environment File

Create a .env file in the project root:


OPENAI_API_KEY=<your-api-key>

OPENAI_API_BASE=https://openai.vocareum.com/v1

        Running the Project
Option A: Jupyter Notebook (Recommended)

Launch:

VS Code

jupyter notebook mp1/mp1_prompt.ipynb

Run the notebook cells in order:

Cell 1: Environment Setup - Loads API credentials from .env.
Cell 2: Imports - Creates the AsyncOpenAI client.
Cell 3: Load Data - data/job_snippets.jsonl and data/golden_set.jsonl
Cell 4: Prompt Strategies
Cell 5: Run Evaluation - Executes 40 concurrent LLM calls or loads cached results.
Cell 6: Scoring Computes: Deterministic accuracy, LLM judge scores
Cell 7: Summary Metrics - Displays a pandas DataFrame containing: Accuracy,Parse rate,Judge score,Cost,Latency
Cell 8: Markdown Export - mp1_comparison.md
Cell 9: Cost Summary


A GPT-4o judge evaluates extraction quality using the following rubric:

	       Accuracy 
               (mean/3)	Parse rate	Judge score	   Cost ($)	Latency 50 (s)
Zero-shot	     2.7       1.0	    24.2	    0.000	    2.754
Few-shot	     2.8       1.0	    24.6	    0.001	    2.331
Structured	     2.9       1.0	    25.0	    0.001	    2.436
Chain-of-thought     2.8       1.0          25.0	    0.001	    2.523

> **Accuracy** — mean number of correctly extracted fields out of 3 (company, role, years).
> **Parse rate** — proportion of responses that parsed cleanly as JSON.
> **Judge score** — mean score from `gpt-4o`-as-judge (1–25 rubric).
> **Total cost** — USD spend for all 10 snippets of that strategy.
> **Latency p50** — median call latency in seconds.

2. Best Overall Performance

Both:

Few-shot Prompting
Structured Prompting

achieved:

Accuracy = 2.9 / 3
Judge Score = 25 / 25

3. Chain-of-Thought Offered Limited Benefit

Although Chain-of-Thought generated more verbose reasoning:

Accuracy did not improve
Judge scores matched Structured prompting
Median latency increased by approximately 0.7 seconds

This suggests that explicit reasoning may not provide meaningful benefits for straightforward extraction tasks.

4. Zero-shot Was Competitive

Zero-shot prompting performed surprisingly well on clean examples and achieved:

Accuracy = 2.8 / 3
Judge Score = 24.2 / 25

Structured Prompting emerged as the most practical strategy for this task due to:
