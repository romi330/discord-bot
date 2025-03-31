import os
import time
import discord
from discord.ext import commands

admins = [445899149997768735]  # Replace with your Discord user ID

def developer_only():
    async def predicate(ctx):
        if ctx.author.id in admins:
            return True
        else:
            return False
    return commands.check(predicate)


class Restricted(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @developer_only()
    async def stats(self, ctx):
        ping = round(self.bot.latency * 1000)
        servers = len(self.bot.guilds)
        start = time.perf_counter()
        end = time.perf_counter()
        total = round(((end - start) * 1000) - ping)

        embed = discord.Embed(title="Bot Statistics", color=discord.Colour.dark_blue())
        embed.add_field(name="Connection Latency", value=f"{ping}ms")
        embed.add_field(name="API Latency", value=f"{abs(total)}ms")
        embed.add_field(name="Servers", value=str(servers))
        await ctx.author.send(embed=embed)

    @commands.command()
    @developer_only()
    async def announce(self, ctx, *, message):
        successful_send_count = 0
        for guild in self.bot.guilds:
            channel = guild.system_channel
            if channel:
                try:
                    embed = discord.Embed(
                        title=":rotating_light: Important Announcement :rotating_light:",
                        color=discord.Colour.blurple(),
                        description=message
                    )
                    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
                    embed.set_footer(text="This message is an official announcement from a developer of Paul!")
                    await channel.send(embed=embed)
                    successful_send_count += 1
                except Exception as e:
                    print(f"Failed to send message in {guild.name}: {e}")
        await ctx.author.send(f"Successfully sent `{successful_send_count}` messages.")

    @commands.command()
    @developer_only()
    async def servers(self, ctx):
        servers = [f"- {guild.name} - ({guild.id})" for guild in self.bot.guilds]
        with open("servers.txt", "w") as f:
            f.write("\n".join(servers))
        file = discord.File("servers.txt")
        await ctx.author.send(f"I am in `{len(self.bot.guilds)}` different servers.", file=file)
        os.remove("servers.txt")

    @commands.command()
    @developer_only()
    async def leave(self, ctx, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            await ctx.author.send("The bot is not in a server with that ID.")
            return
        await ctx.author.send(f"Leaving **{guild.name}** (`{guild.id}`)...")
        await guild.leave()

    @commands.command()
    @developer_only()
    async def serverinfo(self, ctx, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            await ctx.author.send("The bot is not in a server with that ID.")
            return

        embed = discord.Embed(title=f"Server Information - {guild.name}", color=discord.Color.blurple())
        embed.add_field(name="Server ID", value=guild.id, inline=False)
        embed.add_field(name="Member Count", value=guild.member_count, inline=False)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        await ctx.author.send(embed=embed)

    @commands.command()
    @developer_only()
    async def helpdev(self, ctx):
        msg = discord.Embed(title="Admin Commands", color=discord.Colour.blurple())
        msg.add_field(
            name="Bot Developer Console",
            value=(
                "**-** x!helpdev\n"
                "**-** x!servers\n"
                "**-** x!stats\n"
                "**-** x!announce <message>\n"
                "**-** x!leave <guild_id>\n"
                "**-** x!serverinfo <guild_id>\n"
            ),
            inline=False
        )
        msg.set_footer(text="[WARNING] - Many of these actions are global and will affect other servers!")
        await ctx.author.send(embed=msg)

async def setup(bot):
    await bot.add_cog(Restricted(bot))