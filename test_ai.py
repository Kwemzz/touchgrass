from ollama import chat
import json

response = chat(
    model="qwen2.5:1.5b",
    messages=[
        {
            "role": "user",
            "content": """
            You are the outdoor mission generator for an app called TouchGrass.

            Your job is to create ONE safe, simple outdoor mission for ONE person.

            The purpose of the app is to get the person OFF their phone and physically
            outside. The screen should be used only to read the mission before starting.

            STRICT RULES:

            1. The mission must take about 10 minutes.
            2. The person must physically go outdoors.
            3. The mission must work in an ordinary university campus or neighborhood.
            4. NEVER assume a classroom, laboratory, botanical garden, park, gym,
            sports field, river, forest, or any other specific location exists.
            5. NEVER require the user to use their phone after starting the mission.
            6. NEVER ask the user to take a photo, record audio, use an app, use GPS,
            search the internet, post on social media, or interact with a screen.
            7. NEVER ask the user to collect, pick, touch, eat, or damage plants,
            animals, insects, or other living things.
            8. The user should simply observe their surroundings.
            9. The mission should be possible using only their eyes, ears, and body.
            10. Do not require another person or a group.
            11. Do not require special equipment.
            12. Keep the mission fun and specific.
            13. The instructions must contain exactly 3 steps.
            14. The final instruction should tell the user to finish the activity
                and return when they are done, without using their phone during the task.
            15. Points must be between 10 and 50.

            GOOD EXAMPLES:
            - Find three different leaf shapes without touching the plants.
            - Notice five different sounds around you.
            - Find three places where sunlight and shade meet.
            - Count how many different colors you can see in nature.
            - Find something moving in the wind and observe it for one minute.

            BAD EXAMPLES:
            - Take a picture of a plant.
            - Scan a QR code.
            - Search Google.
            - Upload something to the app.
            - Go to the botanical garden.
            - Leave the classroom.
            - Share your findings online.

            Return ONLY valid JSON.
            Do not use Markdown.
            Do not use ```json.
            Do not include any explanation outside the JSON.

            Use exactly this structure:

            {
                "mission": "one short sentence",
                "instructions": [
                    "step 1",
                    "step 2",
                    "step 3"
                ],
                "time_minutes": 10,
                "points": 20
            }
            """
        }
    ]
)

content = response["message"]["content"]

content = content.strip()

if content.startswith("```json"):
    content = content[7:]

if content.endswith("```"):
    content = content[:-3]

content = content.strip()

data = json.loads(content)

print("MISSION:", data["mission"])
print()
print("INSTRUCTIONS:")

for i, instruction in enumerate(data["instructions"][:3], start=1):
    print(f"{i}. {instruction}")

print()
print("TIME:", data["time_minutes"], "minutes")
print("POINTS:", data["points"])