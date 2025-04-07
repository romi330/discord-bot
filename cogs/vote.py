import json
import os
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()
        self.top_gg_api_token = os.getenv("TOP_GG_API_TOKEN")
        self.leaderboard_file = "vote_leaderboard.json"
        self.vote_leaderboard = self.load_leaderboard()

    def load_leaderboard(self):
        try:
            with open(self.leaderboard_file, "r", encoding="utf-8") as load_file:
                return json.load(load_file)
        except FileNotFoundError:
            return {}

    def save_leaderboard(self):
        with open(self.leaderboard_file, "w", encoding="utf-8") as save_file:
            json.dump(self.vote_leaderboard, save_file)

    def update_leaderboard(self, user_id, username):
        if user_id in self.vote_leaderboard:
            self.vote_leaderboard[user_id]["votes"] += 1
        else:
            self.vote_leaderboard[user_id] = {"username": username, "votes": 1}
        self.save_leaderboard()

    @app_commands.command(description="Vote for me!")
    async def vote(self, interaction: discord.Interaction):
        bot_id = self.bot.user.id
        vote_url = f"https://top.gg/bot/{bot_id}/vote"
        embed = discord.Embed(
            title="Vote for the Bot!",
            description=f"Support the bot by voting on [top.gg]({vote_url}). Thank you!",
            color=discord.Color.dark_gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Check if you have voted for the bot.")
    async def check_vote(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        bot_id = self.bot.user.id
        headers = {"Authorization": self.top_gg_api_token}

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://top.gg/api/bots/{bot_id}/check?userId={user_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    has_voted = data.get("voted", 0)
                    if has_voted:
                        self.update_leaderboard(user_id, interaction.user.name)
                        await interaction.response.send_message(f"Thank you for voting, {interaction.user.mention}! 🎉 Your vote has been recorded.")
                    else:
                        await interaction.response.send_message(f"{interaction.user.mention}, you haven't voted yet. You can vote [here](https://top.gg/bot/{bot_id}/vote).")
                else:
                    await interaction.response.send_message("Sorry, I couldn't check your vote status. Please try again later.")

    @app_commands.command(description="View the top voters!")
    async def leaderboard(self, interaction: discord.Interaction):
        if not self.vote_leaderboard:
            await interaction.response.send_message("No votes have been recorded yet.")
            return

        sorted_leaderboard = sorted(self.vote_leaderboard.items(), key=lambda x: x[1]["votes"], reverse=True)
        leaderboard_text = "\n".join([f"{entry[1]['username']}: {entry[1]['votes']} votes" for entry in sorted_leaderboard[:10]])

        top_leader_id, top_leader_data = sorted_leaderboard[0]
        top_leader_username = top_leader_data["username"]

        top_leader = await self.bot.fetch_user(int(top_leader_id))
        top_leader_avatar_url = top_leader.avatar.url if top_leader.avatar else None

        embed = discord.Embed(
            title="Top Voters Leaderboard",
            description=leaderboard_text,
            color=discord.Color.gold()
        )
        embed.set_footer(text="Thank you for your support!")
        if top_leader_avatar_url:
            embed.set_thumbnail(url=top_leader_avatar_url)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Vote(bot))
