
from flask import Flask, render_template, jsonify
from ollama import chat
import json
import re

app = Flask(__name__)


def generate_mission():
    prompt = """
You are TouchGrass, an AI outdoor mission generator.

Create one safe, fun outdoor mission for one person.

Rules:
- It must take about 10 minutes.
- It must work in an ordinary outdoor area.
- Do not assume a particular location exists.
- Do not ask the user to use a phone during the mission.
- No photos, internet, social media, or special equipment.
- Do not touch, pick, collect, eat, or damage living things.
- The person should observe their surroundings.
- Return exactly 3 short instructions.
- Choose a random-sounding, engaging mission.
- Points must be between 10 and 50.

Return ONLY valid JSON in this format:
{
  "mission": "One short sentence",
  "instructions": ["Step one", "Step two", "Step three"],
  "time_minutes": 10,
  "points": 20
}
"""

    response = chat(
        model="qwen2.5:1.5b",
        messages=[{"role": "user", "content": prompt}],
        format="json",
        options={"temperature": 0.8}
    )

    content = response["message"]["content"].strip()

    # Handle code fences if the model returns them.
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    data = json.loads(content)

    # Validate the result before sending it to the website.
    if not isinstance(data.get("mission"), str) or not data["mission"].strip():
        raise ValueError("The AI returned an invalid mission.")

    instructions = data.get("instructions")
    if not isinstance(instructions, list) or len(instructions) < 3:
        raise ValueError("The AI returned insufficient instructions.")

    data["instructions"] = instructions[:3]

    points = data.get("points")
    if not isinstance(points, int) or isinstance(points, bool) or not 10 <= points <= 50:
        data["points"] = 20

    data["time_minutes"] = 10

    return data


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/mission", methods=["GET"])
def mission():
    try:
        return jsonify(generate_mission())
    except Exception as error:
        app.logger.exception("Mission generation failed")
        return jsonify({
            "error": "Could not generate a mission. Check that Ollama is running and Qwen is installed."
        }), 503


if __name__ == "__main__":
    app.run(debug=True)