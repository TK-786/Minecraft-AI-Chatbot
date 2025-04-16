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
        return jsonify(intents)

    except Exception as e:
        print("❌ Error:", e)
        traceback.print_exc()
        return jsonify({"action": "say", "message": "Something went wrong!"})
if __name__ == "__main__":
    app.run(port=5000)
