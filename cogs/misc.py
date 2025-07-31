import discord
from discord import app_commands
from discord.ext import commands
from main import VERSION


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "commands"], hidden=True)
    @commands.cooldown(1, 5)
    async def help(self, ctx):
        await ctx.send(
            "This bot only uses slash commands, please try using `/help` instead."
        )

    @app_commands.command(description="Paul changelog and information.")
    @app_commands.checks.cooldown(1, 2)
    async def paul(self, interaction: discord.Interaction):
        msg = discord.Embed(
            title="Changelog and Information", color=discord.Colour.blurple()
        )
        msg.add_field(name=f"Version {VERSION} | Ninth Release", value="", inline=False)
        msg.add_field(
            name="What's changed?",
            value=(
                "**•** Enhanced vote command with proper interaction handling.\n"
                "**•** Improved error handling for Discord API interactions.\n"
                "**•** Optimized response deferrals to prevent timeouts.\n"
                "**•** Updated command reliability and user experience.\n"
            ),
            inline=True,
        )
        msg.add_field(
            name="What's fixed?",
            value=(
                "**•** Fixed 'Unknown interaction' errors in vote command.\n"
                "**•** Resolved interaction timeout issues.\n"
                "**•** Improved API response handling.\n"
                "**•** Enhanced error messages for better debugging.\n"
            ),
            inline=True,
        )
        msg.add_field(
            name="What's new?",
            value=(
                "**•** Added `/giveaway` command with reaction-based participation.\n"
                "**•** Support for multiple winners in giveaways.\n"
                "**•** Automatic winner selection with random picking.\n"
                "**•** Enhanced user info and server info commands.\n"
                "**•** Improved embed formatting across all commands.\n"
            ),
            inline=False,
        )
        msg.set_footer(
            text="Made with ❤️ by Ronen Lazowski • Open-source forever",
            icon_url="https://cdn.discordapp.com/avatars/1357038796532875406/9c8bc91959694cbcfa7b746e80400e1f.png",
        )

        await interaction.response.send_message(embed=msg, ephemeral=True)

    @app_commands.command(description="Test if the bot is working.")
    @app_commands.checks.cooldown(1, 2)
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "The bot is up and working properly!", ephemeral=True
        )

    @app_commands.command(description="What's my latency?")
    @app_commands.checks.cooldown(1, 2)
    async def ping(self, interaction: discord.Interaction):
        ping = round(self.bot.latency * 1000)
        len(self.bot.guilds)

        await interaction.response.send_message(f"Pong! `{ping}ms`", ephemeral=True)

    @app_commands.command(description="Invite me!")
    @app_commands.checks.cooldown(1, 2)
    async def invite(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "https://discord.com/oauth2/authorize?client_id=1249144690461118627",
            ephemeral=True,
        )

    @app_commands.command(description="Join the support server.")
    @app_commands.checks.cooldown(1, 2)
    async def support(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "https://discord.gg/8hYZUtUxme", ephemeral=True
        )

    @app_commands.command(description="View the bot's source code.")
    @app_commands.checks.cooldown(1, 2)
    async def source(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Paul - Discord Bot",
            description="Paul is an open-source, multipurpose Discord bot built for performance, automation, and community interaction.\n\n"
            "Explore the source code, contribute, or fork your own version!",
            url="https://github.com/ronenlazowski/paul",
            color=discord.Color.from_rgb(36, 41, 46),
        )
        embed.set_thumbnail(url="https://www.ronenlaz.com/images/github-mark-white.png")
        embed.add_field(
            name="📂 Repository",
            value="[ronenlazowski/paul](https://github.com/ronenlazowski/paul)",
            inline=False,
        )
        embed.add_field(name="🛠️ Language", value="Python 3.13.x 🐍", inline=True)
        embed.add_field(
            name="📜 License",
            value="[GPL-3.0 License](https://github.com/ronenlazowski/paul/blob/main/LICENSE) 🧾",
            inline=True,
        )
        embed.add_field(
            name="🚀 Features",
            value="• AutoMod with Discord API\n"
            "• Customizable server settings\n"
            "• Modmail support\n"
            "• JSON-based configuration system\n"
            "• Built to scale with large systems",
            inline=False,
        )
        embed.set_footer(text="Made with ❤️ by Ronen Lazowski • Open-source forever")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Misc(bot))
