from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder="static")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# In-memory chat history keyed by session ID
chat_histories: dict = {}

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
                            "question": {"type": "string", "description": "The question side of the card."},
                            "answer": {"type": "string", "description": "The answer side of the card (1–3 sentences)."},
                            "topic": {"type": "string", "description": "Key concept this card covers (1–3 words)."}
                        },
                        "required": ["question", "answer", "topic"]
                    }
                }
            },
            "required": ["flashcards"]
        }
    }
}


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    """Generate flashcards from study text using function calling (structured output)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body."}), 400

    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided."}), 400
    if len(text) > 10000:
        return jsonify({"error": "Text too long. Please limit to 10,000 characters."}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert study assistant. Generate 8–15 high-quality flashcards "
                        "from the provided study material. Focus on key concepts, definitions, "
                        "important facts, and relationships between ideas. Questions should test "
                        "understanding, not just surface recall. Answers should be concise but complete."
                    ),
                },
                {"role": "user", "content": f"Generate flashcards from this study material:\n\n{text}"},
            ],
            tools=[FLASHCARD_TOOL],
            tool_choice={"type": "function", "function": {"name": "generate_flashcards"}},
        )
        tool_call = response.choices[0].message.tool_calls[0]
        result = json.loads(tool_call.function.arguments)
        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse AI response. Please try again."}), 500
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500


@app.route("/api/adaptive", methods=["POST"])
def adaptive():
    """Generate targeted flashcards for topics the student struggled with."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body."}), 400

    weak_topics = data.get("weak_topics", [])
    original_text = data.get("original_text", "")

    if not weak_topics:
        return jsonify({"error": "No weak topics provided."}), 400

    topics_str = ", ".join(weak_topics)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert study assistant helping a student reinforce weak areas. "
                        "Generate 5–8 additional flashcards that approach the weak topics from "
                        "different angles — use analogies, apply concepts to examples, or ask about "
                        "relationships between ideas. Do NOT repeat questions from a previous session."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"The student struggled with: {topics_str}.\n\n"
                        f"Study material for context:\n{original_text[:4000]}\n\n"
                        "Generate targeted flashcards to reinforce these weak areas."
                    ),
                },
            ],
            tools=[FLASHCARD_TOOL],
            tool_choice={"type": "function", "function": {"name": "generate_flashcards"}},
        )
        tool_call = response.choices[0].message.tool_calls[0]
        result = json.loads(tool_call.function.arguments)
        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse AI response. Please try again."}), 500
    except Exception as e:
        return jsonify({"error": f"Adaptive generation failed: {str(e)}"}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """Multi-turn study chat grounded in the student's uploaded notes."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body."}), 400

    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    context = data.get("context", "")

    if not message:
        return jsonify({"error": "No message provided."}), 400
    if len(message) > 2000:
        return jsonify({"error": "Message too long (max 2000 characters)."}), 400

    if session_id not in chat_histories:
        chat_histories[session_id] = []

    system_content = (
        "You are a helpful study tutor. Answer questions clearly and concisely. "
        "Use examples to clarify difficult concepts. If the student seems confused, "
        "try a different explanation approach. Keep responses under 200 words unless "
        "a longer explanation is truly necessary."
    )
    if context:
        system_content += f"\n\nThe student's study material (for reference):\n{context[:3000]}"

    chat_histories[session_id].append({"role": "user", "content": message})
    history_window = chat_histories[session_id][-12:]  # keep last 12 turns

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_content}] + history_window,
        )
        reply = response.choices[0].message.content
        chat_histories[session_id].append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply, "session_id": session_id})

    except Exception as e:
        chat_histories[session_id].pop()  # undo the user message we added
        return jsonify({"error": f"Chat failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
