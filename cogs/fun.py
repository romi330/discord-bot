import json
import re
import discord
import requests
import os
from bs4 import BeautifulSoup as bs
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()

COC_API_KEY = os.getenv("COC_API_KEY")

HEADERS = {
        "Authorization": f"Bearer {COC_API_KEY}",
        "Accept": "application/json"
    }

BASE_URL = "https://api.clashofclans.com/v1"

def get_player_info(player_tag):
    if not player_tag or not isinstance(player_tag, str):
        raise ValueError("Invalid player tag provided.")
    url = f"{BASE_URL}/players/%23{player_tag.strip('#')}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None

def get_clan_info(clan_tag):
    url = f"{BASE_URL}/clans/%23{clan_tag.strip('#')}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Dad jokes!")
    @app_commands.checks.cooldown(1, 2)
    async def dadjoke(self, interaction: discord.Interaction):
        # Tells a dad joke.
        data = bs(requests.get("https://icanhazdadjoke.com/", timeout=10).text, "html.parser")
        data = str(data.select("p")[0])
        joke = re.findall('class="subtitle">.*</p>$', data)[0].replace('class="subtitle">', '').replace('</p>', '')

        await interaction.response.send_message(embed=discord.Embed(description=joke, color=discord.Colour.blurple()))

    @app_commands.command(description="Get your profile picture or someone else's.")
    @app_commands.checks.cooldown(1, 2)
    async def pfp(self, interaction: discord.Interaction, *, member: discord.User = None):
        # Gets the pfp of the member that you have selected, must be in your server.
        if member == self.bot.user:
            await interaction.response.send_message(":unamused:", ephemeral=True)
            return
        if member is None:
            member = interaction.user
        embed = discord.Embed(title=f"{member.display_name}'s Profile Picture", color=discord.Colour.blurple())
        embed.set_author(name=f"{interaction.user.display_name}")
        embed.set_image(url=member.avatar)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Get positive affirmations to help you get through your day")
    @app_commands.checks.cooldown(1, 5)
    async def affirmation(self, interaction: discord.Interaction):
        affirmation = json.loads(requests.get("https://www.affirmations.dev/", timeout=10).text)["affirmation"]
        await interaction.response.send_message(
            embed=discord.Embed(description=affirmation, color=discord.Colour.blurple()))

    @app_commands.command(description="Get your Clash of Clans player data")
    @app_commands.checks.cooldown(1, 5)
    async def player(self, interaction: discord.Interaction, tag: str):
        player_data = get_player_info(tag)
        if not player_data:
            await interaction.response.send_message("Invalid player tag or API error.")
            return

        embed = discord.Embed(title=f"Player: {player_data['name']}", color=discord.Color.blue())
        embed.add_field(name="Level", value=player_data["expLevel"])
        embed.add_field(name="Town Hall", value=player_data["townHallLevel"])
        embed.add_field(name="Trophies", value=player_data["trophies"])
        embed.add_field(name="Clan", value=player_data['clan']['name'] if 'clan' in player_data else "No Clan")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Get Clash of Clans clan data")
    @app_commands.checks.cooldown(1, 5)
    async def clan(self, interaction: discord.Interaction, tag: str):
        clan_data = get_clan_info(tag)
        if not clan_data:
            await interaction.response.send_message("Invalid clan tag or API error.")
            return

        embed = discord.Embed(title=f"Clan: {clan_data['name']}", color=discord.Color.green())
        embed.set_thumbnail(url=clan_data['badgeUrls']['medium'])
        embed.add_field(name="Clan Level", value=clan_data["clanLevel"])
        embed.add_field(name="Clan Points", value=clan_data["clanPoints"])
        embed.add_field(name="Members", value=f"{clan_data['members']}/50")
        embed.add_field(name="War Wins", value=clan_data["warWins"])
        embed.add_field(name="War League", value=clan_data["warLeague"]["name"] if "warLeague" in clan_data else "N/A")
        embed.add_field(name="Location", value=clan_data["location"]["name"] if "location" in clan_data else "Unknown")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
