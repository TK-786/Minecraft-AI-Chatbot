from openai import OpenAI
import os
from dotenv import load_dotenv
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an intent classifier for a Minecraft AI assistant. 
Given a user's message, return a JSON array of intents with these fields:

- intent: "action", "chat", or "question"
- If action: include a "type" field like "follow", "gather", "attack", etc.
  Optionally include "target" (like "wood", "zombie") and "amount" if needed.
- If question: include a "query" field with the question.
- If chat: include a "message" field with a short response.

Respond ONLY with the JSON. Do NOT include any explanation. Do NOT include any other text or formatting. Be sure to only return the JSON without any surrounding backticks or markdown formatting."""

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