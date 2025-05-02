from flask import Flask, request, jsonify
from llamaChatbot import query_minecraft_chatbot
import traceback
from classifier import classify_message

app = Flask(__name__)

MAX_MESSAGE_LENGTH = 200

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    raw_msg = data.get('message', '').strip()
    if not isinstance(raw_msg, str) or not raw_msg.strip():
        return jsonify([{"intent": "chat", "message": "Please say something."}])
    if len(raw_msg) > MAX_MESSAGE_LENGTH:
        return jsonify([{"intent": "chat", "message": "Your message is too long."}])
    
    message = raw_msg.strip()
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
