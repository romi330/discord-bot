import discord
from discord import app_commands
from discord.ext import commands
from main import version


class misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Paul changelog and information.")
    @app_commands.checks.cooldown(1, 2)
    async def paul(self, interaction: discord.Interaction):
        # Sends changelog and gives a bit of information about the bot.
        msg = discord.Embed(title=f"Paul Changelog and Info.", color=discord.Colour.blurple())
        msg.add_field(name=f"Version {version} | Third Release",
                      value="**-** **[BETA]** Paul. \n",
                      inline=False)
        msg.add_field(name="What's changed?",
                      value="**-** Introducing Automod!\n"
                            "**-** Automod is an administrator only command.\n"
                            "**-** You can create automod rules for your server.\n")
        msg.add_field(name="What's fixed?",
                      value="**-** Bug Squashing. :bug:\n", inline=True)
        msg.add_field(name="Thanks for using Paul!",
                      value="**-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-**\n"
                      "Credits: `wk_killer`.\n",
                      inline=False)

        await interaction.response.send_message(embed=msg, ephemeral=True)

    @app_commands.command(description="Test if the bot is working.")
    @app_commands.checks.cooldown(1, 2)
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("The bot is up and working properly!", ephemeral=True)

    @app_commands.command(description="What's my latency?")
    @app_commands.checks.cooldown(1, 2)
    async def ping(self, interaction: discord.Interaction):
        ping = round(self.bot.latency * 1000)
        len(self.bot.guilds)

        await interaction.response.send_message(f"Pong! `{ping}ms`", ephemeral=True)

    @app_commands.command(description="Invite me!")
    @app_commands.checks.cooldown(1, 2)
    async def invite(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://discord.com/oauth2/authorize?client_id=1249144690461118627",
                                                ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(misc(bot))
