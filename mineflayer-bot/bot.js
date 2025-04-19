const mineflayer = require("mineflayer");
const { pathfinder, Movements, goals } = require("mineflayer-pathfinder");
const fetch = require("node-fetch");

let cancelCurrentTask = false;

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
    if (cancelCurrentTask) {
      clearInterval(interval);
      bot.pathfinder.setGoal(null);
      return;
    }

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

// ---------------Gather----------------
const blockAliases = {
  wood: [
    "oak_log",
    "birch_log",
    "spruce_log",
    "jungle_log",
    "acacia_log",
    "dark_oak_log",
  ],
  stone: ["cobblestone", "stone", "andesite", "granite", "diorite"],
  sand: ["sand"],
  dirt: ["dirt", "coarse_dirt", "grass"],
  // Add more general -> specific mappings as needed
};

async function gatherTarget(target, amount = 1) {
  const mcData = require("minecraft-data")(bot.version);
  const targets = blockAliases[target.toLowerCase()] || [target.toLowerCase()];
  let gathered = 0;

  bot.chat(`Searching for ${amount} ${target}...`);

  const allBlocks = bot.findBlocks({
    matching: (block) => targets.includes(block.name),
    maxDistance: 32,
    count: amount * 5, // Look for extra in case of failed digs
  });

  if (!allBlocks || allBlocks.length === 0) {
    await sendSafeMessage(`Couldn't find any ${target} nearby.`);
    return;
  }

  for (const pos of allBlocks) {
    if (cancelCurrentTask || gathered >= amount) break;

    try {
      const block = bot.blockAt(pos);
      if (!block || block.name === "air") continue;
      if (block.boundingBox === "empty") continue;

      await bot.pathfinder.goto(new goals.GoalBlock(pos.x, pos.y, pos.z));

      const refreshed = bot.blockAt(pos);
      if (!refreshed || !bot.canDigBlock(refreshed)) continue;

      if (gathered >= amount) break;

      bot.lookAt(refreshed.position.offset(0.5, 0.5, 0.5), true);
      await bot.dig(refreshed);
      gathered++;
    } catch (err) {
      console.error(`Skipping block at ${pos}:`, err.message);
    }
  }

  if (gathered >= amount) {
    await sendSafeMessage(`Successfully gathered ${gathered} ${target}.`);
  } else {
    await sendSafeMessage(
      `Only gathered ${gathered} out of ${amount} ${target}.`
    );
  }
}
// ---------------Gather----------------

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
        cancelCurrentTask = false;
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
        } else if (type === "gather") {
          const target = intent.target || "wood";
          const amount = parseInt(intent.amount) || 1;
          gatherTarget(target, amount);
        } else if (type === "stop") {
          cancelCurrentTask = true;
          bot.chat("Stopping current task.");
          bot.pathfinder.setGoal(null);
          bot.clearControlStates();
        } else if (type === "give") {
          const itemName = intent.target || "dirt";
          const amount = parseInt(intent.amount) || 1;
          const player = bot.players[username]?.entity;

          if (!player) {
            await sendSafeMessage("I can't see you nearby.");
            return;
          }

          const item = bot.inventory.items().find((i) => i.name === itemName);
          if (!item || item.count < amount) {
            await sendSafeMessage(
              `I don't have enough ${itemName} to give you.`
            );
            return;
          }
          await bot.pathfinder.goto(new goals.GoalFollow(player, 2));
          await bot.lookAt(player.position.offset(0, 1.5, 0));
          bot.toss(item.type, null, amount, (err) => {
            if (err) {
              bot.chat("Couldn't toss the item.");
            } else {
              bot.chat(`Here you go! ${amount} ${itemName}`);
            }
          });
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
  if (awaitingLocate)
    if (msg.includes("at [")) {
      sendSafeMessage(msg);
    } else if (msg.toLowerCase().includes("could not find")) {
      sendSafeMessage(
        "Couldn't find that location. Try another structure, biome, or POI."
      );
    }
  awaitingLocate = false;
});
// ---------------Chat----------------
