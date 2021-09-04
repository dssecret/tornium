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
import logging
import random

import discord
from discord.ext import commands

from bot import botutils
from bot.vault import Vault
from models import settingsmodel
from models.faction import Faction
from models.server import Server
from models.user import DiscordUser, User

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


@bot.event
async def on_message(message):
    if message.author.bot:
        return None

    server = Server(message.guild.id)

    if len(server.admins) == 0:
        embed = discord.Embed()
        embed.title = 'No Server Admins Stored'
        embed.description = f'There are no server admins stored for {message.guild.name}; therefore an admin will ' \
                            f'need to log in to the [dashboard](https://torn.deek.sh/) for an admin to be added for ' \
                            f'the bot to be operational.'
        message = await message.channel.send(embed=embed)
        await asyncio.sleep(30)
        await message.delete()
        return None

    user = DiscordUser(message.author.id, User(random.choice(server.admins)).key)

    if len(server.factions) != 1:
        if user.tid == 0:
            await message.delete()
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'You are required to be verified officially through the ' \
                                '[official Torn Discord server](https://www.torn.com/discord) before being able to ' \
                                'utilize this bot. If you have recently verified, please ' \
                                'wait for a minute or two before trying again.'
            await message.author.send(embed=embed)
            return None
    elif len(server.factions) == 0:
        if message.clean_content[0] != server.prefix:
            await bot.process_commands(message)
        else:
            return None

        user = User(user.tid)

        if user.factiontid == 0:
            user.refresh(key=User(random.choice(server.admins)).key, force=True)

            if user.factiontid == 0:
                embed = discord.Embed()
                embed.title = 'Faction ID Error'
                embed.description = f'The faction ID of {message.author.name} is not set regardless of the ' \
                                    f'forced refresh.'
                message = await message.channel.send(embed=embed)
                await asyncio.sleep(30)
                await message.delete()
                return None

        faction = Faction(user.factiontid)
    else:
        faction = Faction(server.factions[0])

    if message.channel.id == faction.get_vault_config()['withdrawal'] and message.clean_content[0] != server.prefix:
        await message.delete()
        embed = discord.Embed()
        embed.title = "Bot Channel"
        embed.description = "This channel is only for vault withdrawals. Please do not post any other messages in" \
                            " this channel."
        message = await message.channel.send(embed=embed)
        await asyncio.sleep(30)
        await message.delete()

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
    bot.run(settingsmodel.get('settings', 'bottoken'))
