import datetime
import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import BotMissingPermissions

def guild_only():
    async def predicate(interaction: discord.Interaction):
        if not interaction.guild:
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> This command can only be used in a server.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print("guild_only check failed: Command used outside a guild.")
            return False
        return True
    return app_commands.check(predicate)

def bot_has_permissions(**perms):
    async def predicate(interaction: discord.Interaction):
        missing_perms = [
            perm.replace("_", " ").title()
            for perm, value in perms.items()
            if not getattr(interaction.guild.me.guild_permissions, perm, False)
        ]
        if missing_perms:
            raise BotMissingPermissions(missing_permissions=missing_perms)
        return True
    return app_commands.check(predicate)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Kick a user. (kick_members)")
    @app_commands.default_permissions(kick_members=True)
    @bot_has_permissions(kick_members=True)
    @guild_only()
    async def kick(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.kick(reason=f"Kicked by {interaction.user.name}")
            await interaction.response.send_message(f"Kicked `{member.display_name}` - `{member.id}`.", ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> I don't have permission to kick this user.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                description=f"<:what_in_the_hell:1353784539264192583> An error occurred: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(description="Ban a user. (ban_members)")
    @app_commands.default_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    @guild_only()
    async def ban(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.ban(reason=f"Banned by {interaction.user.name}")
            await interaction.response.send_message(f"Banned `{member.display_name}` - `{member.id}`.", ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> I don't have permission to ban this user.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                description=f"<:what_in_the_hell:1353784539264192583> An error occurred: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(description="Purge messages from a channel. (manage_messages)")
    @app_commands.default_permissions(manage_messages=True)
    @bot_has_permissions(manage_messages=True)
    @guild_only()
    async def purge(self, interaction: discord.Interaction, amount: int):
        if not 1 <= amount <= 500:
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> You must purge between 1 and 500 messages.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"Successfully purged `{len(deleted)}` messages.", ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                description=f"<:what_in_the_hell:1353784539264192583> An error occurred: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    @app_commands.command(description="Times out a user. (moderate_members)")
    @app_commands.default_permissions(moderate_members=True)
    @bot_has_permissions(moderate_members=True)
    @guild_only()
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, seconds: int = 0,
                      minutes: int = 0, hours: int = 0, days: int = 0, reason: str = None):

        if not (seconds >= 0 and minutes >= 0 and hours >= 0 and days >= 0):
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> Invalid time duration.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        duration = datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        try:
            await member.timeout(duration, reason=reason)
            await interaction.response.send_message(f'{member.mention} was timed out for {duration}.', ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> I don't have permission to timeout this user.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                description=f"<:what_in_the_hell:1353784539264192583> An error occurred: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(description="Announces a message in a channel. (manage_channels)")
    @app_commands.default_permissions(manage_channels=True)
    @bot_has_permissions(manage_channels=True)
    @guild_only()
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str,
                       role: discord.Role = None):
        if not message.strip():
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> The announcement message cannot be empty.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            embed = discord.Embed(title=message, color=discord.Color.blurple())
            embed.set_footer(text=f"This announcement was made by {interaction.user.name}.")
            if role:
                mention = "@everyone" if role.name.lower() == "@everyone" else f"<@&{role.id}>"
                await channel.send(mention, embed=embed)
            else:
                await channel.send(embed=embed)
            await interaction.response.send_message(f"Announced `{message}` in {channel}.", ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> I don't have permission to announce in this channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                description=f"<:what_in_the_hell:1353784539264192583> An error occurred: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(description="Locks a channel. (manage_roles)")
    @app_commands.default_permissions(manage_roles=True)
    @bot_has_permissions(manage_roles=True)
    @guild_only()
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel):
        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=False)
            await interaction.response.send_message(f"{channel.mention} was locked.", ephemeral=True)
            await interaction.channel.send("This channel was just locked! :lock:")
        except discord.Forbidden:
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> I don't have permission to lock this channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                description=f"<:what_in_the_hell:1353784539264192583> An error occurred: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(description="Unlocks a channel. (manage_roles)")
    @app_commands.default_permissions(manage_roles=True)
    @bot_has_permissions(manage_roles=True)
    @guild_only()
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel):
        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=True)
            await interaction.response.send_message(f"{channel.mention} was unlocked.", ephemeral=True)
            await interaction.channel.send("This channel was just unlocked! :unlock:")
        except discord.Forbidden:
            embed = discord.Embed(
                description="<:what_in_the_hell:1353784539264192583> I don't have permission to unlock this channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                description=f"<:what_in_the_hell:1353784539264192583> An error occurred: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
