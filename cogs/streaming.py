import disnake
from disnake.ext import commands

class Streaming(commands.Cog):
    """
        Give 'live' role to streamer when streaming.
    """
    def __init__(self, bot):
        """Set bot object."""
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_presence_update(self, before: disnake.Member, after: disnake.Member):
        """
            Called when status of a member changes.
            Call give role function if member is streaming, otherwise ignore.
        """
        guild = before.guild
        member = after
        member_new_activity = str(member.activities).lower()

        live_role = guild.get_role(862116382955405312)

        if "streaming" in member_new_activity:
            # check if member already has role
            if live_role in member.roles:
                return
            # give member 'now live' role
            await member.add_roles(
                live_role, 
                reason="Streamer is live.", 
                atomic=True
            )
            print(f"Streaming: {member} is streaming, {live_role} role given.")
        elif ("streaming" not in member_new_activity):
            # check if member does not have a role.
            if live_role not in member.roles:
                return
            await member.remove_roles(
                live_role, 
                reason="Streamer is live.", 
                atomic=True
            )
            print(f"Streaming: {member} is no longer streaming, {live_role} role removed.")

def setup(bot):
    """Register the cog."""
    bot.add_cog(Streaming(bot))