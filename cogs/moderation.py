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


class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Kick a user. (kick_members)")
    @app_commands.default_permissions(kick_members=True)
    @guild_only()
    async def kick(self, interaction: discord.Interaction, member: discord.Member):
        # Kicks users using the bot.
        highest_role = 0
        for role in interaction.user.roles:
            if role.position > highest_role:
                highest_role = role.position

        if not interaction.user.id == 1249144690461118627 and not interaction.user.id == self.bot.user.id and not any(
                role.position > highest_role for role in member.roles):
            await member.kick(reason=f"Kicked by {interaction.user.name}")
            await interaction.response.send_message(f"Kicked `{member.display_name}` - `{member.id}`.", ephemeral=True)

    @app_commands.command(description="Ban a user. (ban_members)")
    @app_commands.default_permissions(ban_members=True)
    @guild_only()
    async def ban(self, interaction: discord.Interaction, member: discord.Member):
        # Bans users using the bot.
        highest_role = 0
        for role in interaction.user.roles:
            if role.position > highest_role:
                highest_role = role.position

        if not interaction.user.id == 1249144690461118627 and not interaction.user.id == self.bot.user.id and not any(
                role.position > highest_role for role in member.roles):
            await member.ban(reason=f"Banned by {interaction.user.name}")
            await interaction.response.send_message(f"Banned `{member.display_name}` - `{member.id}", ephemeral=True)

    @app_commands.command(description="Purges messages from a channel. (manage_messages).")
    @app_commands.default_permissions(manage_messages=True)
    @guild_only()
    async def purge(self, interaction: discord.Interaction, amount: int):
        # Ensures the amount is within the allowed range
        if not (1 <= amount <= 500):
            await interaction.response.send_message(
                f":x: You tried to purge {amount} messages, but it must be between **1 and 500**.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount)

        await interaction.followup.send(f"Successfully purged `{len(deleted)}` messages.", ephemeral=True)

    @app_commands.command(description="Times out a user. (timeout_members)")
    @app_commands.default_permissions(moderate_members=True)
    @guild_only()
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, seconds: int = 0,
                      minutes: int = 0,
                      hours: int = 0, days: int = 0, reason: str = None):
        # Times out users in your server.
        duration = datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        await member.timeout(duration, reason=reason)

        await interaction.response.send_message(f'{member.mention} was timed for {duration}', ephemeral=True)

    @app_commands.command(description="Announces a message in a channel. (manage_channels)")
    @app_commands.default_permissions(manage_channels=True)
    @guild_only()
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str,
                       role: discord.Role = None):
        # Announces a message to your server.
        embed = discord.Embed(title=f"{message}", color=discord.Color.blurple())
        embed.set_footer(text=f"This announcement was composed and made by {interaction.user.name}.")

        if role is not None:
            if role.name.lower() == '@everyone':
                await channel.send("@everyone", embed=embed)
                await interaction.response.send_message(f"Announced `{message}` in {channel} and mentioned @everyone.",
                                                    ephemeral=True)
            else:
                await channel.send(f"<@&{role.id}>", embed=embed)
                await interaction.response.send_message(f"Announced `{message}` in {channel} and mentioned @{role.name}.",
                                                    ephemeral=True)
        else:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"Announced `{message}` in {channel}.", ephemeral=True)

    @app_commands.command(description="Locks a channel. (manage_roles)")
    @app_commands.default_permissions(manage_roles=True)
    @guild_only()
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # Locks a channel in your server.
        await interaction.channel.set_permissions(target=interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message(f"{channel.mention} was locked.", ephemeral=True)
        await interaction.channel.send("This channel was just locked! :lock:")

    @app_commands.command(description="Unlocks a channel. (manage_roles)")
    @app_commands.default_permissions(manage_roles=True)
    @guild_only()
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # Unlocks a channel in your server.
        await interaction.channel.set_permissions(target=interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message(f"{channel.mention} was unlocked.", ephemeral=True)
        await interaction.channel.send("This channel was just unlocked! :unlock:")


async def setup(bot):
    await bot.add_cog(moderation(bot))
