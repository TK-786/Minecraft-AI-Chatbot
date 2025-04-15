from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an intent classifier for a Minecraft AI assistant. 
Given a user's message, return a JSON array of intents with these fields:

- intent: "action", "chat", or "question"
- If action: include a "type" field like "follow", "gather", "attack", etc.
  Optionally include "target" (like "wood", "zombie") and "amount" if needed.
- If question: include a "query" field with the question.
- If chat: include a "message" field with a short response.

Respond ONLY with the JSON. Do NOT include any explanation. Do NOT include any other text or formatting. Be sure to only return the JSON without any surrounding backticks or formatting."""

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
        raw_text = response.choices[0].message.content.strip()
        print("🔍 Raw GPT Output:", raw_text)
        parsed = eval(raw_text)  
        return parsed
    except Exception as e:
        print("GPT classification failed:", e)
        return [{"intent": "chat", "message": "Hmm, I'm not sure how to respond to that. Maybe try again?"}]