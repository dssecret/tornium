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

import logging

import discord
from discord.ext import commands

from bot import botutils
from bot.vault import Vault
from models import settingsmodel

settingsmodel.initialize()

botlogger = logging.getLogger('bot')
botlogger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
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
    bot.run(settingsmodel.get('settings', 'bottoken'))
