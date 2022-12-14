import disnake
from disnake.ext import commands
import json

with open("./embed_content.json", "r") as embed_content:
    ec = json.load(embed_content)['latency']

class Latency(commands.Cog):
    """Class that sends latency information."""
    
    def __init__(self, bot):
        """Sets bot object."""
        self.bot = bot

    @commands.slash_command(name="latency", description="Get bot latency.")
    @commands.default_member_permissions(manage_guild=True)
    async def latency(self, inter: disnake.ApplicationCommandInteraction):
        """
            Get's the bot latency.
            Admin command.
        """
        latency = self.bot.latency
        latency = round(latency * 1000, 2)

        embed = disnake.Embed(
            title=f"{ec['title'].format(latency=latency)}",
            color=disnake.Colour.blurple()
        )
        await inter.response.send_message(embed=embed, ephemeral=True)
        print(f"{ec['title'].format(latency=latency)}")
        
def setup(bot):
    """Register the cog."""
    bot.add_cog(Latency(bot))