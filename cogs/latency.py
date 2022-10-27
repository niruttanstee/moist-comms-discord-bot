import disnake
from disnake.ext import commands
import asyncio

class Latency(commands.Cog):
    """Class that sends latency information."""
    
    def __init__(self, bot):
        """Sets bot object."""
        self.bot = bot

    @commands.slash_command(name="latency", description="Get the bot latency.")
    @commands.has_permissions(administrator=True)           
    async def goodbye(self, inter: disnake.ApplicationCommandInteraction):

        latency = self.bot.latency
        latency = round(latency * 1000, 2)

        embed = disnake.Embed(
            title=f"Latency {latency}ms",
        )

        await inter.response.send_message(embed=embed)
        
        
def setup(bot):
    """Register the cog."""
    bot.add_cog(Latency(bot))