# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import json
import logging
import os

import discord
from discord.ext import commands

from redisdb import get_redis

try:
    file = open('settings.json')
    file.close()
except FileNotFoundError:
    data = {
        'jsonfiles': ['settings'],
        'dev': False,
        'banlist': [],
        'useragentlist': [],
        'bottoken': '',
        'secret': str(os.urandom(32)),
        'taskqueue': 'redis',
        'username': 'tornium',
        'password': ''
    }
    with open(f'settings.json', 'w') as file:
        json.dump(data, file, indent=4)

with open('settings.json', 'r') as file:
    data = json.load(file)

redis = get_redis()
redis.set('dev', str(data['dev']))
redis.set('banlist', json.dumps(data['banlist']))
redis.set('useragentlist', json.dumps(data['useragentlist']))
redis.set('bottoken', data['bottoken'])
redis.set('secret', data['secret'])
redis.set('taskqueue', data['taskqueue'])
redis.set('username', data['username'])
redis.set('password', data['password'])

from bot import botutils
from bot.vault import Vault
from models.faction import Faction
from models.server import Server

botlogger = logging.getLogger('bot')
botlogger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
botlogger.addHandler(handler)

client = discord.client.Client()
intents = discord.Intents.default()
intents.reactions = True
intents.members = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix=botutils.get_prefix, help_command=None, intents=intents)


@bot.event
async def on_ready():
    guild_count = 0

    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")
        guild_count += 1

    print(f'Bot is in {guild_count} guilds.')

    bot.add_cog(Vault(bot, botlogger))


@bot.event
async def on_message(message):
    if message.author.bot:
        return None

    server = Server(message.guild.id)

    if len(server.admins) == 0:
        await bot.process_commands(message)

    for faction in server.factions:
        faction = Faction(faction)

        if faction.get_vault_config().get('withdrawal') == 0:
            continue

        if message.channel.id == faction.get_vault_config().get('withdrawal') and message.clean_content[0] != server.prefix:
            await message.delete()
            embed = discord.Embed()
            embed.title = "Bot Channel"
            embed.description = "This channel is only for vault withdrawals. Please do not post any other messages in" \
                                " this channel."
            message = await message.channel.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()
            return None

    await bot.process_commands(message)


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
async def help(ctx):
    embed = discord.Embed()
    embed.title = "Bot Help"
    embed.description = "Take a look at the [documentation](https://torn.deek.sh/bot/documentation) if you need any " \
                        "help."
    embed.add_field(name="General Information", value="[Tornium](https://torn.deek.sh/) | "
                                                      "[Tornium Bot](https://torn.deek.sh/bot)")
    embed.add_field(name="Support Server", value="[tiksan](https://discordapp.com/users/695828257949352028)")
    await ctx.send(embed=embed)


if __name__ == "__main__":
    redis = get_redis()
    bot.run(redis.get('bottoken'))
