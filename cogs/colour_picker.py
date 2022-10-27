from tokenize import String
from discord import MessageInteraction
import disnake
from disnake.ext import commands
from db_connect import create_connection as cc
import secret

class ColourPicker(commands.Cog):
    """Enable members to pick their own Discord profile colour."""
    def __init__(self, bot):
        """Set bot object."""
        self.bot = bot
    
    @commands.slash_command(
        name="colour_picker",
        description="Sends colour picker to channel.")
    @commands.default_member_permissions(manage_guild=True)
    async def send_colour_picker(self, inter: disnake.ApplicationCommandInteraction):
        """
            Sends a colour picker to a specified channel enabling members to 
            pick their colour using the select menu.

            Stores component_id (selection menu id) into database to be
            retrieved when/if bot restarts.
        """
        guild_id = inter.guild.id
        channel = inter.channel

        # get select menu class
        view = DropdownView()

        # get message component_id from the sent 
        message = await channel.send(content="Choose your profile colour:", view=view)
        component_id = message.components[0].children[0].custom_id

        # connect to database and check if message component_id is already stored
        conn = cc(secret.COLOUR_PICKER_DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM colour_picker WHERE guild_id=?", (guild_id,))
        rows = cur.fetchall()

        if not rows:
            # component_id not stored
            # connect to database and insert message component_id
            sql = ''' INSERT INTO colour_picker(guild_id, component_id)
                    VALUES(?,?) '''
            cur = conn.cursor()
            values = (guild_id, component_id)
            cur.execute(sql, values)
            conn.commit()
        else:
            # component_id previously stored
            # connect to database and update message component_id with latest
            sql = f''' UPDATE colour_picker SET component_id = ?
                WHERE guild_id = ? '''
            cur = conn.cursor()
            values = (component_id, guild_id)
            cur.execute(sql, values)
            conn.commit()
        
        print(f"Colour_picker: New picker has been setup at: guild_id {guild_id}, component_id: {component_id}")
        
    @commands.Cog.listener()
    async def on_dropdown(self, inter: MessageInteraction):
        """
            Called when the dropdown menu is selected.
            If the dropdown component_id is in the colour_picker database,
            then call the change_role() function.
        """
        try:
            guild_id = inter.guild_id
            component_id = inter.component.custom_id
            # get member's selection option
            component_values = inter.values[0]

            conn = cc(secret.COLOUR_PICKER_DB)
            cur = conn.cursor()
            cur.execute("SELECT component_id FROM colour_picker WHERE guild_id=?", (guild_id,))
            rows = cur.fetchall()
            
            if rows:
                if rows[0][0] == (component_id):
                    await self.change_role(inter, component_values)
            return
        except disnake.errors.InteractionResponded:
            pass

    async def change_role(self, inter: MessageInteraction, role_colour: String):
        """
            Adds a role-based colour to a member upon selection.
            Removes other role_based colour before adding a new one.
        """
        guild = inter.guild
        member = inter.user
        
        colour_roles = {
            'yellow': 1035226461096910930,
            'orange': 1035226684028362802,
            'brown': 1035226867449462805,
            'red': 1035227104838684772,
            'green': 1035227213777350666,
            'blue': 1035227350096412773,
            'purple': 1035227746911146035,
            'pink': 1035227578895712287
        }
        # check and remove member colour roles they have before
        for role in member.roles:
            role_name = role.name.lower()
            try:
                role_to_remove = colour_roles[role_name]
                if role_to_remove:
                    await member.remove_roles(
                        role,
                        reason="Remove to change colour.",
                        atomic=True
                    )
            except KeyError:
                continue

        # get colour role
        role = guild.get_role(colour_roles[f"{role_colour.lower()}"])
        # give colour role to member
        await member.add_roles(
            role, 
            reason="Add to change colour.", 
            atomic=True
        )
        
        # send ephemeral message to member that colour has been changed.
        embed = disnake.Embed(
            title=f"Your colour has been changed to {role_colour.lower()}.",
            color=disnake.Colour.blurple()
        )
        await inter.response.send_message(embed=embed, ephemeral=True)
        print(f"Colour_picker: {member} has changed profile colour to: {role_colour.lower()}")


def setup(bot):
    """Register the cog."""
    bot.add_cog(ColourPicker(bot))


# Defines a custom Select containing colour options that the user can choose.
# The callback function of this class is called when the user changes their choice.
class Dropdown(disnake.ui.Select):
    def __init__(self):
        # Define the options that will be presented inside the dropdown
        options = [
            disnake.SelectOption(
                label="Yellow", description="Change my profile colour to yellow.", emoji="🟨"
            ),
            disnake.SelectOption(
                label="Orange", description="Change my profile colour to orange.", emoji="🟧"
            ),
            disnake.SelectOption(
                label="Brown", description="Change my profile colour to brown.", emoji="🟫"
            ),
            disnake.SelectOption(
                label="Red", description="Change my profile colour to red.", emoji="🟥"
            ),
            disnake.SelectOption(
                label="Green", description="Change my profile colour to green.", emoji="🟩"
            ),
            disnake.SelectOption(
                label="Blue", description="Change my profile colour to blue.", emoji="🟦"
            ),
            disnake.SelectOption(
                label="Purple", description="Change my profile colour to purple.", emoji="🟪"
            ),
            disnake.SelectOption(
                label="Pink", description="Change my profile colour to pink.", emoji="🌸"
            ),
        ]

        # The placeholder is what will be shown when no option is chosen.
        # The min and max values indicate we can only pick one of the three options.
        # The options parameter defines the dropdown options, see above.
        super().__init__(
            placeholder="Select a colour",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The `self` object refers to the
        # Select object, and the `values` attribute gets a list of the user's
        # selected options. We only want the first one.
        await ColourPicker.change_role(self, inter, self.values[0])
        
        

class DropdownView(disnake.ui.View):
    def __init__(self):
        super().__init__()

        # Add the dropdown to our view object.
        self.add_item(Dropdown())