# pylint: disable=unused-argument
import discord
from discord import app_commands
from discord.ext import commands


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.message = None

        self.add_item(discord.ui.Button(
            label="Invite Bot",
            style=discord.ButtonStyle.link,
            url="https://discord.com/oauth2/authorize?client_id=1249144690461118627"
        ))

    async def on_timeout(self):
        if self.message:
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

    async def send(self, interaction: discord.Interaction, embed: discord.Embed):
        await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
        self.message = await interaction.original_response()

    @discord.ui.button(label="General", style=discord.ButtonStyle.primary, emoji="📜")
    async def general_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📜 General Commands",
            description="Essential commands for everyone",
            color=0x3498db
        )
        embed.add_field(name="`/help`", value="Show this help menu", inline=False)
        embed.add_field(name="`/ping`", value="Check bot latency", inline=False)
        embed.add_field(name="`/test`", value="Check if the bot is working", inline=False)
        embed.add_field(name="`/invite`", value="Get the bot's invite link", inline=False)
        embed.add_field(name="`/paul`", value="View changelog and bot information", inline=False)
        embed.set_footer(text="Use / before each command • Page 1/5")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1249144690461118627/9a3afbbef2a17cd9b637e951a5277393.png")  # Replace with your bot's avatar URL
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Fun", style=discord.ButtonStyle.primary, emoji="🎉")
    async def fun_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎉 Fun Commands",
            description="Commands to keep your server entertained",
            color=0xe74c3c
        )
        embed.add_field(name="`/dadjoke`", value="Tells a random dad joke", inline=False)
        embed.add_field(name="`/pfp`", value="Get your or someone else's profile picture", inline=False)
        embed.add_field(name="`/affirmation`", value="Get a positive affirmation", inline=False)
        embed.add_field(name="`/player`", value="Get your Clash of Clans player data", inline=False)
        embed.add_field(name="`/clan`", value="Get Clash of Clans clan data", inline=False)
        embed.add_field(name="`/feedback`", value="Give feedback to the developer", inline=False)
        embed.set_footer(text="Use / before each command • Page 2/5")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1249144690461118627/9a3afbbef2a17cd9b637e951a5277393.png")  # Replace with your bot's avatar URL
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Moderation", style=discord.ButtonStyle.primary, emoji="⚖️")
    async def moderation_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚖️ Moderation Commands",
            description="Keep your server safe and organized",
            color=0x9b59b6
        )
        embed.add_field(name="`/kick`", value="Kick a user from the server", inline=False)
        embed.add_field(name="`/ban`", value="Ban a user from the server", inline=False)
        embed.add_field(name="`/purge`", value="Purge messages in a channel", inline=False)
        embed.add_field(name="`/timeout`", value="Timeout a user for a set duration", inline=False)
        embed.add_field(name="`/announce`", value="Announce a message in a channel", inline=False)
        embed.add_field(name="`/lock`", value="Lock a channel", inline=False)
        embed.add_field(name="`/unlock`", value="Unlock a channel", inline=False)
        embed.set_footer(text="Use / before each command • Page 3/5")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1249144690461118627/9a3afbbef2a17cd9b637e951a5277393.png")  # Replace with your bot's avatar URL
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="AutoMod", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def automoderation_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛡️ AutoMod Setup Guide",
            description="Automatically moderate your server with powerful tools",
            color=0x2ecc71
        )

        features = [
            ("🚫 Blocked Words", "Block specific words that will be automatically deleted"),
            ("🔗 Link Blocker", "Prevent links from being posted in chat"),
            ("🔄 Spam Detection", "Detect and prevent message spam based on similarity and frequency"),
            ("🤐 Profanity Filter", "Censor offensive language in messages"),
            ("😀 Emoji Spam Detection", "Limit the number of emojis in messages"),
            ("🌊 Flood Control", "Prevent rapid consecutive messages from users")
        ]

        for i, (name, value) in enumerate(features, 1):
            embed.add_field(name=f"{i}. {name}", value=value, inline=False)

        embed.add_field(
            name="Setup Instructions",
            value="Use `/automod` to configure these features!",
            inline=False
        )

        embed.set_footer(text="Use / before each command • Page 4/5")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1249144690461118627/9a3afbbef2a17cd9b637e951a5277393.png")  # Replace with your bot's avatar URL
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="ModMail", style=discord.ButtonStyle.primary, emoji="📩")
    async def modmail_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📩 ModMail System",
            description="Contact server moderators privately with your concerns",
            color=0x1abc9c
        )
        embed.add_field(
            name="How to use ModMail:",
            value="Use the `/modmail` command to open a private conversation with the moderators.",
            inline=False
        )
        embed.add_field(
            name="When to use ModMail:",
            value="• Report rule violations\n• Ask for help with server features\n• Request role assignments\n• Discuss private concerns\n• Appeal moderation decisions",
            inline=False
        )
        embed.add_field(
            name="For server owners:",
            value="Set up ModMail with the `/setmodmail` command to specify where messages are sent.",
            inline=False
        )
        embed.add_field(
            name="Cooldown:",
            value="To prevent spam, there's a cooldown between messages.",
            inline=False
        )
        embed.set_footer(text="Use / before each command • Page 5/5")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1249144690461118627/9a3afbbef2a17cd9b637e951a5277393.png")

        await interaction.response.edit_message(embed=embed, view=self)



class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Get information about the bot and available commands.")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📚 Paul Bot Help Center",
            description="**Welcome to the help center!**\nClick the buttons below to explore commands and features.",
            color=0x3498db
        )

        embed.add_field(name="Getting Started", value="This bot offers moderation, fun commands, and automod features.", inline=False)
        embed.add_field(name="Need more help?", value="Join our [support server](https://discord.gg/8hYZUtUxme) for assistance.", inline=False)
        embed.set_footer(text="Use / before each command • More features coming soon!")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1249144690461118627/9a3afbbef2a17cd9b637e951a5277393.png")

        view = HelpView()
        await view.send(interaction, embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
