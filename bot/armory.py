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
from discord.ext import commands, tasks
import requests

from required import *

import time
import re
from datetime import datetime


shorts = {
    "Beer": "Bottle of Beer",
    "Xan": "Xanax",
    "A+": "Blood Bag : A+",
    "A-": "Blood Bag : A-",
    "AB+": "Blood Bag : AB+",
    "AB-": "Blood Bag : AB-",
    "B-": "Blood Bag : B-",
    "Irradiated": "Blood Bag : Irradiated",
    "O+": "Blood Bag : O+",
    "O-": "Blood Bag : O-"
}


class Armory(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger

        # self.autoscan.start()

    @tasks.loop(minutes=30)
    async def autoscan(self):
        self.logger.info(f'The armory autoscan has started at {datetime.now()}')
        data = dbutils.read("armory")

        for guild in dbutils.read("guilds")["guilds"]:
            start = time.time()
            request = requests.get(f'https://api.torn.com/faction/?selections=armorynewsfull&key={guild["tornapikey"]}'
                                  f'&comment=TornBot')

            if request.status_code != 200:
                self.logger.error(f'The Torn API has responded with HTTP status code {request.status_code}.')
                return Exception

            if 'error' in request.json():
                error = request.json()['error']
                self.logger.error(f'The Torn API has responded with error code {error["code"]}.')
                raise Exception

            request = request.json()

            armory = request["armorynews"]
            items_added = 0

            for key, action in armory.items():
                if action["timestamp"] <= int(dbutils.read("armory")[guild["id"]]["lastscan"]):
                    continue

                timestamp = action["timestamp"]
                action = re.sub('<[^<]+?>', '', action['news'])
                words = action.split(" ")

                if "used" not in words:
                    continue  # Not yet implemented

                data[guild["id"]]["requests"].append({
                    "user": words[0],
                    "item": action.split("faction's", 1)[1][1:-7],
                    "timestamp": timestamp
                })
                data[guild["id"]]["lastscan"] = int(time.time())
                items_added += 1

            dbutils.write("armory", data)
            self.logger.info(f'The scan of guild {guild} has been completed in {start - time.time()} seconds with '
                             f'{items_added} actions added.')

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def search(self, ctx, start, stop="now", item="Xanax"):
        if not check_admin(ctx.message.author) and dbutils.get_superuser() != ctx.message.author.id:
            embed = discord.Embed()
            embed.title = "Permission Denied"
            embed.description = f'This command requires {ctx.message.author.name} to be an Administrator. ' \
                                f'This interaction has been logged.'
            await ctx.send(embed=embed)

            self.logger.warning(f'{ctx.message.author.name} has attempted to run search, but is not an Administrator.')
            return None

        if stop == "now":
            stop = str(int(time.time()))

        actions = {}

        if item in shorts:
            item = shorts[item]

        data = dbutils.read("armory")[str(ctx.guild.id)]["requests"]

        for action in data:
            if item == action["item"] and int(start) <= action["timestamp"] <= int(stop):
                if action["user"] in actions:
                    actions[action["user"]] += 1
                else:
                    actions[action["user"]] = 1

        pages = []
        number_users = 0
        embed = discord.Embed()
        embed.title = f'Armory Log for {item}'

        total_users = len(actions)
        start_time = datetime.fromtimestamp(int(start)).strftime("%c")
        stop_time = datetime.fromtimestamp(int(stop)).strftime("%c")

        embed.description = f'Total Users: {total_users}\n' \
                            f'Start Time: {start_time}\n' \
                            f'End Time: {stop_time}'

        for user, number in actions.items():
            if number_users == 24:
                pages.append(embed)
                embed = discord.Embed()
                embed.title = f'Armory Log for {item}'
                total_users = len(actions)
                start_time = datetime.fromtimestamp(int(start)).strftime("%c")
                stop_time = datetime.fromtimestamp(int(stop)).strftime("%c")

                embed.description = f'Total Users: {total_users}\n' \
                                    f'Start Time: {start_time}\n' \
                                    f'End Time: {stop_time}'
                pages.append(embed)

            embed.add_field(name=user, value=f'{item} Used: {number}')
            number_users += 1
        else:
            if len(pages) == 0:
                pages.append(embed)

        message = await ctx.send(embed=pages[0])
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
                if i < len(pages):
                    i += 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == '⏭':
                i = len(pages)
                await message.edit(embed=pages[i])

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                await message.remove_reaction(reaction, user)
            except Exception as e:
                print(e)
                break

        await message.clear_reactions()

