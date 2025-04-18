from flask import Flask, request, jsonify
from llamaChatbot import query_minecraft_chatbot
import traceback
from classifier import classify_message

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '').strip()
    username = data.get('username', 'Player')

    print(f"🧠 Received from {username}: {message}")

    try:
        intents = classify_message(message)
        responses = []

        for intent_obj in intents:
            intent = intent_obj.get("intent")

            if intent == "chat":
                responses.append({
                    "intent": "chat",
                    "message": intent_obj.get("message", "Okay.")
                })

            elif intent == "question":
                reply = query_minecraft_chatbot(intent_obj["query"])
                responses.append({
                    "intent": "chat",
                    "message": str(reply)
                })

            elif intent == "action":
                action_type = intent_obj.get("type")
                responses.append({
                    "intent": "action",
                    "type": action_type,
                    **{k: v for k, v in intent_obj.items() if k not in ("intent", "type")}
                })

        return jsonify(responses)

    except Exception as e:
        print("❌ Error:", e)
        traceback.print_exc()
        return jsonify({"action": "say", "message": "Something went wrong!"})
if __name__ == "__main__":
    app.run(port=5000)
