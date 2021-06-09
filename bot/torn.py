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

from required import *


class Torn(commands.Cog):
    def __init__(self, logger, bot, client):
        self.logger = logger
        self.bot = bot
        self.client = client

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def addid(self, ctx, id:int):
        '''
        Adds the user's Torn ID to the database (across servers).
        '''

        if dbutils.get_user(ctx.message.author.id)["tornid"] != "":
            embed = discord.Embed()
            embed.title = "ID Already Set"
            embed.description = "Your ID is already set in the database."
            await ctx.send(embed=embed)
            return None

        request = await tornget(ctx, f'https://api.torn.com/user/{id}?selections=discord&key=', self.logger)

        if request["discord"]["discordID"] == "":
            embed = discord.Embed()
            embed.title = "ID Not Set"
            embed.description = "Your Discord ID is not set in the Torn database. To set your Discord ID in the Torn" \
                                "database, visit the official Torn Discord server and verify yourself."
            await ctx.send(embed=embed)

            self.logger.info(f'{ctx.message.author.name} has attempted to set id, but is not verified in the official'
                             f' Discord server.')
            return None

        if request["discord"]["discordID"] != str(ctx.message.author.id):
            embed = discord.Embed()
            embed.title = "Invalid ID"
            embed.description = f'Your Discord ID is not the same as the Discord ID stored in Torn\'s' \
                                f' database for your given Torn ID.'
            await ctx.send(embed=embed)
            self.logger.info(f'{ctx.message.author.name} has attempted to set their Torn ID to be {id}, but their'
                             f' Discord ID ({ctx.message.author.id} does not match the value in Torn\'s DB.')
            return None

        data = dbutils.read("users")
        data[str(ctx.message.author.id)]["tornid"] = str(id)
        dbutils.write("users", data)

        embed = discord.Embed()
        embed.title = "ID Set"
        embed.description = "Your ID has been set in the database."
        await ctx.send(embed=embed)
        self.logger.info(f'{ctx.message.author.name} has set their id to be {id}.')

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def addkey(self, ctx, key):
        '''
        Adds the user's Torn API key to the database (across servers). The Torn API key can be enabled and disabled for
        random, global use by the bot by running the `?enkey` and `?diskey` respectively. By default, user's Torn API
        key will not be used randomly and globally.
        '''

        if type(ctx.message.channel) != discord.DMChannel:
            await ctx.message.delete()

        request = await tornget(ctx, f'https://api.torn.com/user/?selections=&key=', self.logger, key=key)

        if dbutils.get_user(ctx.message.author.id, "tornid") == "":
            data = dbutils.read("users")
            data[str(ctx.message.author.id)]["tornid"] = request["player_id"]
            dbutils.write("users", data)

        data = dbutils.read("users")
        data[str(ctx.message.author.id)]["tornapikey"] = key
        dbutils.write("users", data)

        embed = discord.Embed()
        embed.title = "API Key Set"
        embed.description = f'{ctx.message.author.name} has set their API key.'
        await ctx.send(embed=embed)
        self.logger.info(f'{ctx.message.author.name} has set their Torn API key.')

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def rmkey(self, ctx):
        '''
        Removes the user's Torn API key from the database.
        '''

        if dbutils.get_user(ctx.message.author.id, "tornapikey") == "":
            embed = discord.Embed()
            embed.title = "API Key"
            embed.description = f'The API key of {ctx.message.author.name} has not been set yet, and therefore can ' \
                                f'not be removed,'
            await ctx.send(embed=embed)

        data = dbutils.read("users")
        data[str(ctx.message.author.id)]["tornapikey"] = ""
        data[str(ctx.message.author.id)]["generaluse"] = False
        dbutils.write("users", data)

        embed = discord.Embed()
        embed.title = "API Key"
        embed.description = f'The API key of {ctx.message.author.name} has been removed from the database.'
        await ctx.send(embed=embed)
        self.logger.info(f'{ctx.message.author.name} has removed their Torn API key.')

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def enkey(self, ctx):
        '''
        Enables the user's Torn API key for random, global use by the bot. Can be disabled by running `?diskey`.
        '''

        if dbutils.get_user(ctx.message.author.id, "generaluse"):
            embed = discord.Embed()
            embed.title = "API Key"
            embed.description = f'The API key of {ctx.message.author.name} is already authorized for general use.'
            await ctx.send(embed=embed)
            return None

        if dbutils.get_user(ctx.message.author.id, "tornapikey") == "":
            embed = discord.Embed()
            embed.title = "API Key"
            embed.description = f'No API key is currently set for {ctx.message.author.name}.'
            await ctx.send(embed=embed)
            return None

        data = dbutils.read("users")
        data[str(ctx.message.author.id)]["generaluse"] = True
        dbutils.write("users", data)

        embed = discord.Embed()
        embed.title = "API Key"
        embed.description = f'The API key of {ctx.message.author.name} has been enabled for random, global use by ' \
                            f'the bot. The API key can be removed from random, global use by running `?diskey`.'
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def diskey(self, ctx):
        '''
        Disables the user's Torn API key for random, global use by the bot. Can be enabled by running `?enkey`.
        '''

        if not dbutils.get_user(ctx.message.author.id, "generaluse"):
            embed = discord.Embed()
            embed.title = "API Key"
            embed.description = f'The API key of {ctx.message.author.name} is already not authorized for general use.'
            await ctx.send(embed=embed)
            return None

        if dbutils.get_user(ctx.message.author.id, "tornapikey") == "":
            embed = discord.Embed()
            embed.title = "API Key"
            embed.description = f'No API key is currently set for {ctx.message.author.name}.'
            await ctx.send(embed=embed)
            return None

        data = dbutils.read("users")
        data[str(ctx.message.author.id)]["generaluse"] = False
        dbutils.write("users", data)

        embed = discord.Embed()
        embed.title = "API Key"
        embed.description = f'The API key of {ctx.message.author.name} has been disabled for random, global use by ' \
                            f'the bot. The API key can be added to random, global use by running `?enkey`.'
        await ctx.send(embed=embed)
