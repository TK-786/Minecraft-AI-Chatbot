from llama_index.core import Document
import requests

MINECRAFT_API_URL = "https://minecraft-api.vercel.app/api"

def fetch_all_items():
    """Fetches all Minecraft items and caches the response."""
    response = requests.get(f"{MINECRAFT_API_URL}/items")
    
    if response.status_code == 200:
        items = response.json()
        return [
            Document(
                text=(
                    f"Item: {item['name']}\n"
                    f"Stack Size: {item.get('stackSize', 'Unknown')}\n"
                    f"Image: {item.get('image', 'N/A')}"
                ),
                metadata={"name": item["name"]}
            )
            for item in items
        ]
    return []

def fetch_all_blocks():
    """Fetches all Minecraft blocks and caches the response, including luminance and transparency."""
    response = requests.get(
        f"{MINECRAFT_API_URL}/blocks",
        params={"fields": ["name", "image", "blastResistance", "flammable", "tool", "luminance", "transparent"]}
    )

    if response.status_code == 200:
        blocks = response.json()
        return [
            Document(
                text=(
                    f"Block: {block['name']}\n"
                    f"Blast Resistance: {block.get('blastResistance', 'Unknown')}\n"
                    f"Flammable: {str(block.get('flammable', False)).lower()}\n"
                    f"Tool: {block.get('tool', None)}\n"
                    f"Luminance: {block.get('luminance', '0')}\n"
                    f"Transparent: {str(block.get('transparent', False)).lower()}"
                ),
                metadata={"name": block["name"]}
            )
            for block in blocks
        ]
    return []

def fetch_all_recipes():
    """Fetches all craftable Minecraft recipes and caches the response."""
    response = requests.get(f"{MINECRAFT_API_URL}/crafting-recipes")

    if response.status_code == 200:
        recipes = response.json()
        formatted_recipes = []

        for recipe in recipes:
            item_name = recipe["item"]
            quantity = recipe.get("quantity", 1)
            shapeless = recipe.get("shapeless", False)
            crafting_grid = recipe.get("recipe", [])

            # Skip invalid shapeless recipes for known shaped items
            if item_name in {
                "Diamond Sword", "Golden Sword", "Iron Sword", "Netherite Sword", "Stone Sword", "Wooden Sword", 
                "Diamond Axe", "Golden Axe", "Iron Axe", "Netherite Axe", "Stone Axe", "Wooden Axe", 
                "Diamond Pickaxe", "Golden Pickaxe", "Iron Pickaxe", "Netherite Pickaxe", "Stone Pickaxe", "Wooden Pickaxe",
                "Diamond Shovel", "Golden Shovel", "Iron Shovel", "Netherite Shovel", "Stone Shovel", "Wooden Shovel",
                "Diamond Hoe", "Golden Hoe", "Iron Hoe", "Netherite Hoe", "Stone Hoe", "Wooden Hoe",
            } and shapeless:
                continue  

            grid_positions = [
                "Top-Left", "Top-Center", "Top-Right",
                "Middle-Left", "Middle-Center", "Middle-Right",
                "Bottom-Left", "Bottom-Center", "Bottom-Right"
            ]

            crafting_steps = [
                f"{grid_positions[i]}: {ingredient if ingredient else 'Empty'}"
                for i, ingredient in enumerate(crafting_grid)
            ]
            crafting_steps_text = "\n".join(crafting_steps)

            formatted_text = (
                f"Recipe: {item_name}\n"
                f"Quantity: {quantity}\n"
                f"Shapeless: {'True' if shapeless else 'False'}\n"
                f"Crafting Steps:\n{crafting_steps_text}"
            )

            formatted_recipes.append(Document(text=formatted_text, metadata={"name": item_name}))

        return formatted_recipes
    return []

def format_item_name(user_input: str):
    """Formats the item name to match API capitalization rules."""
    exceptions = {"with", "on", "a", "of", "and"}
    words = user_input.lower().split()
    
    formatted_words = [
        word.capitalize() if word not in exceptions or i == 0 else word
        for i, word in enumerate(words)
    ]
    return " ".join(formatted_words)

def get_item_info(item_name: str):
    """Fetches Minecraft item information."""
    formatted_name = format_item_name(item_name)
    items = fetch_all_items()
    
    for item in items:
        if item.metadata["name"] == formatted_name:
            return item.text
    return "Item not found."

def get_block_info(block_name: str):
    """Fetches Minecraft block information."""
    formatted_name = format_item_name(block_name)
    blocks = fetch_all_blocks()
    
    for block in blocks:
        if block.metadata["name"] == formatted_name:
            return block.text
    return "Block not found."

def get_recipes(item_name: str):
    """Fetches Minecraft crafting recipes for a specific item."""
    formatted_name = format_item_name(item_name)
    recipes = fetch_all_recipes()
    
    relevant_recipes = [recipe.text for recipe in recipes if recipe.metadata["name"] == formatted_name]
    
    if relevant_recipes:
        return "\n\n".join(relevant_recipes)
    return "Recipe not found."

### TESTING ##
if __name__ == "__main__":
    # print(get_item_info("Light") + "\n")
    # print(get_block_info("Cobblestone") + "\n")
    print(get_recipes("Diamond Sword") + "\n")

    # print(fetch_all_items()[:3])   # Print first 3 items
    # print(fetch_all_blocks()[:3])  # Print first 3 blocks
    # print(fetch_all_recipes()[:3]) # Print first 3 recipes
