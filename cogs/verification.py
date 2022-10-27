import disnake
from disnake.ext import commands

class Verification(commands.Cog):
    """Give 'Online' role to members who have accepted the pre-screen rules."""
    def __init__(self, bot):
        """Set bot object."""
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_member_update(before, after):
        """
            Called when member status changes.
            Check whether the member is pending member verification in bool.
            If member is pending = 1, otherwise 0.

            member - the member in question
            guild - to use the get role function
            role - to give member the role object
        """
        member = after
        guild = after.guild
        is_pending = after.pending # check if member has pending verification

        if not is_pending:
            # if not pending give the 'online' role
            role = guild.get_role(861049651012435998)
            await member.add_roles(
                role, 
                reason="Member verified.", 
                atomic=True)
            print(f"Verification: {member} given 'online' role.")
        return

def setup(bot):
    """Register the cog."""
    bot.add_cog(Verification(bot))