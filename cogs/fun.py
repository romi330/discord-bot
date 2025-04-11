import json
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

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
