# GPT Chatbot Minecraft Assistant

This includes:

- `mineflayer-bot`: A Minecraft bot that listens to chat and acts based on a GPT-like assistant
- `chatbot-server`: A simple Flask server that receives messages and returns actions

## Requirements

### For the bot:

- Node.js
- `npm install mineflayer mineflayer-pathfinder node-fetch`

### For the Python chatbot:

- Python 3.7+
- `pip install flask`

## Run Instructions

### 1. Start your Minecraft server (localhost)

```
cd minecraft-server
start.bat
```

### 2. In one terminal, run the chatbot:

```
cd chatbot-server
venv/Scripts/activate
python server.py
```

### 3. In another terminal, run the bot:

```
cd mineflayer-bot
node bot.js
```
