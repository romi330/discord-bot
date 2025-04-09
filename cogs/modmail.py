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


class Modmail(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setmodmail", description="Set the modmail log channel (manage_channels)"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def setmodmail(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        config = load_config()
        config[str(interaction.guild.id)] = channel.id
        save_config(config)
        await interaction.response.send_message(
            f"Modmail log channel set to {channel.mention}", ephemeral=True
        )

    @app_commands.command(name="modmail", description="Send a modmail message")
    @app_commands.checks.cooldown(2, 240)
    async def modmail(self, interaction: discord.Interaction):
        modal = ModmailModal(self.bot)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot):
    await bot.add_cog(Modmail(bot))
