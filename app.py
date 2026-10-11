
from flask import Flask, render_template, jsonify
from ollama import chat
import requests
import os
import json
import re
import random

app = Flask(__name__)

# AI configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

PROMPT = """
You are TouchGrass, an AI outdoor mission generator.

Create one safe, fun outdoor mission for one person.

Rules:
- The mission should take about 10 minutes.
- It must work in an ordinary outdoor area.
- Do not assume a particular location exists.
- No photos, internet, social media, or equipment.
- Do not ask users to use their phones outdoors.
- Do not touch, pick, collect, eat, or damage living things.
- Avoid roads, climbing, unsafe areas, and strangers.
- Focus on observing nature and surroundings.
- Give exactly 3 short instructions.
- Points must be between 10 and 50.

Return ONLY valid JSON:
{
    "mission": "A short mission title",
    "instructions": [
        "First instruction",
        "Second instruction",
        "Third instruction"
    ],
    "time_minutes": 10,
    "points": 20
}
"""


# Backup missions if hosted AI fails
FALLBACK_MISSIONS = [
    {
        "mission": "Discover the sounds around you.",
        "instructions": [
            "Find a safe and peaceful outdoor spot.",
            "Listen for three different sounds.",
            "Notice which sound you enjoy the most."
        ],
        "time_minutes": 10,
        "points": 20
    },
    {
        "mission": "Explore the colours of nature.",
        "instructions": [
            "Step outside and observe your surroundings.",
            "Find five different colours around you.",
            "Notice where each colour appears naturally."
        ],
        "time_minutes": 10,
        "points": 25
    },
    {
        "mission": "Go on a texture hunt.",
        "instructions": [
            "Walk around a safe outdoor area.",
            "Find three different textures without touching anything.",
            "Compare the patterns and shapes you notice."
        ],
        "time_minutes": 10,
        "points": 30
    },
    {
        "mission": "Discover patterns outdoors.",
        "instructions": [
            "Look for repeating shapes in your surroundings.",
            "Identify three interesting patterns.",
            "Choose your favourite pattern and observe it."
        ],
        "time_minutes": 10,
        "points": 20
    },
    {
        "mission": "Find beauty in the little things.",
        "instructions": [
            "Take a slow walk in a familiar outdoor area.",
            "Notice three small details you usually overlook.",
            "Spend a moment appreciating your favourite discovery."
        ],
        "time_minutes": 10,
        "points": 25
    },
    {
        "mission": "Explore the shapes around you.",
        "instructions": [
            "Find a safe place to observe your surroundings.",
            "Spot three different shapes in nature.",
            "Compare how these shapes appear in different objects."
        ],
        "time_minutes": 10,
        "points": 30
    }
]


def fallback_mission():
    return random.choice(FALLBACK_MISSIONS)


# Generate using local Ollama
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


# Generate using hosted OpenRouter
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
            "temperature": 0.7,
            "max_tokens": 1200,
            "response_format": {
                "type": "json_object"
            }
        },
        timeout=25
    )

    if not response.ok:
        app.logger.error(
            "OpenRouter HTTP error %s: %s",
            response.status_code,
            response.text[:500]
        )
        response.raise_for_status()

    result = response.json()

    message = result["choices"][0]["message"]

    return message.get("content") or ""


# Generate and validate a mission
def generate_mission():

    if AI_PROVIDER == "ollama":
        content = generate_with_ollama()

    elif AI_PROVIDER == "openrouter":
        content = generate_with_openrouter()

    else:
        raise ValueError("Invalid AI_PROVIDER setting.")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("AI returned empty content.")

    content = content.strip()

    # Remove Markdown code fences
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    # Parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Some models include explanations around the JSON
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if not match:
            raise ValueError("AI did not return JSON.")

        data = json.loads(match.group())

    # Validate mission
    if not isinstance(data, dict):
        raise ValueError("Invalid mission data.")

    mission = data.get("mission")
    instructions = data.get("instructions")
    points = data.get("points")

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


# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Mission API
@app.route("/api/mission", methods=["GET"])
def mission():
    try:
        result = generate_mission()
        return jsonify(result)

    except Exception:
        app.logger.exception("AI mission generation failed")

        # If AI fails, return a backup mission
        return jsonify(fallback_mission())


if __name__ == "__main__":
    app.run(debug=True)
