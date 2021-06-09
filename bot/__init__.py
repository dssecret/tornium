# This file is part of torn-command.
#
# torn-command is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# torn-command is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with torn-command.  If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
import psutil

import sys
import logging
import time

import vault
import admin
from required import *
import dbutils

assert sys.version_info >= (3, 6), "requires Python 3.6 or newer"

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

    print(f'Bot is in {guild_count} guilds.')

    bot.add_cog(vault.Vault(bot, botlogger))
    bot.add_cog(admin.Admin(botlogger, bot, client))


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

    # for jsonguild in guilds["guilds"]:
    #     if jsonguild["id"] == str(guild.id):
    #         break
    # else:
    #     guilds["guilds"].append({
    #         "id": str(guild.id),
    #         "prefix": "?",
    #         "tornapikey": "",
    #         "tornapikey2": "",
    #         "tornapikey3": ""
    #     })
    #     dbutils.write("guilds", guilds)
    # if str(guild.id) not in vaults:
    #     vaults[guild.id] = {
    #         "channel": "",
    #         "role": "",
    #         "channel2": "",
    #         "role2": "",
    #         "banking": "",
    #         "banking2": ""
    #     }
    #     dbutils.write("vault", vaults)


# @bot.event
# async def on_message(message):
#     if message.author.bot:
#         return None
#     if str(message.channel.id) == dbutils.read("vault")[str(message.guild.id)]["banking"] \
#             and message.clean_content[0] != get_prefix(client, message):
#         await message.delete()
#         embed = discord.Embed()
#         embed.title = "Bot Channel"
#         embed.description = "This channel is only for vault withdrawals. Please do not post any other messages in" \
#                             " this channel."
#         message = await message.channel.send(embed=embed)
#         await asyncio.sleep(30)
#         await message.delete()
#
#     await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    data = dbutils.read('users')

    if str(member.id) in data:
        return None
    if member.bot:
        return None
    # data[member.id] = {
    #     "tornid": "",
    #     "tornapikey": "",
    #     "generaluse": False
    # }
    # dbutils.write("users", data)


@bot.command()
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
async def prefix(ctx):
    '''
    Returns the prefix for the bot
    '''

    embed = discord.Embed()
    embed.title = "Bot Prefix"
    embed.description = f'The bot prefix is {get_prefix(bot, ctx.message)}.'
    await ctx.send(embed=embed)


@bot.command()
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
async def help(ctx):
    embed = discord.Embed()
    embed.title = "Bot Help"
    embed.description = "Take a look at the [documentation](https://torn.deek.sh/bot/documentation) if you need any " \
                        "help."
    embed.add_field(name="General Information", value="[Torn Command](https://torn.deek.sh/) | "
                                                      "[Torn Command Bot](https://torn.deek.sh/bot)")
    embed.add_field(name="Support Server", value="[tiksan](https://discordapp.com/users/695828257949352028)")
    await ctx.send(embed=embed)


if __name__ == "__main__":
    bot.run(dbutils.read("guilds")["bottoken"])
