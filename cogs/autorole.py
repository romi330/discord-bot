import json
import os

import discord
from discord import app_commands
from discord.ext import commands


class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.filepath = "autorole_config.json"
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({}, f)
        with open(self.filepath, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def save_config(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.config and self.config[guild_id].get("enabled", False):
            role_id = self.config[guild_id].get("role_id")
            if role_id:
                role = member.guild.get_role(int(role_id))
                if role:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        pass
                    except discord.HTTPException:
                        pass

    @app_commands.command(
        name="autorole", description="Configure auto-role settings for this server."
    )
    @app_commands.default_permissions(administrator=True)
    async def autorole(self, interaction: discord.Interaction):

        class AutoRoleView(discord.ui.View):
            def __init__(self, cog, interaction):
                super().__init__(timeout=60)
                self.cog = cog
                self.interaction = interaction
                self.update_toggle_button()

            def update_toggle_button(self):
                guild_id = str(self.interaction.guild.id)
                enabled = self.cog.config.get(guild_id, {}).get("enabled", False)
                toggle_button = self.children[0]
                toggle_button.style = (
                    discord.ButtonStyle.green if enabled else discord.ButtonStyle.red
                )
                toggle_button.label = "Auto-Role (ON)" if enabled else "Auto-Role (OFF)"

            @discord.ui.button(
                label="Toggle Auto-Role", style=discord.ButtonStyle.green
            )
            async def toggle_autorole(
                self, interaction: discord.Interaction, _: discord.ui.Button
            ):
                if interaction.user != self.interaction.user:
                    await interaction.response.send_message(
                        "You are not allowed to use this button.", ephemeral=True
                    )
                    return

                guild_id = str(self.interaction.guild.id)
                if guild_id not in self.cog.config:
                    self.cog.config[guild_id] = {"enabled": False, "role_id": None}

                self.cog.config[guild_id]["enabled"] = not self.cog.config[guild_id][
                    "enabled"
                ]
                self.cog.save_config()
                self.update_toggle_button()
                status = (
                    "enabled" if self.cog.config[guild_id]["enabled"] else "disabled"
                )
                await interaction.response.edit_message(
                    content=f"Auto-role has been {status}.", view=self
                )

            @discord.ui.button(label="Set Role", style=discord.ButtonStyle.blurple)
            async def set_role(
                self, interaction: discord.Interaction, _: discord.ui.Button
            ):
                if interaction.user != self.interaction.user:
                    await interaction.response.send_message(
                        "You are not allowed to use this button.", ephemeral=True
                    )
                    return

                class RoleSelect(discord.ui.Select):
                    def __init__(self, cog, interaction):
                        self.cog = cog
                        self.interaction = interaction
                        options = [
                            discord.SelectOption(label=role.name, value=str(role.id))
                            for role in interaction.guild.roles
                            if not role.is_bot_managed()
                        ]
                        super().__init__(
                            placeholder="Select a role...", options=options
                        )

                    async def callback(self, interaction: discord.Interaction):
                        role_id = self.values[0]
                        guild_id = str(self.interaction.guild.id)
                        if guild_id not in self.cog.config:
                            self.cog.config[guild_id] = {
                                "enabled": False,
                                "role_id": None,
                            }

                        self.cog.config[guild_id]["role_id"] = role_id
                        self.cog.save_config()
                        role = self.interaction.guild.get_role(int(role_id))
                        await interaction.response.send_message(
                            f"Auto-role has been set to {role.name}.", ephemeral=True
                        )

                select = RoleSelect(self.cog, self.interaction)
                view = discord.ui.View()
                view.add_item(select)
                await interaction.response.send_message(
                    "Select a role for auto-role:", view=view, ephemeral=True
                )

        view = AutoRoleView(self, interaction)
        await interaction.response.send_message(
            "Use the buttons below to configure auto-role:", view=view, ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(AutoRole(bot))
