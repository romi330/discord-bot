import asyncio
import os
import traceback
from dotenv import load_dotenv
import random
import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import CommandOnCooldown
import spotipy
from spotipy.oauth2 import SpotifyOAuth

version = "v3.9"
intents = discord.Intents.default()
intents.message_content = True # Required for on_message, feedback, and modmail (privileged)
client = commands.Bot(command_prefix="x!", intents=intents, help_command=None)
log_channel = 1353416165350834278
load_dotenv()

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://localhost:8888/callback",
    scope="user-library-read user-read-playback-state user-read-currently-playing"
)

sp = spotipy.Spotify(auth_manager=sp_oauth)

def refresh_token():
    token_info = sp_oauth.get_cached_token()
    if token_info and sp_oauth.is_token_expired(token_info):
        new_token = sp_oauth.refresh_access_token(token_info["refresh_token"])
        return new_token["access_token"]
    return token_info["access_token"]

async def send_dm(user, message):
    try:
        await user.send(message)
    except discord.Forbidden:
        print("I do not have permission to send DMs to this user.")

@client.event
async def on_ready():
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} application command(s)")

        print(f"Bot Information:")
        print(f"  Name: {client.user.name}")
        print(f"  ID: {client.user.id}")
        print(f"  Discriminator: {client.user.discriminator}")
        print(f"  Bot Version: {version}")

        print("\nServer Statistics:")
        total_servers = len(client.guilds)
        total_users = sum(guild.member_count for guild in client.guilds)
        print(f"  Total Servers: {total_servers}")
        print(f"  Total Users: {total_users}")

        log_channel_obj = client.get_channel(log_channel)
        if log_channel_obj:
            startup_embed = discord.Embed(
                title="🤖 Bot Startup Notification",
                color=discord.Color.green()
            )
            startup_embed.add_field(name="Bot Version", value=version, inline=False)
            startup_embed.add_field(name="Total Servers", value=total_servers, inline=True)
            startup_embed.add_field(name="Total Users", value=total_users, inline=True)
            startup_embed.add_field(name="Synced Commands", value=len(synced), inline=True)

            import platform
            startup_embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
            startup_embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)

            await log_channel_obj.send(embed=startup_embed)

    except Exception as e:
        print(f"Error in on_ready: {e}")
        traceback.print_exc()

    client.loop.create_task(update_spotify_activity())

    print("\nBot is ready and operational!")

async def update_spotify_activity():
    global sp
    while True:
        try:
            sp = spotipy.Spotify(auth_manager=sp_oauth)
            current_playback = sp.current_playback()

            if current_playback and current_playback.get('is_playing') and current_playback.get('item'):
                track_name = current_playback['item']['name']
                artist_name = current_playback['item']['artists'][0]['name']

                activity = discord.Activity(
                    type=discord.ActivityType.streaming,
                    name=track_name,
                    details=f'Listening to {track_name}',
                    state=f'by {artist_name}',
                    url="https://twitch.tv/romi330"
                )
            else:
                activity = discord.Streaming(name=f"{version} | /paul", url="https://twitch.tv/romi330")

            await client.change_presence(activity=activity)
            await asyncio.sleep(10)

        except Exception as e:
            print(f"Error updating Spotify activity: {e}")
            traceback.print_exc()
            await asyncio.sleep(30)

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.strip() == client.user.mention:
        if random.random() > 0.9999:
            await message.channel.send("<a:peepoclown:1353784183092416686>")
            user = await client.fetch_user('445899149997768735')
            await send_dm(user, "peepo happened!")
        else:
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
            error_message = f":x: {str(exception).split(':')[-1]}" if ":" in str(exception) else ":x: An error occurred."
        elif isinstance(exception, (commands.BadArgument, commands.MissingRequiredArgument)):
            error_message = f":x: {str(exception)}"
        else:
            error_message = ":x: Oops, something went wrong. Please try again later."

        try:
            await interaction.response.send_message(
                embed=discord.Embed(description=error_message, color=red),
                ephemeral=True
            )
        except discord.HTTPException:
            try:
                await interaction.edit_original_response(embed=discord.Embed(description=error_message, color=red))
            except discord.HTTPException:
                pass

    log_channel_obj = client.get_channel(log_channel)
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
        error_message = ":x: You do not have permission to use this command."
    elif isinstance(exception, (commands.BadArgument, commands.MissingRequiredArgument)):
        error_message = f":x: {str(exception)}"
    else:
        error_message = ":x: Oops, something went wrong. Please try again later."

    try:
        await ctx.send(embed=discord.Embed(description=error_message, color=red))
    except discord.HTTPException:
        pass

    log_channel_obj = client.get_channel(log_channel)
    if log_channel_obj:
        error_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        if len(error_trace) > 2000:
            error_trace = error_trace[:1997] + "..."
        await log_channel_obj.send(f"**Error in `{ctx.command}`**: {exception}\n```python\n{error_trace}```")


if __name__ == '__main__':
    asyncio.run(client.load_extension("cogs.restricted"))
    asyncio.run(client.load_extension("cogs.moderation"))
    asyncio.run(client.load_extension("cogs.misc"))
    asyncio.run(client.load_extension("cogs.fun"))
    asyncio.run(client.load_extension("cogs.feedback"))
    asyncio.run(client.load_extension("cogs.modmail"))
    asyncio.run(client.load_extension("cogs.automod"))
    load_dotenv()
    client.run(os.getenv("TOKEN"))
