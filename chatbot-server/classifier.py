from openai import OpenAI
import os
from dotenv import load_dotenv
import re
from minecraft_tags import STRUCTURES, BIOMES, POI

load_dotenv()

structure_list = ", ".join(STRUCTURES)
biome_list = ", ".join(BIOMES)
poi_list = ", ".join(POI)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an intent classifier for a Minecraft AI assistant.

Given a user's message, return a JSON array of intent objects with the following fields:

- "intent": one of "action", "chat", or "question"

- If intent is "action":
    - "type": the action type, such as "follow", "gather", "attack", or "locate"
    - Optional fields:
        - "target": a Minecraft target (e.g., "zombie", "wood", etc.)
        - "amount": a number, if the action involves quantity
    - For "locate" specifically:
        - "target_type": one of "structure", "biome", or "poi"
        - "target": Must be a valid Minecraft ID from one of:
            - For structures, one of: {structure_list}
            - For biomes, one of: {biome_list}
            - For POIs, one of: {poi_list}
        Ensure the target is a valid Minecraft ID from the provided lists. 
        The target MUST be from the lists provided, not a general term.
        Match the user's request to the closest exact Minecraft ID from the lists below. Do not invent new terms.
        If the user says a general term like "village", convert it to the most relevant specific ID from the list, such as "village_plains".
        You MUST pick the closest matching ID from the appropriate list (structures, biomes, POIs) and only use that.

- If intent is "question":
    - "query": the user's question

- If intent is "chat":
    - "message": a brief friendly response

Your response must be:
- Pure JSON array with no additional commentary
- No markdown
- No explanation
- No backticks
- No quotes around the JSON object

Return only the raw JSON output like this:
[
  { "intent": "action", "type": "locate", "target_type": "biome", "target": "plains" }
]

[
    {
        "intent": "action",
        "type": "attack",
        "target": "zombie"
    }
]
"""

def classify_message(message: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)  # remove ```json\n or ```
            raw = raw.rstrip("```").strip()


        print("Raw GPT Output:", raw)
        parsed = eval(raw)  
        return parsed
    except Exception as e:
        print("GPT classification failed:", e)
        return [{"intent": "chat", "message": "Hmm, I'm not sure how to respond to that. Maybe try again?"}]
    

if __name__ == "__main__":
    test_messages = [
        "Can you gather some wood?",
        "What is the best way to build a house?",
        "Hello, how are you?",
        "Attack the zombie!",
        "Can you follow me?",
        "How do I make a crafting table?",
        "Tell me a joke.",
        "Where can I find diamonds?",
        "Gather 10 pieces of iron.",
    ]

    for message in test_messages:
        print(f"Message: {message}")
        result = classify_message(message)
        print("Result:", result)