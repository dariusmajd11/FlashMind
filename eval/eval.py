#!/usr/bin/env python3
"""
FlashMind Evaluation Script
=============================
Metric: Concept Coverage Rate (CCR)

For each test case, the script generates flashcards from the passage using
the same prompt and function-calling setup as the live app, then checks what
fraction of expected key concepts appear in the generated card text.

A concept is considered "covered" if it appears as a case-insensitive
substring in any card's question + answer + topic fields combined.

Usage (from project root, with .env configured):
    python eval/eval.py

Results are printed to stdout and saved to eval/results.json.
"""

import json
import os
import sys
from pathlib import Path

# Allow running from project root or from eval/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not set. Copy .env.example to .env and add your key.")
    sys.exit(1)

FLASHCARD_TOOL = {
    "type": "function",
    "function": {
        "name": "generate_flashcards",
        "description": "Generate a set of study flashcards from educational material.",
        "parameters": {
            "type": "object",
            "properties": {
                "flashcards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "answer": {"type": "string"},
                            "topic": {"type": "string"},
                        },
                        "required": ["question", "answer", "topic"],
                    },
                }
            },
            "required": ["flashcards"],
        },
    },
}

SYSTEM_PROMPT = (
    "You are an expert study assistant. Generate 8–15 high-quality flashcards "
    "from the provided study material. Focus on key concepts, definitions, "
    "important facts, and relationships between ideas. Questions should test "
    "understanding, not just surface recall. Answers should be concise but complete."
)


def generate_flashcards(passage: str) -> list[dict]:
    """Call OpenAI with function calling to get structured flashcards."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate flashcards from this study material:\n\n{passage}"},
        ],
        tools=[FLASHCARD_TOOL],
        tool_choice={"type": "function", "function": {"name": "generate_flashcards"}},
    )
    tool_call = response.choices[0].message.tool_calls[0]
    return json.loads(tool_call.function.arguments)["flashcards"]


def compute_ccr(flashcards: list[dict], expected_concepts: list[str]) -> tuple[float, list[str], list[str]]:
    """
    Compute Concept Coverage Rate.
    Returns (score, covered_concepts, missed_concepts).
    """
    combined_text = " ".join(
        f"{c.get('question','')} {c.get('answer','')} {c.get('topic','')}".lower()
        for c in flashcards
    )
    covered, missed = [], []
    for concept in expected_concepts:
        (covered if concept.lower() in combined_text else missed).append(concept)
    score = len(covered) / len(expected_concepts) if expected_concepts else 0.0
    return score, covered, missed


def main():
    test_cases_path = Path(__file__).parent / "test_cases.json"
    results_path = Path(__file__).parent / "results.json"

    with open(test_cases_path) as f:
        test_cases = json.load(f)

    results = []
    total_ccr = 0.0
    error_count = 0

    print(f"\nFlashMind Eval — {len(test_cases)} test cases\n")
    print(f"{'ID':<4} {'Description':<38} {'CCR':>6}  {'Covered/Total':<14} Missed")
    print("─" * 90)

    for tc in test_cases:
        try:
            cards = generate_flashcards(tc["passage"])
            ccr, covered, missed = compute_ccr(cards, tc["expected_concepts"])
            total_ccr += ccr
            n_total = len(tc["expected_concepts"])

            missed_str = ", ".join(missed) if missed else "—"
            print(f"{tc['id']:<4} {tc['description']:<38} {ccr:>5.2f}  {len(covered)}/{n_total:<13} {missed_str}")

            results.append({
                "id": tc["id"],
                "description": tc["description"],
                "ccr": round(ccr, 3),
                "cards_generated": len(cards),
                "covered": covered,
                "missed": missed,
            })

        except Exception as e:
            error_count += 1
            print(f"{tc['id']:<4} {tc['description']:<38} ERROR: {e}")
            results.append({"id": tc["id"], "description": tc["description"], "error": str(e)})

    valid = len(test_cases) - error_count
    avg = total_ccr / valid if valid else 0.0

    print("─" * 90)
    print(f"\nAverage CCR: {avg:.3f}  ({avg*100:.1f}%)  [{valid}/{len(test_cases)} cases succeeded]\n")

    output = {"avg_ccr": round(avg, 3), "n_cases": len(test_cases), "results": results}
    with open(results_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to {results_path}\n")


if __name__ == "__main__":
    main()
