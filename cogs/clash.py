import os
from asyncio import Lock
import discord
import requests
from discord import app_commands, ui
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

COC_API_KEY = os.getenv("COC_API_KEY")

HEADERS = {"Authorization": f"Bearer {COC_API_KEY}", "Accept": "application/json"}

BASE_URL = "https://api.clashofclans.com/v1"


def get_player_info(player_tag):
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


def get_clan_warlog(clan_tag):
    url = f"{BASE_URL}/clans/%23{clan_tag.strip('#')}/warlog"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None


def get_clan_members(clan_tag):
    url = f"{BASE_URL}/clans/%23{clan_tag.strip('#')}/members"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None


class ClashMenuView(ui.View):
    def __init__(self, bot, author: discord.User):
        super().__init__(timeout=60)
        self.bot = bot
        self.author = author
        self.command_in_progress = False
        self.lock = Lock()

    async def disable_all_buttons(self):
        for child in self.children:
            if isinstance(child, ui.Button):
                child.disabled = True

    async def ensure_author(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "❌ You are not allowed to use this menu.", ephemeral=True
            )
            return False
        return True

    @ui.button(label="Player Info", style=discord.ButtonStyle.primary, emoji="👑")
    async def player_info(self, interaction: discord.Interaction, _: ui.Button):
        if not await self.ensure_author(interaction):
            return

        if self.command_in_progress:
            await interaction.response.send_message(
                "❌ A command is already in progress. Please wait or cancel it.",
                ephemeral=True,
            )
            return

        self.command_in_progress = True
        await interaction.response.send_message(
            "Please provide the player tag (e.g., #PLAYER_TAG):", ephemeral=True
        )

        def check(message):
            return (
                message.author == interaction.user
                and message.channel == interaction.channel
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if not self.command_in_progress:
                return

            player_tag = msg.content.strip()
            player_data = get_player_info(player_tag)

            if not player_data:
                await interaction.followup.send(
                    "❌ Invalid player tag or API error. Please try again.",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title=f"👤 Player: {player_data['name']}",
                description=f"**Tag:** `{player_data['tag']}`",
                color=discord.Color.blue(),
            )
            embed.add_field(name="🏆 Level", value=player_data["expLevel"], inline=True)
            embed.add_field(
                name="🏠 Town Hall", value=player_data["townHallLevel"], inline=True
            )
            embed.add_field(
                name="🥇 Trophies", value=player_data["trophies"], inline=True
            )
            embed.add_field(
                name="🏰 Clan",
                value=(
                    player_data["clan"]["name"] if "clan" in player_data else "No Clan"
                ),
                inline=False,
            )
            embed.set_thumbnail(
                url=(
                    player_data["clan"]["badgeUrls"]["medium"]
                    if "clan" in player_data
                    else None
                )
            )
            await interaction.followup.send(embed=embed)

        except TimeoutError:
            if self.command_in_progress:
                await interaction.followup.send(
                    "⏳ You took too long to respond.", ephemeral=True
                )
        finally:
            self.command_in_progress = False

    @ui.button(label="Clan Info", style=discord.ButtonStyle.primary, emoji="🏰")
    async def clan_info(self, interaction: discord.Interaction, _: ui.Button):
        if not await self.ensure_author(interaction):
            return

        if self.command_in_progress:
            await interaction.response.send_message(
                "❌ A command is already in progress. Please wait or cancel it.",
                ephemeral=True,
            )
            return

        self.command_in_progress = True
        await interaction.response.send_message(
            "Please provide the clan tag (e.g., #CLAN_TAG):", ephemeral=True
        )

        def check(message):
            return (
                message.author == interaction.user
                and message.channel == interaction.channel
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            clan_tag = msg.content.strip()
            clan_data = get_clan_info(clan_tag)

            if not clan_data:
                await interaction.followup.send(
                    "❌ Invalid clan tag or API error. Please try again.",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title=f"🏰 Clan: {clan_data['name']}",
                description=f"**Tag:** `{clan_data['tag']}`",
                color=discord.Color.green(),
            )
            embed.set_thumbnail(url=clan_data["badgeUrls"]["medium"])
            embed.add_field(
                name="📈 Clan Level", value=clan_data["clanLevel"], inline=True
            )
            embed.add_field(
                name="⭐ Clan Points", value=clan_data["clanPoints"], inline=True
            )
            embed.add_field(
                name="👥 Members", value=f"{clan_data['members']}/50", inline=True
            )
            embed.add_field(name="⚔️ War Wins", value=clan_data["warWins"], inline=True)
            embed.add_field(
                name="🏆 War League",
                value=(
                    clan_data["warLeague"]["name"]
                    if "warLeague" in clan_data
                    else "N/A"
                ),
                inline=True,
            )
            embed.add_field(
                name="🌍 Location",
                value=(
                    clan_data["location"]["name"]
                    if "location" in clan_data
                    else "Unknown"
                ),
                inline=True,
            )
            await interaction.followup.send(embed=embed)

        except TimeoutError:
            await interaction.followup.send(
                "⏳ You took too long to respond.", ephemeral=True
            )
        finally:
            self.command_in_progress = False

    @ui.button(label="War Info", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def war_info(self, interaction: discord.Interaction, _: ui.Button):
        if not await self.ensure_author(interaction):
            return

        if self.command_in_progress:
            await interaction.response.send_message(
                "❌ A command is already in progress. Please wait or cancel it.",
                ephemeral=True,
            )
            return

        self.command_in_progress = True
        await interaction.response.send_message(
            "Please provide the clan tag (e.g., #CLAN_TAG):", ephemeral=True
        )

        def check(message):
            return (
                message.author == interaction.user
                and message.channel == interaction.channel
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            clan_tag = msg.content.strip()
            warlog_data = get_clan_warlog(clan_tag)

            if not warlog_data or "items" not in warlog_data:
                await interaction.followup.send(
                    "❌ No war log available or invalid clan tag. Please try again.",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title="⚔️ Clan War Log",
                description=f"**War log for clan tag:** `{clan_tag}`",
                color=discord.Color.orange(),
            )
            for war in warlog_data["items"][:5]:
                opponent_name = war.get("opponent", {}).get("name", "Unknown Opponent")
                result = war.get("result", "Unknown Result")
                clan_stars = war.get("clan", {}).get("stars", "N/A")
                opponent_stars = war.get("opponent", {}).get("stars", "N/A")

                embed.add_field(
                    name=f"⚔️ War vs {opponent_name}",
                    value=f"**Result:** {result}\n**Stars:** {clan_stars} - {opponent_stars}",
                    inline=False,
                )
            await interaction.followup.send(embed=embed)

        except TimeoutError:
            await interaction.followup.send(
                "⏳ You took too long to respond.", ephemeral=True
            )
        finally:
            self.command_in_progress = False

    @ui.button(label="Cancel", style=discord.ButtonStyle.gray, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, _: ui.Button):
        if not await self.ensure_author(interaction):
            return

        async with self.lock:
            if not self.command_in_progress:
                await interaction.response.send_message(
                    "❌ No command is currently in progress.", ephemeral=True
                )
                return

            self.command_in_progress = False
            await self.disable_all_buttons()
            await interaction.response.edit_message(
                content="✅ All commands have been canceled.", view=self
            )

    async def on_timeout(self):
        await self.disable_all_buttons()


class Clash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description="Clash of Clans features menu")
    async def clash(self, interaction: discord.Interaction):
        view = ClashMenuView(self.bot, interaction.user)
        embed = discord.Embed(
            title="⚔️ Clash of Clans Features",
            description=(
                "Welcome to the Clash of Clans integration menu!\n\n"
                "**• Player Info**: Get detailed stats about a player.\n\n"
                "**• Clan Info**: View information about a clan.\n\n"
                "**• War Info**: Check the latest war logs.\n\n"
                "**• Cancel**: Cancel the current command and disable all buttons.\n\n"
            ),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Clash(bot))
