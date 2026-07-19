"""
run.py

Runs the full experiment: for each brand, for each Groq model, ask the same
question under three conditions:

  1. parametric  -- no context, just the model's training knowledge
  2. ambient_web -- Tavily search results injected as context
  3. corrected   -- the verified canonical profile injected as context

Then scores every response against ground truth and prints a comparison
table. This makes real API calls and costs real (free-tier) quota every
time you run it -- expect the numbers to shift run to run, because these
are live models, not fixtures.

Usage:
    pip install -r requirements.txt
    cp .env.example .env   # fill in your two free API keys
    python run.py
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, str(Path(__file__).parent / "data"))
from ground_truth import BRANDS  # noqa: E402

from providers import (  # noqa: E402
    GROQ_MODELS,
    get_groq_client,
    get_tavily_client,
    ask_groq,
    ask_groq_with_context,
    search_web,
)
from extraction import evaluate_response  # noqa: E402
from correction import to_canonical_profile  # noqa: E402

QUESTION_TEMPLATE = (
    "Tell me about {brand}. What do they do, when were they founded, "
    "where are they headquartered, how do they price their product, and "
    "what are their main products or features?"
)


def run_experiment():
    groq_client = get_groq_client()
    tavily_client = get_tavily_client()

    out_path = Path(__file__).parent / "results.json"
    all_results = {}

    for brand_name, gt in BRANDS.items():
        print(f"\n=== {brand_name} ===")
        question = QUESTION_TEMPLATE.format(brand=brand_name)

        print("  Searching the live web via Tavily...")
        web_context = search_web(tavily_client, brand_name)
        canonical_context = to_canonical_profile(brand_name, gt)

        brand_results = {}
        for model in GROQ_MODELS:
            print(f"  Querying {model} under 3 conditions...")
            try:
                model_results = {}

                parametric_answer = ask_groq(groq_client, model, question)
                model_results["parametric"] = {
                    "answer": parametric_answer,
                    "eval": evaluate_response(parametric_answer, gt).as_dict(),
                }
                time.sleep(1)  # be polite to the free tier rate limit

                web_answer = ask_groq_with_context(groq_client, model, question, web_context)
                model_results["ambient_web"] = {
                    "answer": web_answer,
                    "eval": evaluate_response(web_answer, gt).as_dict(),
                }
                time.sleep(1)

                corrected_answer = ask_groq_with_context(groq_client, model, question, canonical_context)
                model_results["corrected"] = {
                    "answer": corrected_answer,
                    "eval": evaluate_response(corrected_answer, gt).as_dict(),
                }
                time.sleep(1)

                brand_results[model] = model_results
            except Exception as e:
                # A single bad/deprecated model name shouldn't cost you the
                # results you already have for every other model and brand.
                print(f"  !! {model} failed, skipping it: {e}")
                continue

        all_results[brand_name] = brand_results

        # Write after every brand, not just at the end -- if something
        # fails on brand 3, you keep brands 1 and 2 instead of losing
        # everything.
        out_path.write_text(json.dumps(all_results, indent=2))

    print(f"\nFull results (including raw model answers) written to {out_path}")
    return all_results


def print_summary_table(all_results):
    print(f"\n{'Brand':<10}{'Model':<24}{'Parametric':>12}{'Ambient Web':>14}{'Corrected':>12}")
    print("-" * 72)
    for brand_name, brand_results in all_results.items():
        for model, conditions in brand_results.items():
            p = conditions["parametric"]["eval"]["score"]
            w = conditions["ambient_web"]["eval"]["score"]
            c = conditions["corrected"]["eval"]["score"]
            print(f"{brand_name:<10}{model:<24}{p:>12.1f}{w:>14.1f}{c:>12.1f}")


if __name__ == "__main__":
    results = run_experiment()
    print_summary_table(results)
