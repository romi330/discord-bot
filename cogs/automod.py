import json
import datetime
import time
import os
import re
from collections import defaultdict
from better_profanity import profanity
import discord
from discord import app_commands, ui, Embed
from discord.ext import commands


class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.json_file = "automod_rules.json"

        self.user_messages = defaultdict(lambda: defaultdict(list))
        self.recent_messages = defaultdict(lambda: defaultdict(list))

        self.last_cleanup = time.time()

        profanity.load_censor_words()

        self.load_rules()

    def load_rules(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r", encoding="utf-8") as file:
                self.rules = json.load(file)
        else:
            self.rules = {}

        default_thresholds = {
            "spam_messages": 5,
            "spam_seconds": 10,
            "flood_messages": 5,
            "flood_seconds": 5,
            "emoji_limit": 5
        }

        for _, guild_rules in self.rules.items():
            guild_rules.setdefault("thresholds", {})
            for key, value in default_thresholds.items():
                guild_rules["thresholds"].setdefault(key, value)

    def save_rules(self):
        with open(self.json_file, "w", encoding="utf-8") as file:
            json.dump(self.rules, file, indent=4)

    def cleanup_message_cache(self):
        current_time = time.time()
        if current_time - self.last_cleanup < 600:
            return

        self.last_cleanup = current_time

        for guild_id in list(self.user_messages.keys()):
            for user_id in list(self.user_messages[guild_id].keys()):
                self.user_messages[guild_id][user_id] = [
                    msg for msg in self.user_messages[guild_id][user_id]
                    if (datetime.datetime.now(datetime.timezone.utc) - msg['timestamp']).total_seconds() < 3600
                ]
                if not self.user_messages[guild_id][user_id]:
                    del self.user_messages[guild_id][user_id]
            if not self.user_messages[guild_id]:
                del self.user_messages[guild_id]

        for guild_id in list(self.recent_messages.keys()):
            for channel_id in list(self.recent_messages[guild_id].keys()):
                self.recent_messages[guild_id][channel_id] = [
                    msg for msg in self.recent_messages[guild_id][channel_id]
                    if (datetime.datetime.now(datetime.timezone.utc) - msg['timestamp']).total_seconds() < 3600
                ]
                if not self.recent_messages[guild_id][channel_id]:
                    del self.recent_messages[guild_id][channel_id]
            if not self.recent_messages[guild_id]:
                del self.recent_messages[guild_id]

    @app_commands.command(name="automod", description="Manage AutoMod settings (blocked words, links, etc.).")
    @app_commands.default_permissions(manage_messages=True)
    async def automod_settings(self, interaction: discord.Interaction):
        if not interaction.guild.me.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "⚠️ I don't have the 'Manage Messages' permission, which is required for AutoMod to function properly.",
                ephemeral=True
            )
            return

        guild_id = str(interaction.guild_id)
        rules = self.rules.get(guild_id, {})

        view = AutoModMainMenu(self, guild_id, rules)
        await interaction.response.send_message(
            "🛡️ **AutoMod Control Panel**\nSelect an option to configure:",
            view=view,
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        if not message.guild.me.guild_permissions.manage_messages:
            return

        self.cleanup_message_cache()

        guild_id = str(message.guild.id)
        rules = self.rules.get(guild_id, {})

        thresholds = rules.get("thresholds", {
            "spam_messages": 5,
            "spam_seconds": 10,
            "flood_messages": 5,
            "flood_seconds": 5,
            "emoji_limit": 5
        })

        if rules.get("blocked_words", False):
            blocked_words = rules.get("blocked_words_list", [])
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
            if await self.is_spam(message, thresholds["spam_messages"], thresholds["spam_seconds"]):
                await self.delete_message(message, "spam")
                return

        if rules.get("emoji_spam_detection", False):
            if self.contains_emoji_spam(message.content, thresholds["emoji_limit"]):
                await self.delete_message(message, "emoji spam")
                return

        if rules.get("flood_control", False):
            if await self.is_flood(message, thresholds["flood_messages"], thresholds["flood_seconds"]):
                await self.delete_message(message, "flood")
                return

    async def delete_message(self, message: discord.Message, reason: str):
        try:
            await message.delete()
            permissions = message.channel.permissions_for(message.guild.me)
            if permissions.send_messages:
                try:
                    await message.channel.send(
                        f"{message.author.mention}, your message was deleted due to {reason}.",
                        delete_after=5
                    )
                except discord.errors.HTTPException:
                    pass
        except discord.errors.NotFound:
            pass
        except discord.errors.Forbidden:
            pass

    def contains_link(self, content: str):
        link_pattern = r'https?://\S+|www\.\S+'
        return bool(re.search(link_pattern, content))

    def contains_profanity(self, content: str):
        return profanity.contains_profanity(content)

    def contains_emoji_spam(self, content: str, emoji_limit: int = 5):
        custom_emojis = re.findall(r'<a?:\w+:\d+>', content)
        unicode_emojis = re.findall(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content)

        total_emojis = custom_emojis + unicode_emojis
        return len(total_emojis) > emoji_limit

    async def is_spam(self, message: discord.Message, message_limit: int = 5, time_window: int = 10):
        guild_id = message.guild.id
        user_id = message.author.id
        current_time = message.created_at

        self.user_messages[guild_id][user_id].append({
            'content': message.content,
            'timestamp': current_time
        })

        self.user_messages[guild_id][user_id] = [
            msg for msg in self.user_messages[guild_id][user_id]
            if (current_time - msg['timestamp']).total_seconds() < time_window
        ]

        if len(self.user_messages[guild_id][user_id]) > message_limit:
            return True

        similar_messages = [
            msg for msg in self.user_messages[guild_id][user_id]
            if self.messages_similar(msg['content'], message.content)
        ]

        return len(similar_messages) > message_limit / 2

    def messages_similar(self, msg1: str, msg2: str, threshold: float = 0.8):
        if len(msg1) < 5 or len(msg2) < 5:
            return msg1 == msg2

        msg1 = re.sub(r'[^\w\s]', '', msg1.lower())
        msg2 = re.sub(r'[^\w\s]', '', msg2.lower())

        words1 = msg1.split()
        words2 = msg2.split()

        if not words1 or not words2:
            return False

        total_words = max(len(words1), len(words2))
        matching_words = sum(1 for word in words1 if word in words2)

        return matching_words / total_words >= threshold

    async def is_flood(self, message: discord.Message, message_limit: int = 5, time_window: int = 5):
        guild_id = message.guild.id
        channel_id = message.channel.id
        user_id = message.author.id
        current_time = message.created_at

        self.recent_messages[guild_id][channel_id].append({
            'user': user_id,
            'timestamp': current_time
        })

        self.recent_messages[guild_id][channel_id] = [
            msg for msg in self.recent_messages[guild_id][channel_id]
            if (current_time - msg['timestamp']).total_seconds() < time_window
        ]

        user_channel_messages = [
            msg for msg in self.recent_messages[guild_id][channel_id]
            if msg.get('user') == user_id
        ]

        return len(user_channel_messages) > message_limit

class AutoModMainMenu(ui.View):
    def __init__(self, cog, guild_id, rules):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild_id = guild_id
        self.rules = rules

    @ui.button(label="Feature Settings", style=discord.ButtonStyle.primary, emoji="⚙️")
    async def feature_settings(self, interaction: discord.Interaction, button: ui.Button):
        view = FeatureSettingsView(self.cog, self.guild_id, self.rules)
        await interaction.response.edit_message(
            content="🛡️ **AutoMod Feature Settings**\nToggle features on/off:",
            view=view
        )

    @ui.button(label="Word Filters", style=discord.ButtonStyle.primary, emoji="🔤")
    async def word_filters(self, interaction: discord.Interaction, button: ui.Button):
        view = WordFiltersView(self.cog, self.guild_id, self.rules)
        await interaction.response.edit_message(
            content="🔤 **AutoMod Word Filters**\nManage blocked words:",
            view=view
        )

    @ui.button(label="Threshold Settings", style=discord.ButtonStyle.primary, emoji="📊")
    async def threshold_settings(self, interaction: discord.Interaction, button: ui.Button):
        view = ThresholdSettingsView(self.cog, self.guild_id, self.rules)
        await interaction.response.edit_message(
            content="📊 **AutoMod Threshold Settings**\nConfigure detection thresholds:",
            view=view
        )

    @ui.button(label="View Status", style=discord.ButtonStyle.success, emoji="📋")
    async def view_status(self, interaction: discord.Interaction, button: ui.Button):
        features = {
            "Link Blocker": "blocked_links",
            "Spam Detection": "spam_detection",
            "Profanity Filter": "profanity_filter",
            "Emoji Spam Detection": "emoji_spam_detection",
            "Flood Control": "flood_control",
            "Word Filter": "blocked_words"
        }

        thresholds = self.rules.get("thresholds", {})
        spam_messages = thresholds.get("spam_messages", 5)
        spam_seconds = thresholds.get("spam_seconds", 10)
        flood_messages = thresholds.get("flood_messages", 5)
        flood_seconds = thresholds.get("flood_seconds", 5)
        emoji_limit = thresholds.get("emoji_limit", 5)

        embed = Embed(
            title="🛡 Server AutoMod Status",
            description=f"Current AutoMod configuration for {interaction.guild.name}",
            color=discord.Color.blue()
        )

        feature_status = ""
        for feature_name, rule_key in features.items():
            status = "✅ Enabled" if self.rules.get(rule_key, False) else "❌ Disabled"
            feature_status += f"**{feature_name}**: {status}\n"

        embed.add_field(name="Features", value=feature_status, inline=False)

        threshold_status = (
            f"**Spam Detection**: {spam_messages} msgs in {spam_seconds}s\n"
            f"**Flood Control**: {flood_messages} msgs in {flood_seconds}s\n"
            f"**Emoji Limit**: {emoji_limit} per message"
        )
        embed.add_field(name="Thresholds", value=threshold_status, inline=False)

        if self.rules.get("blocked_words", False):
            blocked_words = self.rules.get("blocked_words_list", [])
            blocked_words_str = ", ".join(f"`{word}`" for word in blocked_words) if blocked_words else "None"
            if len(blocked_words_str) > 1024:
                blocked_words_str = blocked_words_str[:1021] + "..."
            embed.add_field(name="Blocked Words", value=blocked_words_str, inline=False)

        await interaction.response.edit_message(content="", embed=embed, view=self)

    @ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="✖️")
    async def close_menu(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="AutoMod settings closed.", view=None)
class FeatureSettingsView(ui.View):
    def __init__(self, cog, guild_id, rules):
        super().__init__(timeout=300)
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
            (self.toggle_flood_control, "flood_control", "Flood Control"),
            (self.toggle_word_filter, "blocked_words", "Word Filter")
        ]

        for button, rule_key, label in button_configs:
            current_value = self.rules.get(rule_key, False)
            button.style = discord.ButtonStyle.green if current_value else discord.ButtonStyle.red
            button.label = f"{label}: {'ON' if current_value else 'OFF'}"

    async def toggle_rule(self, interaction: discord.Interaction, rule_name: str, label: str, button: ui.Button):
        current_value = self.rules.get(rule_name, False)
        new_value = not current_value
        self.rules[rule_name] = new_value
        self.cog.rules.setdefault(self.guild_id, {})[rule_name] = new_value
        self.cog.save_rules()

        button.style = discord.ButtonStyle.green if new_value else discord.ButtonStyle.red
        button.label = f"{label}: {'ON' if new_value else 'OFF'}"

        await interaction.response.edit_message(view=self)

    @ui.button(label="Link Blocker: OFF", style=discord.ButtonStyle.red)
    async def toggle_link_blocker(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "blocked_links", "Link Blocker", button)

    @ui.button(label="Spam Detection: OFF", style=discord.ButtonStyle.red)
    async def toggle_spam_detection(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "spam_detection", "Spam Detection", button)

    @ui.button(label="Profanity Filter: OFF", style=discord.ButtonStyle.red)
    async def toggle_profanity_filter(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "profanity_filter", "Profanity Filter", button)

    @ui.button(label="Emoji Spam: OFF", style=discord.ButtonStyle.red)
    async def toggle_emoji_spam_detection(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "emoji_spam_detection", "Emoji Spam", button)

    @ui.button(label="Flood Control: OFF", style=discord.ButtonStyle.red)
    async def toggle_flood_control(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "flood_control", "Flood Control", button)

    @ui.button(label="Word Filter: OFF", style=discord.ButtonStyle.red)
    async def toggle_word_filter(self, interaction: discord.Interaction, button: ui.Button):
        await self.toggle_rule(interaction, "blocked_words", "Word Filter", button)

    @ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = AutoModMainMenu(self.cog, self.guild_id, self.rules)
        await interaction.response.edit_message(
            content="🛡️ **AutoMod Control Panel**\nSelect an option to configure:",
            view=view
        )

class WordFiltersView(ui.View):
    def __init__(self, cog, guild_id, rules):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild_id = guild_id
        self.rules = rules

    @ui.button(label="View Blocked Words", style=discord.ButtonStyle.primary)
    async def view_blocked_words(self, interaction: discord.Interaction, button: ui.Button):
        blocked_words = self.rules.get("blocked_words_list", [])
        if not blocked_words:
            await interaction.response.send_message("No blocked words have been set.", ephemeral=True)
            return

        blocked_words_str = ", ".join(f"`{word}`" for word in blocked_words)

        if len(blocked_words_str) <= 1900:
            await interaction.response.send_message(f"**Blocked words:**\n{blocked_words_str}", ephemeral=True)
        else:
            parts = []
            current_part = "**Blocked words:**\n"

            for word in blocked_words:
                word_str = f"`{word}`, "
                if len(current_part) + len(word_str) > 1900:
                    parts.append(current_part.rstrip(", "))
                    current_part = word_str
                else:
                    current_part += word_str

            if current_part:
                parts.append(current_part.rstrip(", "))

            await interaction.response.send_message(parts[0], ephemeral=True)

            for part in parts[1:]:
                await interaction.followup.send(part, ephemeral=True)

    @ui.button(label="Add Blocked Word", style=discord.ButtonStyle.green)
    async def add_blocked_word(self, interaction: discord.Interaction, button: ui.Button):
        modal = BlockedWordModal(title="Add Blocked Word", cog=self.cog, guild_id=self.guild_id, rules=self.rules)
        await interaction.response.send_modal(modal)

    @ui.button(label="Remove Blocked Word", style=discord.ButtonStyle.red)
    async def remove_blocked_word(self, interaction: discord.Interaction, button: ui.Button):
        modal = BlockedWordModal(title="Remove Blocked Word", cog=self.cog, guild_id=self.guild_id,
                                 rules=self.rules, is_remove=True)
        await interaction.response.send_modal(modal)

    @ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = AutoModMainMenu(self.cog, self.guild_id, self.rules)
        await interaction.response.edit_message(
            content="🛡️ **AutoMod Control Panel**\nSelect an option to configure:",
            view=view
        )

class BlockedWordModal(ui.Modal):
    word_input = ui.TextInput(label="Enter word", placeholder="Enter a word to block or remove")

    def __init__(self, title, cog, guild_id, rules, is_remove=False):
        super().__init__(title=title)
        self.cog = cog
        self.guild_id = guild_id
        self.rules = rules
        self.is_remove = is_remove

    async def on_submit(self, interaction: discord.Interaction):
        word = self.word_input.value.lower().strip()

        if not word:
            await interaction.response.send_message("Please enter a valid word.", ephemeral=True)
            return

        self.rules.setdefault("blocked_words_list", [])

        if self.is_remove:
            if word in self.rules["blocked_words_list"]:
                self.rules["blocked_words_list"].remove(word)
                self.cog.rules.setdefault(self.guild_id, {})["blocked_words_list"] = self.rules["blocked_words_list"]
                self.cog.save_rules()
                await interaction.response.send_message(f"Removed `{word}` from blocked words.", ephemeral=True)
            else:
                await interaction.response.send_message(f"`{word}` is not in the blocked words list.", ephemeral=True)
        else:
            if word not in self.rules["blocked_words_list"]:
                self.rules["blocked_words_list"].append(word)
                self.cog.rules.setdefault(self.guild_id, {})["blocked_words_list"] = self.rules["blocked_words_list"]
                self.cog.save_rules()
                await interaction.response.send_message(f"Added `{word}` to blocked words.", ephemeral=True)
            else:
                await interaction.response.send_message(f"`{word}` is already in the blocked words list.",
                                                        ephemeral=True)


class ThresholdSettingsView(ui.View):
    def __init__(self, cog, guild_id, rules):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild_id = guild_id
        self.rules = rules

        # Ensure thresholds exist in the rules
        if "thresholds" not in self.rules:
            self.rules["thresholds"] = {
                "spam_messages": 5,
                "spam_seconds": 10,
                "flood_messages": 5,
                "flood_seconds": 5,
                "emoji_limit": 5
            }
            self.cog.save_rules()

    @ui.button(label="Spam Settings", style=discord.ButtonStyle.primary)
    async def spam_settings(self, interaction: discord.Interaction, button: ui.Button):
        modal = ThresholdModal(
            title="Spam Detection Settings",
            cog=self.cog,
            guild_id=self.guild_id,
            rules=self.rules,
            threshold_type="spam"
        )
        await interaction.response.send_modal(modal)

    @ui.button(label="Flood Settings", style=discord.ButtonStyle.primary)
    async def flood_settings(self, interaction: discord.Interaction, button: ui.Button):
        modal = ThresholdModal(
            title="Flood Control Settings",
            cog=self.cog,
            guild_id=self.guild_id,
            rules=self.rules,
            threshold_type="flood"
        )
        await interaction.response.send_modal(modal)

    @ui.button(label="Emoji Limit", style=discord.ButtonStyle.primary)
    async def emoji_settings(self, interaction: discord.Interaction, button: ui.Button):
        modal = EmojiLimitModal(
            title="Emoji Limit Settings",
            cog=self.cog,
            guild_id=self.guild_id,
            rules=self.rules
        )
        await interaction.response.send_modal(modal)

    @ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = AutoModMainMenu(self.cog, self.guild_id, self.rules)
        await interaction.response.edit_message(
            content="🛡️ **AutoMod Control Panel**\nSelect an option to configure:",
            view=view
        )
class ThresholdModal(ui.Modal):
    def __init__(self, title, cog, guild_id, rules, threshold_type):
        super().__init__(title=title)
        self.cog = cog
        self.guild_id = guild_id
        self.rules = rules
        self.threshold_type = threshold_type

        default_thresholds = {
            "spam_messages": 5,
            "spam_seconds": 10,
            "flood_messages": 5,
            "flood_seconds": 5,
            "emoji_limit": 5
        }

        if "thresholds" not in self.rules:
            self.rules["thresholds"] = default_thresholds.copy()
            self.cog.rules.setdefault(self.guild_id, {})["thresholds"] = default_thresholds.copy()
            self.cog.save_rules()
        else:
            for key, value in default_thresholds.items():
                if key not in self.rules["thresholds"]:
                    self.rules["thresholds"][key] = value
                    self.cog.rules.setdefault(self.guild_id, {}).setdefault("thresholds", {})[key] = value
                    self.cog.save_rules()

        thresholds = self.rules["thresholds"]

        self.messages = ui.TextInput(
            label=f"Message Count (Current: {thresholds[f'{threshold_type}_messages']})",
            placeholder="Number of messages to trigger detection",
            default=str(thresholds[f'{threshold_type}_messages']),
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.messages)

        self.seconds = ui.TextInput(
            label=f"Time Window in Seconds (Current: {thresholds[f'{threshold_type}_seconds']})",
            placeholder="Time window in seconds",
            default=str(thresholds[f'{threshold_type}_seconds']),
            required=True,
            min_length=1,
            max_length=3
        )
        self.add_item(self.seconds)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            messages = int(self.messages.value)
            seconds = int(self.seconds.value)

            if messages < 1 or messages > 20:
                await interaction.response.send_message("Message count must be between 1 and 20.", ephemeral=True)
                return

            if seconds < 1 or seconds > 300:
                await interaction.response.send_message("Time window must be between 1 and 300 seconds.",
                                                        ephemeral=True)
                return

            self.rules.setdefault("thresholds", {})
            self.rules["thresholds"][f"{self.threshold_type}_messages"] = messages
            self.rules["thresholds"][f"{self.threshold_type}_seconds"] = seconds

            self.cog.rules.setdefault(self.guild_id, {}).setdefault("thresholds", {})
            self.cog.rules[self.guild_id]["thresholds"][f"{self.threshold_type}_messages"] = messages
            self.cog.rules[self.guild_id]["thresholds"][f"{self.threshold_type}_seconds"] = seconds

            self.cog.save_rules()

            await interaction.response.send_message(
                f"{self.threshold_type.capitalize()} detection settings updated: {messages} messages in {seconds} seconds",
                ephemeral=True
            )

        except ValueError:
            await interaction.response.send_message("Please enter valid numbers.", ephemeral=True)

class EmojiLimitModal(ui.Modal):
    def __init__(self, title, cog, guild_id, rules):
        super().__init__(title=title)
        self.cog = cog
        self.guild_id = guild_id
        self.rules = rules

        thresholds = self.rules.get("thresholds", {"emoji_limit": 5})

        self.emoji_limit = ui.TextInput(
            label=f"Max Emojis Per Message (Current: {thresholds['emoji_limit']})",
            placeholder="Maximum number of emojis allowed per message",
            default=str(thresholds['emoji_limit']),
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.emoji_limit)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.emoji_limit.value)

            if limit < 1 or limit > 50:
                await interaction.response.send_message("Emoji limit must be between 1 and 50.", ephemeral=True)
                return

            self.rules.setdefault("thresholds", {})
            self.rules["thresholds"]["emoji_limit"] = limit

            self.cog.rules.setdefault(self.guild_id, {}).setdefault("thresholds", {})
            self.cog.rules[self.guild_id]["thresholds"]["emoji_limit"] = limit

            self.cog.save_rules()

            await interaction.response.send_message(
                f"Emoji limit updated: maximum {limit} emojis per message",
                ephemeral=True
            )

        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))
