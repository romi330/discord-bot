import json
import datetime
import re
import discord
import requests
from bs4 import BeautifulSoup as bs
from discord import app_commands
from discord.ext import commands

class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Dad jokes!")
    @app_commands.checks.cooldown(1, 2)
    async def dadjoke(self, interaction: discord.Interaction):
        data = bs(
            requests.get("https://icanhazdadjoke.com/", timeout=10).text, "html.parser"
        )
        data = str(data.select("p")[0])
        joke = (
            re.findall('class="subtitle">.*</p>$', data)[0]
            .replace('class="subtitle">', "")
            .replace("</p>", "")
        )

        await interaction.response.send_message(
            embed=discord.Embed(description=joke, color=discord.Colour.blurple())
        )

    @app_commands.command(description="Get your profile picture or someone else's.")
    @app_commands.checks.cooldown(1, 2)
    async def pfp(
        self, interaction: discord.Interaction, *, member: discord.User = None
    ):
        if member == self.bot.user:
            await interaction.response.send_message(":unamused:", ephemeral=True)
            return
        if member is None:
            member = interaction.user
        embed = discord.Embed(
            title=f"{member.display_name}'s Profile Picture",
            color=discord.Colour.blurple(),
        )
        embed.set_author(name=f"{interaction.user.display_name}")
        embed.set_image(url=member.avatar)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        description="Get positive affirmations to help you get through your day"
    )
    @app_commands.checks.cooldown(1, 5)
    async def affirmation(self, interaction: discord.Interaction):
        affirmation = json.loads(
            requests.get("https://www.affirmations.dev/", timeout=10).text
        )["affirmation"]
        await interaction.response.send_message(
            embed=discord.Embed(description=affirmation, color=discord.Colour.blurple())
        )

    @app_commands.command(description="Get detailed information about a user.")
    @app_commands.checks.cooldown(1, 5)
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user

        roles = [role.mention for role in member.roles if role != interaction.guild.default_role]
        embed = discord.Embed(
            title=f"User Info - {member}",
            color=member.color,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=member.avatar)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Display Name", value=member.display_name, inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.add_field(name="Roles", value=", ".join(roles) if roles else "No roles", inline=False)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="Bot?", value="Yes" if member.bot else "No", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Get detailed information about the server.")
    @app_commands.checks.cooldown(1, 5)
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"Server Info - {guild.name}",
            color=discord.Colour.blurple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=guild.icon)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created On", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        embed.add_field(name="Verification Level", value=str(guild.verification_level).capitalize(), inline=True)
        embed.add_field(name="Features", value=", ".join(guild.features) if guild.features else "None", inline=False)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
