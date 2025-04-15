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
                # TODO:
                responses.append({"action": "say", "message": intent_obj["message"]})

            elif intent == "question":
                reply = query_minecraft_chatbot(intent_obj["query"])
                responses.append({"action": "say", "message": str(reply)})

            elif intent == "action":
                action_type = intent_obj.get("type")

                if action_type == "follow":
                    responses.append({"action": "follow"})

                else:
                    responses.append({"action": "say", "message": f"Action '{action_type}' not supported yet."})

        return jsonify(responses[0] if responses else {"action": "say", "message": "No valid intent found."})

    except Exception as e:
        print("❌ Error:", e)
        traceback.print_exc()
        return jsonify({"action": "say", "message": "Something went wrong!"})
if __name__ == "__main__":
    app.run(port=5000)
