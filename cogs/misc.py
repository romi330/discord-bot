import discord
from discord import app_commands
from discord.ext import commands
from main import version


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "commands"], hidden=True)
    @commands.cooldown(1,5)
    async def help(self, ctx):
        await ctx.send("This bot only uses slash commands, please try using `/help` instead.")

    @app_commands.command(description="Paul changelog and information.")
    @app_commands.checks.cooldown(1, 2)
    async def paul(self, interaction: discord.Interaction):
        msg = discord.Embed(title=f"Paul Changelog and Info.", color=discord.Colour.blurple())
        msg.add_field(name=f"Version {version} | Fourth Release",
                      value="",
                      inline=False)
        msg.add_field(name="What's changed?",
                      value="**-** New Help Command!\n"
                            "**-** You can use it to give you more information about all the commands that we offer.\n")
        msg.add_field(name="What's fixed?",
                      value="**-** Bug Squashing. :bug:\n"
                            "**-** Finally out of beta! <a:lil_swag:1353785503539007640>\n", inline=True)
        msg.add_field(name="Thank you for using Paul!",
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
    await bot.add_cog(Misc(bot))
