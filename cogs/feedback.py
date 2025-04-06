from discord import ui, Embed, Colour, Interaction, TextStyle
from discord import app_commands
from discord.ui import TextInput
from discord.ext import commands
import discord
from main import LOG_CHANNEL

class FeedbackModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Submit Feedback")

        self.title_field = TextInput(
            label='Title',
            placeholder='Briefly describe your feedback',
            style=TextStyle.short,
            max_length=30,
            required=True
        )
        self.category_field = TextInput(
            label='Category',
            placeholder='Category of your feedback',
            style=TextStyle.short,
            max_length=30,
            required=True
        )
        self.details_field = TextInput(
            label='Details',
            placeholder='Describe your feedback in detail',
            style=TextStyle.paragraph,
            max_length=1000,
            required=True
        )

        self.add_item(self.title_field)
        self.add_item(self.category_field)
        self.add_item(self.details_field)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f'Thanks for your feedback, {interaction.user.name}!', ephemeral=True
        )

        channel = LOG_CHANNEL if isinstance(LOG_CHANNEL, discord.TextChannel) else interaction.client.get_channel(
            LOG_CHANNEL)
        if channel:
            embed = Embed(title="New Feedback Received", color=Colour.dark_blue())
            embed.add_field(name="Title", value=self.title_field.value, inline=False)
            embed.add_field(name="Category", value=self.category_field.value, inline=False)
            embed.add_field(name="Details", value=self.details_field.value, inline=False)
            embed.set_author(name=interaction.user.name,
                             icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

            await channel.send(embed=embed)


class Feedback(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Submit feedback")
    @app_commands.checks.cooldown(2, 240)
    async def feedback(self, interaction: discord.Interaction):
        modal = FeedbackModal()
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot):
    await bot.add_cog(Feedback(bot))
