import json, os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOL = {"type":"function","function":{"name":"generate_flashcards","parameters":{"type":"object","properties":{"flashcards":{"type":"array","items":{"type":"object","properties":{"question":{"type":"string"},"answer":{"type":"string"},"topic":{"type":"string"}},"required":["question","answer","topic"]}}},"required":["flashcards"]}}}

def generate_v2(passage):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"You are a study assistant. Generate flashcards from the provided study material."},
            {"role":"user","content":f"Generate flashcards from this:\n\n{passage}"}
        ],
        tools=[TOOL],
        tool_choice={"type":"function","function":{"name":"generate_flashcards"}}
    )
    return json.loads(r.choices[0].message.tool_calls[0].function.arguments)["flashcards"]

def ccr(cards, concepts):
    combined = " ".join(f"{c.get('question','')} {c.get('answer','')} {c.get('topic','')}".lower() for c in cards)
    return sum(1 for c in concepts if c.lower() in combined) / len(concepts)

with open("eval/test_cases.json") as f:
    cases = json.load(f)

total, errors = 0.0, 0
for tc in cases:
    try:
        cards = generate_v2(tc["passage"])
        score = ccr(cards, tc["expected_concepts"])
        total += score
        print(f"{tc['id']:>2}. {tc['description']:<38} {score:.2f}")
    except Exception as e:
        errors += 1
        print(f"{tc['id']:>2}. ERROR: {e}")

print(f"\nV2 Average CCR: {total/(len(cases)-errors):.3f}  (errors: {errors})")
