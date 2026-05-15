import json, os, sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_v1(passage):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a study assistant. Generate flashcards as a JSON array with 'question' and 'answer' fields."},
            {"role": "user", "content": f"Generate flashcards from this:\n\n{passage}"}
        ]
    )
    text = response.choices[0].message.content
    text = text.replace("```json","").replace("```","").strip()
    return json.loads(text)

def ccr(cards, concepts):
    combined = " ".join(f"{c.get('question','')} {c.get('answer','')}".lower() for c in cards)
    covered = sum(1 for c in concepts if c.lower() in combined)
    return covered / len(concepts)

with open("eval/test_cases.json") as f:
    cases = json.load(f)

total, errors = 0.0, 0
for tc in cases:
    try:
        cards = generate_v1(tc["passage"])
        score = ccr(cards, tc["expected_concepts"])
        total += score
        print(f"{tc['id']:>2}. {tc['description']:<38} {score:.2f}")
    except Exception as e:
        errors += 1
        print(f"{tc['id']:>2}. {tc['description']:<38} ERROR: {e}")

print(f"\nV1 Average CCR: {total/(len(cases)-errors):.3f}  (errors: {errors})")
