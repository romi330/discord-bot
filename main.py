import asyncio
import os
import traceback
import platform
import datetime
import aiohttp
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.app_commands import CommandOnCooldown

VERSION = "v8.5.2"
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="x!", intents=intents, help_command=None)

load_dotenv()
LOG_CHANNEL = os.getenv("LOG_CHANNEL")
TOP_GG_API_TOKEN = os.getenv("TOP_GG_API_TOKEN")
TWITCH_URL = os.getenv("TWITCH_URL", "https://twitch.tv/romi330")

if not TOP_GG_API_TOKEN:
    raise ValueError("TOP_GG_API_TOKEN is missing. Please set it in the environment variables.")

try:
    LOG_CHANNEL = int(LOG_CHANNEL) if LOG_CHANNEL else None
except ValueError:
    LOG_CHANNEL = None
    print("Invalid LOG_CHANNEL value. Ensure it is a valid channel ID.")

os.chdir(os.path.dirname(os.path.abspath(__file__)))

async def post_server_count():
    url = f"https://top.gg/api/bots/{client.user.id}/stats"
    headers = {"Authorization": TOP_GG_API_TOKEN, "Content-Type": "application/json"}
    payload = {"server_count": len(client.guilds)}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                print(f"Failed to post server count to Top.gg. Status: {response.status}")
                print(await response.text())

@client.event
async def on_ready():
    try:
        client.start_time = datetime.datetime.now(datetime.timezone.utc)
        client.loop.create_task(post_server_count_periodically())
        print("Current working directory:", os.getcwd())
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} application command(s)")

        print("Bot Information:")
        print(f"  Name: {client.user.name}")
        print(f"  ID: {client.user.id}")
        print(f"  Discriminator: {client.user.discriminator}")
        print(f"  Bot Version: {VERSION}")

        print("\nServer Statistics:")
        total_servers = len(client.guilds)
        total_users = sum(guild.member_count for guild in client.guilds)
        print(f"  Total Servers: {total_servers}")
        print(f"  Total Users: {total_users}")
        print("\nBot is ready and operational!")
        log_channel_obj = client.get_channel(LOG_CHANNEL)
        if log_channel_obj:
            startup_embed = discord.Embed(title="🤖 Bot Startup Notification", color=discord.Color.green())
            startup_embed.add_field(name="Bot Version", value=VERSION, inline=False)
            startup_embed.add_field(name="Total Servers", value=total_servers, inline=True)
            startup_embed.add_field(name="Total Users", value=total_users, inline=True)
            startup_embed.add_field(name="Synced Commands", value=len(synced), inline=True)
            startup_embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
            startup_embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
            await log_channel_obj.send(embed=startup_embed)
        else:
            print("Log channel not found or invalid LOG_CHANNEL value. Skipping log message.")

        update_presence_task.start()
        print("Presence update task started.")
    except RuntimeError:
        print("Presence update task is already running.")
    except (discord.HTTPException, discord.ClientException, OSError) as e:
        print(f"Error in on_ready: {e}")
        traceback.print_exc()

async def post_server_count_periodically():
    while True:
        await post_server_count()
        await asyncio.sleep(1800)

local_activities = [f"{VERSION} | /help", f"{VERSION} | /paul", f"{VERSION} | /source", f"{VERSION} | /invite"]

@tasks.loop(seconds=30)
async def update_presence_task():
    for activity in local_activities:
        try:
            await client.change_presence(activity=discord.Streaming(name=activity, url=TWITCH_URL))
            await asyncio.sleep(30)
        except (discord.HTTPException, asyncio.TimeoutError):
            await client.get_channel(LOG_CHANNEL).send("Failed to update presence. Retrying...")
            await asyncio.sleep(60)

@update_presence_task.before_loop
async def before_update_presence():
    await client.wait_until_ready()

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.strip() == client.user.mention:
        await message.channel.send(":wave:")
    await client.process_commands(message)

@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, exception: app_commands.AppCommandError):
    red = discord.Colour.red()
    if not interaction.response.is_done():
        if isinstance(exception, CommandOnCooldown):
            cooldown_time = round(exception.retry_after, 2)
            error_message = f":hourglass: This command is on cooldown. Try again in `{cooldown_time}` seconds."
        elif isinstance(exception, (app_commands.CommandInvokeError, commands.CommandInvokeError)):
            error_message = f"<:what_in_the_hell:1353784539264192583> {str(exception).rsplit(':', maxsplit=1)[-1]}" if ":" in str(exception) else "<:what_in_the_hell:1353784539264192583> An error occurred."
        elif isinstance(exception, (commands.BadArgument, commands.MissingRequiredArgument)):
            error_message = f"<:what_in_the_hell:1353784539264192583> {str(exception)}"
        elif isinstance(exception, app_commands.MissingPermissions):
            missing_perms = ", ".join(exception.missing_permissions)
            error_message = f"<a:peepoclown:1353784183092416686> You are missing the following permission(s): `{missing_perms}`."
        elif isinstance(exception, app_commands.BotMissingPermissions):
            missing_perms = ", ".join(exception.missing_permissions)
            error_message = f"<:what_in_the_hell:1353784539264192583> I am missing the following permission(s): `{missing_perms}`."
        else:
            error_message = "<:what_in_the_hell:1353784539264192583> Oops, something went wrong. Please try again later."
        try:
            await interaction.response.send_message(embed=discord.Embed(description=error_message, color=red), ephemeral=True)
        except discord.HTTPException:
            try:
                await interaction.edit_original_response(embed=discord.Embed(description=error_message, color=red))
            except discord.HTTPException:
                pass
    if not isinstance(exception, (commands.BadArgument, commands.MissingRequiredArgument, app_commands.BotMissingPermissions, app_commands.MissingPermissions, CommandOnCooldown)):
        log_channel_obj = client.get_channel(LOG_CHANNEL)
        if log_channel_obj:
            error_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
            if len(error_trace) > 2000:
                error_trace = error_trace[:1997] + "..."
            await log_channel_obj.send(f"**Error**: {exception}\n```python\n{error_trace}```")

@client.event
async def on_command_error(ctx: commands.Context, exception: commands.CommandError):
    red = discord.Colour.red()

    if isinstance(exception, commands.CommandOnCooldown):
        cooldown_time = round(exception.retry_after, 2)
        error_message = f":hourglass: This command is on cooldown. Try again in `{cooldown_time}` seconds."
    elif isinstance(exception, commands.CheckFailure):
        error_message = "<a:peepoclown:1353784183092416686> You do not have permission to use this command."
    elif isinstance(
        exception, (commands.BadArgument, commands.MissingRequiredArgument)
    ):
        error_message = f"<:what_in_the_hell:1353784539264192583> {str(exception)}"
    elif isinstance(exception, commands.CommandNotFound):
        error_message = "<:what_in_the_hell:1353784539264192583> Command not found. Please try again later."
    elif isinstance(exception, commands.MissingPermissions):
        missing_perms = ", ".join(exception.missing_permissions)
        error_message = f"<a:peepoclown:1353784183092416686> You are missing the following permission(s): `{missing_perms}`."
    elif isinstance(exception, commands.BotMissingPermissions):
        missing_perms = ", ".join(exception.missing_permissions)
        error_message = f"<:what_in_the_hell:1353784539264192583> I am missing the following permission(s): `{missing_perms}`."
    else:
        error_message = "<:what_in_the_hell:1353784539264192583> Oops, something went wrong. Please try again later."

    try:
        await ctx.send(
            embed=discord.Embed(description=error_message, color=red), ephemeral=True
        )
    except discord.HTTPException:
        pass
    if not isinstance(
        exception,
        (
            commands.BadArgument,
            commands.MissingRequiredArgument,
            commands.BotMissingPermissions,
            commands.MissingPermissions,
            commands.CommandOnCooldown,
            commands.CheckFailure,
            commands.CommandNotFound,
        ),
    ):
        if isinstance(exception, (commands.CommandInvokeError, commands.CommandError)):
            log_channel_obj = client.get_channel(LOG_CHANNEL)
            if log_channel_obj:
                error_trace = "".join(
                    traceback.format_exception(
                        type(exception), exception, exception.__traceback__
                    )
                )
                if len(error_trace) > 2000:
                    error_trace = error_trace[:1997] + "..."
                await log_channel_obj.send(
                    f"**Error in `{ctx.command}`**: {exception}\n```python\n{error_trace}```"
                )

if __name__ == "__main__":
    extensions = ["cogs.restricted", "cogs.moderation", "cogs.misc", "cogs.fun", "cogs.feedback", "cogs.modmail", "cogs.automod", "cogs.help", "cogs.vote", "cogs.clash", "cogs.autorole"]
    for ext in extensions:
        asyncio.run(client.load_extension(ext))
    client.run(os.getenv("TOKEN"))
