"""Main discord file for bot startup."""
import discord
import secret
import os

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

class MyClient(discord.Client):
    """Discord client main class."""
    async def on_ready(self):
        """When the client is ready, do this."""
        print(f"Logged in as {self.user}.")
        print("ready")

for filename in os.listdir("cogs"):
    print(filename)

client = MyClient()
client.run(secret.TOKEN)
