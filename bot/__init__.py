# This file is part of torn-bot.
# 
# torn-bot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
# 
# torn-bot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with torn-bot.  If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
import psutil

import sys
import asyncio
import logging
import time

import vault
import admin
import moderation
import superuser
import torn
import armory
from required import *
import dbutils

assert sys.version_info >= (3, 6), "requires Python %s.%s or newer" % (3, 6)

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

botlogger = logging.getLogger('bot')
botlogger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
botlogger.addHandler(handler)

dbutils.initialize()

guilds = dbutils.read("guilds")
vaults = dbutils.read("vault")
users = dbutils.read("users")
aractions = dbutils.read("armory")

client = discord.client.Client()
intents = discord.Intents.default()
intents.reactions = True
intents.members = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix=get_prefix, help_command=None, intents=intents)


@bot.event
async def on_ready():
    guild_count = 0

    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")
        guild_count += 1

        for jsonguild in guilds["guilds"]:
            if jsonguild["id"] == str(guild.id):
                break
        else:
            guilds["guilds"].append({
                "id": str(guild.id),
                "prefix": "?",
                "tornapikey": "",
                "tornapikey2": "",
                "tornapikey3": ""
            })
            dbutils.write("guilds", guilds)

        if str(guild.id) not in vaults:
            vaults[guild.id] = {
                "channel": "",
                "role": "",
                "channel2": "",
                "role2": "",
                "banking": "",
                "banking2": ""
            }
            dbutils.write("vault", vaults)

        if str(guild.id) not in aractions:
            aractions[guild.id] = {
                "lastscan": 0,
                "requests": []
            }
            dbutils.write("armory", aractions)

        for member in guild.members:
            if str(member.id) in users:
                continue
            if member.bot:
                continue
            users[member.id] = {
                "tornid": "",
                "tornapikey": "",
                "generaluse": False
            }
            dbutils.write("users", users)

    print(f'Bot is in {guild_count} guilds.')

    bot.add_cog(vault.Vault(bot, botlogger))
    bot.add_cog(admin.Admin(botlogger, bot, client))
    bot.add_cog(moderation.Moderation(botlogger))
    bot.add_cog(superuser.Superuser(client, botlogger, bot))
    bot.add_cog(torn.Torn(botlogger, bot, client))
    bot.add_cog(armory.Armory(bot, botlogger))


@bot.event
async def on_guild_join(guild):
    embed = discord.Embed()
    embed.title = f'Welcome to {bot.user.display_name}'
    embed.description = f'Thank you for inviting {bot.user.display_name} to your server'
    embed.add_field(name="Help", value="`?help` or contact <@tiksan#9110> on Discord, on tiksan [2383326] on Torn,"
                                       " or dssecret on Github")
    embed.add_field(name="How to Setup", value="Run admin commands that can be found in the [Wiki]"
                                               "(https://github.com/dssecret/torn-bot/wiki) under [Commands]"
                                               "(https://github.com/dssecret/torn-bot/wiki/Commands).")
    await guild.text_channels[0].send(embed=embed)

    for jsonguild in guilds["guilds"]:
        if jsonguild["id"] == str(guild.id):
            break
    else:
        guilds["guilds"].append({
            "id": str(guild.id),
            "prefix": "?",
            "tornapikey": "",
            "tornapikey2": "",
            "tornapikey3": ""
        })
        dbutils.write("guilds", guilds)
    if str(guild.id) not in vaults:
        vaults[guild.id] = {
            "channel": "",
            "role": "",
            "channel2": "",
            "role2": "",
            "banking": "",
            "banking2": ""
        }
        dbutils.write("vault", vaults)


@bot.event
async def on_message(message):
    if message.author.bot:
        return None
    if str(message.channel.id) == dbutils.read("vault")[str(message.guild.id)]["banking"] \
            and message.clean_content[0] != get_prefix(client, message):
        await message.delete()
        embed = discord.Embed()
        embed.title = "Bot Channel"
        embed.description = "This channel is only for vault withdrawals. Please do not post any other messages in" \
                            " this channel."
        message = await message.channel.send(embed=embed)
        await asyncio.sleep(30)
        await message.delete()

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed()
        embed.title = "Cooldown"
        embed.description = f'You are on cooldown. Please try again in {round(error.retry_after, 2)} seconds.'
        message = await ctx.send(embed=embed)
        if str(ctx.message.channel.id) == dbutils.get_vault(ctx.guild.id, "banking"):
            await asyncio.sleep(30)
            await message.delete()
    else:
        print(error)
        botlogger.error(error)
        raise error


@bot.event
async def on_member_join(member):
    data = dbutils.read('users')

    if str(member.id) in data:
        return None
    if member.bot:
        return None
    data[member.id] = {
        "tornid": "",
        "tornapikey": "",
        "generaluse": False
    }
    dbutils.write("users", data)


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.guild)
async def ping(ctx):
    '''
    Shows the ping to the server
    '''

    latency = bot.latency
    botlogger.info(f'Latency: {latency}')

    embed = discord.Embed()
    embed.title = "Latency"
    embed.description = f'{latency} seconds'
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
async def prefix(ctx):
    '''
    Returns the prefix for the bot
    '''

    embed = discord.Embed()
    embed.title = "Bot Prefix"
    embed.description = f'The bot prefix is {get_prefix(bot, ctx.message)}.'
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
async def version(ctx):
    '''
    Returns the current version of the bot
    '''

    embed = discord.Embed()
    embed.title = "Version"
    embed.description = "v1.3"
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
async def license(ctx):
    '''
    Returns the copyright of the bot's software.
    '''

    embed = discord.Embed()
    embed.title = "License: Affero General Public License v3"
    embed.description = "torn-bot is free software: you can redistribute it and/or modify it under the terms of " \
                        "the GNU Affero General Public License as published by the Free Software Foundation, either" \
                        " version 3 of the License, or (at your option) any later version. torn-bot is distributed in" \
                        " the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied " \
                        "warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero " \
                        "General Public License for more details. You should have received a copy of the GNU" \
                        " General Public License along with torn-bot.  If not, see <https://www.gnu.org/licenses/>."
    embed.add_field(name="Full License", value="A full version of the license can also be found in the [GitHub"
                                               " repository](https://github.com/dssecret/torn-bot/blob/main/LICENSE).")
    embed.add_field(name="License Repercussions", value="Due to the license used for this project, all forks,"
                                                        " clones, and hosted versions of this project must include "
                                                        "this same license (the Affero General Public License v3)."
                                                        " Additionally, hosted versions must have a method for the"
                                                        " user to retrieve the source code from the hosted "
                                                        "versions' server(s). For more information on the AGPL"
                                                        " v3 license, check out GNU's [license page]"
                                                        "(https://www.gnu.org/licenses/).")
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.guild)
async def info(ctx):
    '''
    Returns the bot's info
    '''

    embed = discord.Embed()
    embed.title = "Bot Info"
    embed.add_field(name="Uptime", value=f'{round((time.time() - psutil.boot_time()) / 3600, 2)} hours')
    embed.add_field(name="% CPU", value=f'{psutil.cpu_percent()}%')
    embed.add_field(name="% Memory", value=f'{psutil.virtual_memory().percent}%')
    embed.add_field(name="% Swap", value=f'{psutil.swap_memory().percent}%')
    embed.add_field(name="Total Bytes Sent", value=get_size(psutil.net_io_counters().bytes_sent))
    embed.add_field(name="Total Bytes Received", value=get_size(psutil.net_io_counters().bytes_recv))
    await ctx.send(embed=embed)


@bot.command()
async def slap(ctx, member: discord.Member):
    await ctx.send("https://media0.giphy.com/media/3XlEk2RxPS1m8/giphy.gif?cid=ecf05e47aoaaoysgo5u0f7wwb6ld83m973qehz7twfaue7zt&rid=giphy.gif&ct=g")


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.guild)
async def help(ctx, arg=None):
    '''
    Returns links to the documentation, issues, developer contact information, and other pages if no command is passed
    as a parameter. If a command is passed as a parameter, the help command returns the help message of the passed
    command.
    '''

    embed = discord.Embed()
    command_list = [command.name for command in bot.commands]

    if not arg:
        embed = None
        page1 = discord.Embed(
            title='Useful Resources',
            description=f'Server: {ctx.guild.name}\nPrefix: {ctx.prefix}'
        ).set_footer(text="Page 1/5")
        page2 = discord.Embed(
            title='Vault Commands',
        ).set_footer(text="Page 2/5")
        page3 = discord.Embed(
            title='Admin Commands',
            description='Ha! You think I\'d share the admin commands with you. If you\'re really an admin on the server'
                        ', check out the commands in my docs.'
        ).set_footer(text="Page 3/5")
        page4 = discord.Embed(
            title="Torn Commands"
        ).set_footer(text="Page 4/5")
        page5 = discord.Embed(
            title="Miscellaneous Commands"
        ).set_footer(text="Page 5/5")

        page1.description = f'Server: {ctx.guild.name}\nPrefix: {ctx.prefix}'
        page1.add_field(name="GitHub Repository", value="https://github.com/dssecret/torn-bot")
        page1.add_field(name="GitHub Issues", value="https://github.com/dssecret/torn-bot/issues")
        page1.add_field(name="Documentation (Under Construction)", value="https://github.com/dssecret/torn-bot/wiki")
        page1.add_field(name="Torn City User", value="https://www.torn.com/profiles.php?XID=2383326")
        page1.add_field(name="Discord User", value="tiksan#9110")
        page1.add_field(name="For More Information", value="Please contact me (preferably on Discord or Github).")

        page2.add_field(name="`?withdraw [value]`", value="Sends a request to withdraw the passed amount of money to "
                                                          "the banker")
        page2.add_field(name="`?fulfill [request]`", value="Fulfills the specified withdrawal request")
        page2.add_field(name="`?bal`", value="Returns your full balance in the faction vault.")
        page2.add_field(name="`?b`", value="Returns a simplified version of your balance in the faction vault.")

        page4.add_field(name="`?addid`", value="Adds and verifies the user's Torn ID to the database to "
                                               "decrease number of API calls.")
        page4.add_field(name="`?addkey` and `?rmkey`", value="Respectively adds and removes the user's Torn API to the "
                                                             "database. The Torn API key can be enabled and disabled "
                                                             "for random, global use by running the `?enkey` and "
                                                             "`?diskey`` commands respectively. Adding the API key to "
                                                             "the bot will allow for more customized information to be"
                                                             " displayed.")
        page4.add_field(name="`?enkey` and `?diskey", value="Respectively enables and disables the user's API key "
                                                            "from random, global use.")

        page5.add_field(name="`?prefix`", value="Returns the bot's current prefix.")
        page5.add_field(name="`?version`", value="Returns the bot's current version (assuming I remember to change "
                                                 "it before I release it).")
        page5.add_field(name="`?license`", value="Returns the license of the bot's software.")
        page5.add_field(name="`?info`", value="Returns the bot's system information.")

        pages = [page1, page2, page3, page4, page5]

        message = await ctx.send(embed=page1)
        await message.add_reaction('⏮')
        await message.add_reaction('◀')
        await message.add_reaction('▶')
        await message.add_reaction('⏭')

        def check(reaction, user):
            return user == ctx.author

        i = 0
        reaction = None

        while True:
            if str(reaction) == '⏮':
                i = 0
                await message.edit(embed=pages[i])
            elif str(reaction) == '◀':
                if i > 0:
                    i -= 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == '▶':
                if i < 4:
                    i += 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == '⏭':
                i = 4
                await message.edit(embed=pages[i])

            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
                await message.remove_reaction(reaction, user)
            except:
                break

        await message.clear_reactions()
    elif arg in command_list:
        embed.add_field(name=arg, value=bot.get_command(arg).help)
    else:
        embed.description = "This command does not exist."

    if embed is not None:
        await ctx.send(embed=embed)


if __name__ == "__main__":
    bot.run(dbutils.read("guilds")["bottoken"])
