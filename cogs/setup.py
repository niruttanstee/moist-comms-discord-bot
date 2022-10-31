import disnake
from disnake.ext import commands
from db_connect import create_connection as cc
import json
import secret

with open("./embed_content.json", "r") as embed_content:
    ec = json.load(embed_content)['setup']

# feature num: [feature name, requires setup, setup command]
current_features = {
    0: ["0️⃣ **RNG**", False]
}

class Setup(commands.Cog):
    """Sets up the bot to customise enabling of cogs."""
    
    def __init__(self, bot):
        """Sets bot object."""
        self.bot = bot

    @commands.slash_command(name="setup", 
        description="Setup Remus bot.")
    @commands.default_member_permissions(manage_channels=True)
    async def setup(self, inter: disnake.ApplicationCommandInteraction):
        """
            Called when user uses /setup 
            Sends information about setup as an embed with a reaction for 
            the member to react to proceed to the setup phase.

            Inserts guild_id, member_id, message_id, step to database
        """
        guild_id = inter.guild.id
        member_id = inter.user.id

        # (0) Send pre-setup message with time to complete.
        embed_0 = disnake.Embed(
            title=f"{ec['embed_0']['title']}",
            description=f"{ec['embed_0']['description'].format(eta_time=5)}",
            colour=disnake.Colour.blurple(),
        )
        embed_0.add_field(
            name=f"{ec['embed_0']['field_1']['name']}", 
            value=f"{ec['embed_0']['field_1']['value']}", 
            inline=False)
        embed_0.add_field(
            name=f"{ec['embed_0']['field_2']['name']}",
            value=f"{ec['embed_0']['field_2']['value']}", 
            inline=False)
        embed_0.set_thumbnail(url=f"{ec['embed_1']['thumbnail']}")
        embed_0.set_footer(text="Remus - by Ooowey")

        await inter.response.send_message(embed=embed_0)
        # get message object from sent message
        message = await inter.original_response()
        await message.add_reaction("✅")
        
        # get message id and store in database for reaction listener
        # delete message id previously stored from database
        message_id = message.id

        conn = cc(secret.REMUS_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM setup_listener WHERE guild_id=?", (guild_id,))

        # insert guild_id and message_id to setup_listener database
        # to allow listener events to be filtered
        sql = ''' INSERT INTO setup_listener(guild_id, member_id, message_id, step)
        VALUES(?,?,?,?) '''
        values = (guild_id, member_id, message_id, 0)
        cur.execute(sql, values)
        conn.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: disnake.RawReactionActionEvent):
        """
            Calls when a reaction is added in a guild.
            This specific functions handles all interactive reaction for
            the setup embed.

            Checks the reaction:

            If its a bot, return. Otherwise proceeds to check reaction payload 
            information.

            If the member that reacted is not the same as in the database,
            return, otherwise continue.
            
            If the message_id is the same as in the database, get the step
            information.

            The step is the setup stage of either (1,2,3) as an int. 
            The step decides the correct function to be called for the specific
            stage of the setup process.
        """
        member = payload.member
        emote = payload.emoji.name
        
        guild_id = payload.guild_id
        channel_id = payload.channel_id
        member_id = member.id
        message_id = payload.message_id
        
        if member.bot:
            return
        
        # check member_id and message_id from database to match
        conn = cc(secret.REMUS_DB)
        cur = conn.cursor()
        cur.execute("""SELECT step FROM setup_listener 
            WHERE member_id=? AND message_id=?""", (member_id, message_id,))
        rows = cur.fetchall()

        if not rows:
            return

        # message is a setup reaction
        # get message object to edit embed upon updating progress
        guild: disnake.Guild = await self.bot.fetch_guild(guild_id)
        channel: disnake.TextChannel  = await guild.fetch_channel(channel_id)
        message: disnake.Message = await channel.fetch_message(message_id)

        if rows[0][0] == 0:
            if emote == "✅":
                # remove emojis before calling next embed.
                await message.clear_reactions()
                await self.setup_step_1(guild, message)
            
        elif rows[0][0] == 1:
            if emote == "0️⃣": # feature 1: RNG
                # add feature to database from index based identifier 0, 1 etc
                sql = f''' UPDATE setup SET feature_0 = ?
                WHERE guild_id = ? '''
                cur = conn.cursor()
                values = (1, guild_id)
                cur.execute(sql, values)
                conn.commit()
            
            if emote == "✅": # continue to step 2
                await message.clear_reactions()
                await self.setup_step_2(guild, message)

        else: # step 2
            if emote == "❎": # go back to step 1 to select feature.
                await message.clear_reactions()
                await self.setup_step_1(guild, message)

            if emote == "✅": # continue to step 3
                await message.clear_reactions()
                await self.setup_step_3(guild, message)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: disnake.RawReactionActionEvent):
        """
            Calls when a member removes a reaction in the guild.
            This specific function handles the removal of features from the
            database as the member unreacts to feature reaction options. In
            step 3.

            If the reaction was done by a bot, return.

            If the reaction message_id and member_id is in the database
            continue, otherwise return.

            If the reaction contains the correct emote corresponding to the
            features to remove, set the feature in the database to 0. Otherwise
            return.
        """
        emote = payload.emoji.name

        guild_id = payload.guild_id
        member_id = payload.user_id
        message_id = payload.message_id

        # guild and member objects fetch
        guild: disnake.Guild = await self.bot.fetch_guild(guild_id)
        member: disnake.Member = await guild.fetch_member(member_id)
        
        if member.bot:
            return

        # check member_id and message_id from database to match, and get steps
        conn = cc(secret.REMUS_DB)
        cur = conn.cursor()
        cur.execute("""SELECT step FROM setup_listener 
            WHERE member_id=? AND message_id=?""", (member_id, message_id,))
        rows = cur.fetchall()

        if not rows:
            return

        # check the step is 1 (the selection of features stage)
        if rows[0][0] != 1:
            return

        # filter emote to update correct feature from database
        feature_identifier = ""

        if emote == "0️⃣": # RNG - feature 0
            feature_identifier = "feature_0"

        # add feature to database from index based identifier 0, 1 etc
        if feature_identifier:
            sql = f" UPDATE setup SET {feature_identifier} = ? WHERE guild_id = ? "
            cur = conn.cursor()
            values = (0, guild_id)
            cur.execute(sql, values)
            conn.commit()

            
    async def setup_step_1(self, guild: disnake.Guild, message: disnake.Message):
        """
            Called when member is in setup step 1; accepted the introduction
            information embed.

            Sends an embed to the member with all available features. 
            Reactions are added with the embed with each reaction unique to
            the corresponding features the member can add.

            By reacting, the member is enabling the features.
            By unreacting, the member is disabling the features.
            By reacting to the tick symbol, proceeds to step 2.
        """
        # remove and insert new guild_id and default features boolean
        conn = cc(secret.REMUS_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM setup WHERE guild_id=?", 
        (guild.id,))

        sql = ''' INSERT INTO setup(guild_id, feature_0) 
            VALUES (?,?) '''
        values = (guild.id, 0)
        cur.execute(sql, values)
        conn.commit()

        # update step in setup_listener database to 1
        sql = f''' UPDATE setup_listener SET step = ?
                WHERE message_id = ? '''
        cur = conn.cursor()
        values = (1, message.id)
        cur.execute(sql, values)
        conn.commit()

        # (1) Send embed message on available features
        embed_1 = disnake.Embed(
            title=f"{ec['embed_1']['title']}",
            description=f"{ec['embed_1']['description']}",
            colour=disnake.Colour.blurple(),
        )
        embed_1.add_field(
            name=f"{ec['embed_1']['field_1']['name']}", 
            value=f"{ec['embed_1']['field_1']['value']}", 
            inline=False)
        embed_1.add_field(
            name=f"{ec['embed_1']['field_end']['name']}",
            value=f"{ec['embed_1']['field_end']['value']}", 
            inline=False)
        embed_1.set_thumbnail(url=f"{ec['embed_1']['thumbnail']}")
        embed_1.set_footer(text="Remus - by Ooowey")
        await message.edit(embed=embed_1)
        
        # add reaction corresponding to the available features
        await message.add_reaction("0️⃣")
        await message.add_reaction("✅")
    
    async def setup_step_2(self, guild: disnake.Guild, message: disnake.Message):
        """
            Called when member is in setup step 2; reacted to the tick to
            confirm the features wanted.

            Sends embed to the member with all selected features fetched from
            database.

            React to cross to go back to step 1 to select features again.
            React to tick to proceed to step 3.
        """
        # update step in setup_listener database to 2
        conn = cc(secret.REMUS_DB)
        sql = f''' UPDATE setup_listener SET step = ?
                WHERE message_id = ? '''
        cur = conn.cursor()
        values = (2, message.id)
        cur.execute(sql, values)
        conn.commit()

        # fetch select features from setup database
        cur.execute("SELECT feature_0 FROM setup WHERE guild_id=?", (guild.id,))
        rows = cur.fetchall()

        selected_feature_list = []
        not_selected = False

        feature_count = 0
        for feature in rows[0]:
            if feature == 1: # if feature is enabled
                selected_feature_list.append(current_features[feature_count][0])
            feature_count+=1
        
        if not selected_feature_list:
            not_selected = True

        async def features_printer():
            """Prints formatted features list."""
            formatted_features = ""
            if not_selected:
                formatted_features = ec['embed_2']['field_1']['not_selected']
            else:
                for feature in selected_feature_list:
                    formatted_features = formatted_features + f"{feature}\n"
            return formatted_features

        # (2) Send embed message on selected features
        embed_name = ec['embed_2']['field_1']['name']
        embed_name = embed_name.format(selected_total=len(selected_feature_list))
        embed_value = await features_printer()

        embed_2 = disnake.Embed(
            title=f"{ec['embed_2']['title']}",
            description=f"{ec['embed_2']['description']}",
            colour=disnake.Colour.blurple(),
        )
        embed_2.add_field(
            name=f"{embed_name}", 
            value=f"{embed_value}", 
            inline=False)
        embed_2.set_thumbnail(url=f"{ec['embed_2']['thumbnail']}")
        embed_2.set_footer(text="Remus - by Ooowey")

        await message.edit(embed=embed_2)
        
        # add reaction corresponding to the available features
        # if member did not select a feature, only cross reaction is displayed.
        if not_selected:
            embed_2.add_field(
            name=f"{ec['embed_2']['field_end']['name']}", 
            value=f"{ec['embed_2']['field_end']['value_not_selected']}", 
            inline=False)
            await message.edit(embed=embed_2)
            await message.add_reaction("❎")
        else:
            embed_2.add_field(
            name=f"{ec['embed_2']['field_end']['name']}", 
            value=f"{ec['embed_2']['field_end']['value_selected']}", 
            inline=False)
            await message.edit(embed=embed_2)
            await message.add_reaction("❎")
            await message.add_reaction("✅")
    
    async def setup_step_3(self, guild: disnake.Guild, message: disnake.Message):
        """
            Called when member is in setup step 3; completion of setup and
            telling members of any further setup required by selected
            features.

            Sends embed to member with all selected features requiring setup.
        """
        # update step in setup_listener database to 3
        conn = cc(secret.REMUS_DB)
        sql = f''' UPDATE setup_listener SET step = ?
                WHERE message_id = ? '''
        cur = conn.cursor()
        values = (3, message.id)
        cur.execute(sql, values)
        conn.commit()

        # fetch select features from setup database
        cur.execute("SELECT feature_0 FROM setup WHERE guild_id=?", (guild.id,))
        rows = cur.fetchall()

        selected_feature_list = [] # stores all selected features
        feature_count = 0 # count of the number of features

        for feature in rows[0]:
            if feature == 1: # if feature is enabled
                selected_feature_list.append(current_features[feature_count])
            feature_count+=1

        async def features_printer():
            """Prints out features with required setup commands."""
            formatted_feature = ""

            for feature in selected_feature_list:
                if feature[1] == False:
                    formatted_feature = (formatted_feature + 
                        f"{feature[0]}\n``Does not require setup``")
                else:
                    formatted_feature = (formatted_feature +
                        f"{feature[0]}\n``Requires setup, use:`` ``{feature[2]}``")
            return formatted_feature

        # (3) Send embed message on selected features required to setup and completion
        selected_features = await features_printer()

        embed_3 = disnake.Embed(
            title=f"{ec['embed_3']['title']}",
            description=f"{ec['embed_3']['description']}",
            colour=disnake.Colour.blurple(),
        )
        embed_3.add_field(
            name=f"{ec['embed_3']['field_1']['name']}", 
            value=f"{selected_features}", 
            inline=False
        )
        embed_3.set_thumbnail(url=f"{ec['embed_2']['thumbnail']}")
        embed_3.set_footer(text="Remus - by Ooowey")
        await message.edit(embed=embed_3)

def setup(bot):
    """Register the cog."""
    bot.add_cog(Setup(bot))