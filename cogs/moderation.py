import datetime
import discord
from discord import app_commands
from discord.ext import commands

def guild_only():
    async def predicate(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(":x: This command can only be used in a server.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

def bot_has_permissions(**perms):
    async def predicate(interaction: discord.Interaction):
        missing_perms = [perm.replace("_", " ").title() for perm, value in perms.items() if not getattr(interaction.guild.me.guild_permissions, perm, False)]
        if missing_perms:
            await interaction.response.send_message(
                f"<:what_in_the_hell:1353784539264192583> I am missing the following permission(s): `{', '.join(missing_perms)}`.",
                ephemeral=True
            )
            return False
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
        await member.kick(reason=f"Kicked by {interaction.user.name}")
        await interaction.response.send_message(f"Kicked `{member.display_name}` - `{member.id}`.", ephemeral=True)

    @app_commands.command(description="Ban a user. (ban_members)")
    @app_commands.default_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    @guild_only()
    async def ban(self, interaction: discord.Interaction, member: discord.Member):
        await member.ban(reason=f"Banned by {interaction.user.name}")
        await interaction.response.send_message(f"Banned `{member.display_name}` - `{member.id}`.", ephemeral=True)

    @app_commands.command(description="Purge messages from a channel. (manage_messages)")
    @app_commands.default_permissions(manage_messages=True)
    @bot_has_permissions(manage_messages=True)
    @guild_only()
    async def purge(self, interaction: discord.Interaction, amount: int):
        if not (1 <= amount <= 500):
            await interaction.response.send_message(":x: You must purge between 1 and 500 messages.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"Successfully purged `{len(deleted)}` messages.", ephemeral=True)

    @app_commands.command(description="Times out a user. (moderate_members)")
    @app_commands.default_permissions(moderate_members=True)
    @bot_has_permissions(moderate_members=True)
    @guild_only()
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, seconds: int = 0,
                      minutes: int = 0, hours: int = 0, days: int = 0, reason: str = None):
        duration = datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        await member.timeout(duration, reason=reason)
        await interaction.response.send_message(f'{member.mention} was timed out for {duration}.', ephemeral=True)

    @app_commands.command(description="Announces a message in a channel. (manage_channels)")
    @app_commands.default_permissions(manage_channels=True)
    @bot_has_permissions(manage_channels=True)
    @guild_only()
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str,
                       role: discord.Role = None):
        embed = discord.Embed(title=message, color=discord.Color.blurple())
        embed.set_footer(text=f"This announcement was made by {interaction.user.name}.")
        if role:
            mention = "@everyone" if role.name.lower() == "@everyone" else f"<@&{role.id}>"
            await channel.send(mention, embed=embed)
        else:
            await channel.send(embed=embed)
        await interaction.response.send_message(f"Announced `{message}` in {channel}.", ephemeral=True)

    @app_commands.command(description="Locks a channel. (manage_roles)")
    @app_commands.default_permissions(manage_roles=True)
    @bot_has_permissions(manage_roles=True)
    @guild_only()
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message(f"{channel.mention} was locked.", ephemeral=True)
        await interaction.channel.send("This channel was just locked! :lock:")

    @app_commands.command(description="Unlocks a channel. (manage_roles)")
    @app_commands.default_permissions(manage_roles=True)
    @bot_has_permissions(manage_roles=True)
    @guild_only()
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message(f"{channel.mention} was unlocked.", ephemeral=True)
        await interaction.channel.send("This channel was just unlocked! :unlock:")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
