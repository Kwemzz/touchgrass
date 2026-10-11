
from flask import Flask, render_template, jsonify
from ollama import chat
import requests
import os
import json
import re

app = Flask(__name__)

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "qwen/qwen3.8-27b:free"
)

PROMPT = """
You are TouchGrass, an AI outdoor mission generator.

Create one safe, fun outdoor mission for one person.

Rules:
- It must take about 10 minutes.
- It must work in an ordinary outdoor area.
- Do not assume a particular location exists.
- Do not ask the user to use a phone during the mission.
- No photos, internet, social media, or special equipment.
- Do not touch, pick, collect, eat, or damage living things.
- Stay in safe, accessible public or familiar areas.
- Avoid roads, climbing, unsafe terrain, and strangers.
- The person should observe their surroundings.
- Return exactly 3 short instructions.
- Choose a varied, engaging mission.
- Points must be between 10 and 50.

Return ONLY valid JSON in this format:
{
  "mission": "One short sentence",
  "instructions": ["Step one", "Step two", "Step three"],
  "time_minutes": 10,
  "points": 20
}
"""


def generate_with_ollama():
    response = chat(
        model="qwen2.5:1.5b",
        messages=[
            {"role": "user", "content": PROMPT}
        ],
        format="json",
        options={"temperature": 0.8}
    )

    return response["message"]["content"]


def generate_with_openrouter():
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing.")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "user", "content": PROMPT}
            ],
            "temperature": 0.8,
            "max_tokens": 1200,
            "response_format": {
                "type": "json_object"
            }
        },
        timeout=60
    )

    if not response.ok:
        app.logger.error(
            "OpenRouter error %s: %s",
            response.status_code,
            response.text[:1000]
        )
        response.raise_for_status()

    result = response.json()

    message = result["choices"][0]["message"]

    app.logger.warning(
    "OpenRouter model: %s | finish_reason: %s | content: %r",
    result.get("model"),
    result["choices"][0].get("finish_reason"),
    message.get("content")
)

    return message.get("content") or ""


def generate_mission():
    if AI_PROVIDER == "ollama":
        content = generate_with_ollama()

    elif AI_PROVIDER == "openrouter":
        content = generate_with_openrouter()

    else:
        raise ValueError("Invalid AI_PROVIDER configuration.")

    content = content.strip()

    # Remove markdown code fences if present
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    app.logger.warning("Content before JSON parsing: %r", content)

    if not content:
        raise ValueError("OpenRouter returned an empty AI response.")

    try:
        data = json.loads(content)

    except json.JSONDecodeError as error:
        app.logger.error(
            "JSON parsing failed: %s | Content: %r",
            error,
            content[:500]
        )
        raise ValueError("The AI returned invalid JSON.")
    raise ValueError("The AI returned invalid JSON.")

    if not isinstance(data, dict):
        raise ValueError("Invalid AI response.")

    mission = data.get("mission")
    instructions = data.get("instructions")

    if not isinstance(mission, str) or not mission.strip():
        raise ValueError("Invalid mission title.")

    if (
        not isinstance(instructions, list)
        or len(instructions) != 3
        or any(
            not isinstance(step, str) or not step.strip()
            for step in instructions
        )
    ):
        raise ValueError("Invalid mission instructions.")

    points = data.get("points")

    if (
        not isinstance(points, int)
        or isinstance(points, bool)
        or not 10 <= points <= 50
    ):
        points = 20

    return {
        "mission": mission.strip(),
        "instructions": [
            step.strip() for step in instructions
        ],
        "time_minutes": 10,
        "points": points
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/mission", methods=["GET"])
def mission():
    try:
        return jsonify(generate_mission())

    except Exception:
        app.logger.exception("Mission generation failed")

        return jsonify({
            "error": "Could not generate a mission. Please try again."
        }), 503


if __name__ == "__main__":
    app.run(debug=True)
