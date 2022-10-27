"""Main discord file for bot startup."""
import disnake
from disnake.ext import commands
import secret
import os

intents = disnake.Intents.default()
intents.members = True
intents.messages = True
intents.presences = True

bot = commands.InteractionBot(
    intents=intents, 
    test_guilds=[860934544693919744], 
    sync_commands_debug=True)

@bot.event
async def on_ready():
    print("Bot is ready.")

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        file = filename[:-3]
        bot.load_extension(f"cogs.{file}")
        print(f"Loaded cog: {file}")

bot.run(secret.TOKEN)
