const mineflayer = require("mineflayer");
const { pathfinder, Movements, goals } = require("mineflayer-pathfinder");
const fetch = require("node-fetch");

// ---------------SPAWN BOT----------------
// This bot will connect to a local Minecraft server
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
// ---------------SPAWN BOT----------------

// ---------------Attack----------------
function attackNearest(targetName) {
  const mob = bot.nearestEntity(
    (entity) =>
      ["mob", "animal", "hostile", "water_creatures"].includes(entity.type) &&
      entity.name.toLowerCase().includes(targetName.toLowerCase())
  );

  console.log(`Looking for: ${targetName.toLowerCase()}`);

  if (!mob) {
    bot.chat(`I can't find any ${targetName}s nearby.`);
    return;
  }

  bot.chat(`Attacking ${mob.name} until it dies...`);

  const goal = new goals.GoalFollow(mob, 1); // follow with distance 1 block
  bot.pathfinder.setGoal(goal, true);

  // Step 2: Keep attacking until mob is gone
  const interval = setInterval(() => {
    if (!mob.isValid) {
      clearInterval(interval);
      bot.pathfinder.setGoal(null);
      sendSafeMessage(`${targetName} defeated!`);
      return;
    }

    bot.lookAt(mob.position.offset(0, mob.height, 0), true);
    bot.attack(mob);
  }, 600); // roughly 1 attack per second
}
// ---------------Attack----------------

// ---------------React to chat----------------
const delay = (ms) => new Promise((res) => setTimeout(res, ms));
const MAX_CHAT_LENGTH = 100;

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

    const intents = Array.isArray(data) ? data : [data];

    for (const intent of intents) {
      const kind = intent.intent || "action";
      const type = intent.type;

      if (kind === "action") {
        if (type === "follow" && bot.players[username]?.entity) {
          await sendSafeMessage("Following you!");
          const goal = new goals.GoalFollow(bot.players[username].entity, 3);
          bot.pathfinder.setGoal(goal, true);
        } else if (type === "attack") {
          const target = intent.target || "zombie";
          attackNearest(target);
        } else if (type === "locate") {
          const targetType = intent.target_type || "structure";
          const target = intent.target || "village";
          await sendSafeMessage(`Locating ${targetType} ${target}...`);
          runLocate(`${targetType} ${target}`);
        } else {
          await sendSafeMessage(`Action '${type}' not supported yet.`);
        }
      } else if (kind === "chat") {
        await sendSafeMessage(intent.message || "Okay.");
      } else {
        await sendSafeMessage("I didn't understand that.");
      }
    }
  } catch (err) {
    console.error("Error calling Python server:", err);
    await sendSafeMessage("Something went wrong talking to my brain 😵");
  }
});

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

let awaitingLocate = false;

function runLocate(target) {
  bot.chat(`/locate ${target}`);
  awaitingLocate = true;
}

bot.on("message", (jsonMsg) => {
  const msg = jsonMsg.toString();
  if (awaitingLocate && msg.includes("at [")) {
    awaitingLocate = false;
    sendSafeMessage(msg);
  }
});
// ---------------Chat----------------
