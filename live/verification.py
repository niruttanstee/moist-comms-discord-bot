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
            Check whether the member has a pending member verification.
            If member is pending = 1, otherwise 0.

            is_pending = boolean
            member = the member in question
            guild = to use the get role function
            role = to give member the role object
        """
        member = after
        guild = after.guild
        is_pending = after.pending # check if member has pending verification

        if not is_pending:
            # check if member already has role            
            role = guild.get_role(861049651012435998)

            if role not in member.roles:
                # member does not have role, give role
                await member.add_roles(
                role, 
                reason="Member verified.", 
                atomic=True)
                print(f"Verification: Given 'online' role to {member}")

        return


def setup(bot):
    """Register the cog."""
    bot.add_cog(Verification(bot))