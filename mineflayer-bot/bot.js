const mineflayer = require("mineflayer");
const { pathfinder, Movements, goals } = require("mineflayer-pathfinder");
const fetch = require("node-fetch");

const bot = mineflayer.createBot({
  host: "localhost",
  port: 25565,
  username: "AssistantBot",
});

bot.loadPlugin(pathfinder);

bot.once("spawn", () => {
  const mcData = require("minecraft-data")(bot.version);
  const defaultMove = new Movements(bot, mcData);
  bot.pathfinder.setMovements(defaultMove);
  bot.chat("Ready to assist!");
});

const delay = (ms) => new Promise((res) => setTimeout(res, ms));

const MAX_CHAT_LENGTH = 100;

async function sendSafeMessage(text) {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  for (let line of lines) {
    while (line.length > 0) {
      let chunk = line;

      if (line.length > MAX_CHAT_LENGTH) {
        const breakpoint = line.lastIndexOf(" ", MAX_CHAT_LENGTH);
        chunk =
          breakpoint > 0
            ? line.slice(0, breakpoint)
            : line.slice(0, MAX_CHAT_LENGTH);
      }

      bot.chat(chunk);
      await delay(1000);

      line = line.slice(chunk.length).trimStart();
    }
  }
}

bot.on("chat", async (username, message) => {
  if (username === bot.username) return;

  console.log(`Received chat: ${message}`);

  try {
    const res = await fetch("http://localhost:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, username }),
    });

    const data = await res.json();
    console.log("Received from Python:", data);

    if (data.action === "follow" && bot.players[username]?.entity) {
      await sendSafeMessage("Following you!");
      const goal = new goals.GoalFollow(bot.players[username].entity, 3);
      bot.pathfinder.setGoal(goal, true);
    } else if (data.action === "say") {
      await sendSafeMessage(data.message || "Okay.");
    } else {
      await sendSafeMessage("I didn't understand that.");
    }
  } catch (err) {
    console.error("Error calling Python server:", err);
    await sendSafeMessage("Something went wrong talking to my brain 😵");
  }
});
