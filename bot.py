import discord, hashlib, hmac, binascii, os
from discord import app_commands

TOKEN = os.getenv("BOT_TOKEN")

class MinefieldBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.tree.sync()  # Sync commands to Discord
        print("Slash commands synced.")

bot = MinefieldBot()

def secure_random(seed: str, random_seed: str):
    hash_hex = hmac.new(
        binascii.unhexlify(seed), 
        random_seed.encode(), 
        hashlib.sha256
    ).hexdigest()
    hash_int = int(hash_hex, 16)
    if hash_int < 0:
        hash_int = -hash_int
    
    def next_int(min_val, max_val):
        if max_val <= 0:
            raise ValueError("Bound must be positive")
        return min_val + (hash_int % (max_val - min_val))
    
    return next_int

def get_mine_locations(client_seed: str, server_seed: str, nonce: str, mines: int):
    minefield = ["BOMB"] * mines + ["ROBUX"] * (25 - mines)
    random_seed = f"{client_seed}-{nonce}-0"
    rng = secure_random(server_seed, random_seed)
    rng_idx = 0
    
    for i in range(len(minefield) - 1, 0, -1):
        index = rng(0, i + 1)
        rng_idx += 1
        random_seed = f"{client_seed}-{nonce}-{rng_idx}"
        rng = secure_random(server_seed, random_seed)
        
        minefield[i], minefield[index] = minefield[index], minefield[i]
    
    return ["💣" if val == "BOMB" else "💎" for val in minefield]

@bot.tree.command(name="predict_mine_positions", description="Generate a 5x5 minefield grid")
@app_commands.describe(
    client_seed="Enter the client seed",
    server_seed="Enter the server seed (hashed)",
    nonce="Enter the nonce value",
    mines_count="Number of mines between 1 and 24"
)
async def mines(interaction: discord.Interaction, client_seed: str, server_seed: str, nonce: str, mines_count: int):
    try:
        gridArray = get_mine_locations(client_seed, server_seed, nonce, mines_count)
        grid = [gridArray[i:i+5] for i in range(0, 25, 5)]
        gridString = "\n".join(grid)
        await interaction.response.send_message(grid)
    except Exception as e:
        await interaction.response.send_message(f"Prediction failed: {e}", ephemeral=True)

bot.run(TOKEN)