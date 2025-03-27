import discord
from discord import app_commands, ui, Embed
from discord.ext import commands
import json
import os
import re
from collections import defaultdict
import asyncio
from better_profanity import profanity


class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.json_file = "automod_rules.json"

        self.user_messages = defaultdict(list)
        self.recent_messages = defaultdict(list)

        profanity.load_censor_words()

        self.load_rules()

    def load_rules(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as file:
                self.rules = json.load(file)
        else:
            self.rules = {}

    def save_rules(self):
        with open(self.json_file, "w") as file:
            json.dump(self.rules, file, indent=4)

    @app_commands.command(name="automod", description="Manage AutoMod settings (blocked words, links, etc.).")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def automod_settings(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        rules = self.rules.get(guild_id, {})

        view = AutoModView(self, guild_id, rules)
        await interaction.response.send_message(
            "Click a button to manage AutoMod rules:",
            view=view,
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        guild_id = str(message.guild.id)
        rules = self.rules.get(guild_id, {})

        if rules.get("blocked_words", False):
            blocked_words = rules.get("blocked_words", [])
            if any(word.lower() in message.content.lower() for word in blocked_words):
                await self.delete_message(message, "blocked word")
                return

        if rules.get("blocked_links", False):
            if self.contains_link(message.content):
                await self.delete_message(message, "blocked link")
                return

        if rules.get("profanity_filter", False):
            if self.contains_profanity(message.content):
                await self.delete_message(message, "profanity")
                return

        if rules.get("spam_detection", False):
            if await self.is_spam(message):
                await self.delete_message(message, "spam")
                return

        if rules.get("emoji_spam_detection", False):
            if self.contains_emoji_spam(message.content):
                await self.delete_message(message, "emoji spam")
                return

        if rules.get("flood_control", False):
            if await self.is_flood(message):
                await self.delete_message(message, "flood")
                return

    async def delete_message(self, message: discord.Message, reason: str):
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, your message was deleted due to {reason}.",
                delete_after=5
            )
        except discord.errors.NotFound:
            pass
        except discord.errors.Forbidden:
            pass

    def contains_link(self, content: str):
        link_pattern = r'https?://\S+|www\.\S+'
        return bool(re.search(link_pattern, content))

    def contains_profanity(self, content: str):
        return profanity.contains_profanity(content)

    def contains_emoji_spam(self, content: str):
        custom_emojis = re.findall(r'<a?:\w+:\d+>', content)
        unicode_emojis = re.findall(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content)

        total_emojis = custom_emojis + unicode_emojis
        return len(total_emojis) > 5

    async def is_spam(self, message: discord.Message):
        guild_id = message.guild.id
        user_id = message.author.id
        current_time = message.created_at

        self.user_messages[guild_id].append({
            'content': message.content,
            'timestamp': current_time
        })

        self.user_messages[guild_id] = [
            msg for msg in self.user_messages[guild_id]
            if (current_time - msg['timestamp']).total_seconds() < 10
        ]

        if len(self.user_messages[guild_id]) > 4:
            return True

        similar_messages = [
            msg for msg in self.user_messages[guild_id]
            if self.messages_similar(msg['content'], message.content)
        ]

        return len(similar_messages) > 2

    def messages_similar(self, msg1: str, msg2: str, threshold: float = 0.8):
        msg1 = re.sub(r'[^\w\s]', '', msg1.lower())
        msg2 = re.sub(r'[^\w\s]', '', msg2.lower())

        words1 = msg1.split()
        words2 = msg2.split()

        total_words = max(len(words1), len(words2))
        matching_words = sum(1 for word in words1 if word in words2)

        return matching_words / total_words >= threshold

    async def is_flood(self, message: discord.Message):
        guild_id = message.guild.id
        channel_id = message.channel.id
        current_time = message.created_at

        self.recent_messages[guild_id].append({
            'channel': channel_id,
            'timestamp': current_time
        })

        self.recent_messages[guild_id] = [
            msg for msg in self.recent_messages[guild_id]
            if (current_time - msg['timestamp']).total_seconds() < 5
        ]

        channel_messages = [
            msg for msg in self.recent_messages[guild_id]
            if msg.get('channel') == channel_id
        ]

        return len(channel_messages) > 4


class AutoModView(ui.View):
    def __init__(self, cog, guild_id, rules):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.rules = rules

        self.update_button_states()

    def update_button_states(self):
        button_configs = [
            (self.toggle_link_blocker, "blocked_links", "Link Blocker"),
            (self.toggle_spam_detection, "spam_detection", "Spam Detection"),
            (self.toggle_profanity_filter, "profanity_filter", "Profanity Filter"),
            (self.toggle_emoji_spam_detection, "emoji_spam_detection", "Emoji Spam Detection"),
            (self.toggle_flood_control, "flood_control", "Flood Control")
        ]

        for button, rule_key, label in button_configs:
            current_value = self.rules.get(rule_key, False)
            button.style = discord.ButtonStyle.green if current_value else discord.ButtonStyle.red
            button.label = f"{label} ({'Enabled' if current_value else 'Disabled'})"

    async def toggle_rule(self, interaction: discord.Interaction, rule_name: str, current_value: bool, label: str,
                          button: ui.Button):
        new_value = not current_value
        self.rules[rule_name] = new_value
        self.cog.rules.setdefault(self.guild_id, {})[rule_name] = new_value
        self.cog.save_rules()

        button.style = discord.ButtonStyle.green if new_value else discord.ButtonStyle.red
        button.label = f"{label} ({'Enabled' if new_value else 'Disabled'})"

        await interaction.response.edit_message(view=self)

        status = "enabled" if new_value else "disabled"
        await interaction.followup.send(f"{label} has been {status}.", ephemeral=True)

    @ui.button(label="View Blocked Words", style=discord.ButtonStyle.blurple)
    async def view_blocked_words(self, interaction: discord.Interaction, button: ui.Button):
        blocked_words = self.rules.get("blocked_words", [])
        blocked_words_str = ", ".join(blocked_words) or "No blocked words set."
        await interaction.response.send_message(f"Blocked words: `{blocked_words_str}`", ephemeral=True)

    @ui.button(label="Add Blocked Word", style=discord.ButtonStyle.green)
    async def add_blocked_word(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Please reply with the word you want to block.", ephemeral=True)

        try:
            word_msg = await self.cog.bot.wait_for(
                "message",
                check=lambda m: m.author == interaction.user and m.channel == interaction.channel,
                timeout=30.0
            )
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out. Please try again.", ephemeral=True)
            return

        word_to_add = word_msg.content.lower()
        blocked_words = self.rules.setdefault("blocked_words", [])

        if word_to_add not in blocked_words:
            blocked_words.append(word_to_add)
            self.cog.save_rules()
            await interaction.followup.send(f"Blocked word `{word_to_add}` has been added.", ephemeral=True)
        else:
            await interaction.followup.send(f"Word `{word_to_add}` is already blocked.", ephemeral=True)

    @ui.button(label="Remove Blocked Word", style=discord.ButtonStyle.red)
    async def remove_blocked_word(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Please reply with the word you want to remove.", ephemeral=True)

        try:
            word_msg = await self.cog.bot.wait_for(
                "message",
                check=lambda m: m.author == interaction.user and m.channel == interaction.channel,
                timeout=30.0
            )
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out. Please try again.", ephemeral=True)
            return

        word_to_remove = word_msg.content.lower()
        blocked_words = self.rules.get("blocked_words", [])

        if word_to_remove in blocked_words:
            blocked_words.remove(word_to_remove)
            self.cog.save_rules()
            await interaction.followup.send(f"Blocked word `{word_to_remove}` has been removed.", ephemeral=True)
        else:
            await interaction.followup.send(f"Word `{word_to_remove}` is not in the blocked words list.",
                                            ephemeral=True)

    @ui.button(label="Link Blocker (Disabled)", style=discord.ButtonStyle.red)
    async def toggle_link_blocker(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "blocked_links", self.rules.get("blocked_links", False), "Link Blocker", button)

    @ui.button(label="Spam Detection (Disabled)", style=discord.ButtonStyle.red)
    async def toggle_spam_detection(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "spam_detection", self.rules.get("spam_detection", False), "Spam Detection", button)

    @ui.button(label="Profanity Filter (Disabled)", style=discord.ButtonStyle.red)
    async def toggle_profanity_filter(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "profanity_filter", self.rules.get("profanity_filter", False), "Profanity Filter", button)

    @ui.button(label="Emoji Spam Detection (Disabled)", style=discord.ButtonStyle.red)
    async def toggle_emoji_spam_detection(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "emoji_spam_detection", self.rules.get("emoji_spam_detection", False), "Emoji Spam Detection", button)

    @ui.button(label="Flood Control (Disabled)", style=discord.ButtonStyle.red)
    async def toggle_flood_control(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "flood_control", self.rules.get("flood_control", False), "Flood Control", button)

    @ui.button(label="List AutoMod Features", style=discord.ButtonStyle.blurple)
    async def list_automod_features(self, interaction: discord.Interaction, button: ui.Button):
        features = {
            "Link Blocker": "blocked_links",
            "Spam Detection": "spam_detection",
            "Profanity Filter": "profanity_filter",
            "Emoji Spam Detection": "emoji_spam_detection",
            "Flood Control": "flood_control"
        }

        embed = Embed(
            title="🛡 Server AutoMod Feature Status",
            description=f"AutoMod features for {interaction.guild.name}",
            color=discord.Color.blue()
        )

        for feature_name, rule_key in features.items():
            status = "✅ Enabled" if self.rules.get(rule_key, False) else "❌ Disabled"
            embed.add_field(name=feature_name, value=status, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))