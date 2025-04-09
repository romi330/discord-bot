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

    @app_commands.command(description="Vote for the bot or check your vote status.")
    @app_commands.checks.cooldown(1, 30)
    async def vote(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        bot_id = self.bot.user.id
        vote_url = f"https://top.gg/bot/{bot_id}/vote"
        headers = {"Authorization": self.top_gg_api_token}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://top.gg/api/bots/{bot_id}/check?userId={user_id}",
                headers=headers,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    has_voted = data.get("voted", 0)
                    if has_voted:
                        embed = discord.Embed(
                            title="Thank you for voting! 🎉",
                            description=f"Your vote has been recorded, {interaction.user.mention}!",
                            color=discord.Color.green(),
                        )
                        embed.set_footer(text="Your support helps the bot grow!")
                    else:
                        embed = discord.Embed(
                            title="You Haven't Voted Yet!",
                            description=f"{interaction.user.mention}, you can vote for the bot [here]({vote_url}).",
                            color=discord.Color.red(),
                        )
                        embed.set_footer(
                            text="Voting helps the bot grow and unlocks rewards!"
                        )
                else:
                    embed = discord.Embed(
                        title="Error Checking Vote Status",
                        description="Sorry, I couldn't check your vote status. Please try again later.",
                        color=discord.Color.orange(),
                    )
                    embed.set_footer(text=f"Error Code: {response.status}")

                await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Vote(bot))
