import json
import os
import discord
from discord import ui, Embed, Colour, TextStyle, Interaction
from discord.ext import commands
from discord import app_commands

CONFIG_FILE = "modmail.json"

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump({}, file, indent=4)


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as load_config_file:
        try:
            return json.load(load_config_file)
        except json.JSONDecodeError:
            return {}


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as save_config_file:
            json.dump(config, save_config_file, indent=4)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Failed to save configuration: {e}")


class ModmailModal(ui.Modal):
    def __init__(self, bot: commands.Bot):
        super().__init__(title="Modmail")
        self.bot = bot

        self.message = ui.TextInput(
            label="Your message:",
            placeholder="Describe your issue or concern...",
            style=TextStyle.paragraph,
            max_length=500,
        )
        self.add_item(self.message)

    async def on_submit(self, interaction: Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        config = load_config()
        guild_id = str(interaction.guild.id)
        log_channel_id = config.get(guild_id)

        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = Embed(
                    title="New Modmail!",
                    description=self.message.value,
                    color=Colour.blurple(),
                ).set_author(
                    name=interaction.user.name,
                    icon_url=(
                        interaction.user.avatar.url if interaction.user.avatar else None
                    ),
                )

                await log_channel.send(embed=embed)

                await interaction.response.send_message(
                    "Your message will be sent to the moderators. Thank you for reaching out!",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "Modmail system is not properly configured. Please contact an administrator.",
                    ephemeral=True,
                )
        else:
            await interaction.response.send_message(
                "Modmail system has not been set up for this server. Please contact an administrator.",
                ephemeral=True,
            )


class ChannelSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot, guild: discord.Guild, page: int):
        self.bot = bot
        self.guild = guild
        self.page = page
        self.channels_per_page = 25

        start = page * self.channels_per_page
        end = start + self.channels_per_page
        channels = guild.text_channels[start:end]

        options = [
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in channels
        ]

        if not options:
            options = [discord.SelectOption(label="No channels available", value="none")]

        super().__init__(placeholder="Select a channel...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message(
                "No channels available to select.", ephemeral=True
            )
            return

        channel_id = int(self.values[0])
        config = load_config()
        config[str(interaction.guild.id)] = channel_id
        save_config(config)

        channel = self.guild.get_channel(channel_id)
        await interaction.response.send_message(
            f"Modmail log channel has been set to {channel.mention}.", ephemeral=True
        )


class ChannelSelectView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild = guild
        self.page = 0
        self.update_view()

    def update_view(self):
        self.clear_items()
        self.add_item(ChannelSelect(self.bot, self.guild, self.page))

        if len(self.guild.text_channels) > 25:
            if self.page > 0:
                self.add_item(self.PreviousPageButton(self))
            if (self.page + 1) * 25 < len(self.guild.text_channels):
                self.add_item(self.NextPageButton(self))

    class PreviousPageButton(discord.ui.Button):
        def __init__(self, parent_view):
            super().__init__(label="Previous", style=discord.ButtonStyle.blurple)
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            self.parent_view.page -= 1
            self.parent_view.update_view()
            await interaction.response.edit_message(view=self.parent_view)

    class NextPageButton(discord.ui.Button):
        def __init__(self, parent_view):
            super().__init__(label="Next", style=discord.ButtonStyle.blurple)
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            self.parent_view.page += 1
            self.parent_view.update_view()
            await interaction.response.edit_message(view=self.parent_view)


class Modmail(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setmodmail", description="Set the modmail log channel"
    )
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def setmodmail(self, interaction: discord.Interaction):
        view = ChannelSelectView(self.bot, interaction.guild)
        await interaction.response.send_message(
            "Select a channel for modmail using the dropdown below.", view=view, ephemeral=True
        )

    @app_commands.command(name="modmail", description="Send a modmail message")
    @app_commands.checks.cooldown(2, 240)
    async def modmail(self, interaction: discord.Interaction):
        modal = ModmailModal(self.bot)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot):
    await bot.add_cog(Modmail(bot))
