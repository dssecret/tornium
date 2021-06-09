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
import dbutils

import time
import asyncio


class Vault(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger

    @commands.command(aliases=["req", "with", "w"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def withdraw(self, ctx, arg):
        '''
        Sends a message to faction leadership (assuming you have enough funds in the vault and you are a member of the
        specific faction)
        '''

        await ctx.message.delete()

        if ctx.message.author.nick is None:
            sender = ctx.message.author.name
        else:
            sender = ctx.message.author.nick

        senderid = get_torn_id(sender)
        sender = remove_torn_id(sender)

        if dbutils.get_user(ctx.message.author.id, "tornid") == "":
            verification = await tornget(ctx, f'https://api.torn.com/user/{senderid}?selections=discord&key=',
                                         self.logger)

            if verification["discord"]["discordID"] != str(ctx.message.author.id) and \
                    verification["discord"]["discordID"] != "":
                embed = discord.Embed()
                embed.title = "Permission Denied"
                embed.description = f'The nickname of {ctx.message.author.nick} in {ctx.guild.name} does not reflect ' \
                                    f'the Torn ID and username. Please update the nickname (i.e. through YATA) or add' \
                                    f' your ID to the database via the `?addid` or `addkey` commands (NOTE: the ' \
                                    f'`?addkey` command requires your Torn API key). This interaction has been logged.'
                await ctx.send(embed=embed)
                self.logger.warning(f'{ctx.message.author.id} (known as {ctx.message.author.name} does not have an '
                                    f'accurate nickname, and attempted to withdraw some money from the faction vault.')
                return None
            else:
                senderid = verification["discord"]["userID"]

        value = text_to_num(arg)
        self.logger.info(f'{sender} has submitted a request for {arg}.')

        primary_faction = await tornget(ctx, "https://api.torn.com/faction/?selections=donations&key=", self.logger)

        secondary_faction = None
        if dbutils.get_guild(ctx.guild.id, "tornapikey2") != "":
            secondary_faction = await tornget(ctx, "https://api.torn.com/faction/?selections=donations&key=",
                                              self.logger, 2)

        tertiary_faction = None
        if dbutils.get_guild(ctx.guild.id, "tornapikey3") != "":
            tertiary_faction = await tornget(ctx, "https://api.torn.com/faction/?selections=donations&key=",
                                             self.logger, 3)

        if str(senderid) in primary_faction["donations"]:
            if int(value) > primary_faction["donations"][str(senderid)]["money_balance"]:
                self.logger.warning(f'{sender} has requested {arg}, but only has '
                                    f'{primary_faction["donations"][str(senderid)]["money_balance"]} in the vault.')
                await ctx.send(f'You do not have {arg} in the faction vault.')
                return None
            else:
                channel = discord.utils.get(ctx.guild.channels, name=dbutils.get_vault(ctx.guild.id, "channel"))

                self.logger.info(f'{sender} has successfully requested {arg} from the faction vault.')

                requestid = dbutils.read("requests")["nextrequest"]

                embed = discord.Embed()
                embed.title = f'Money Request #{dbutils.read("requests")["nextrequest"]}'
                embed.description = "Your request has been forwarded to the faction leadership."
                original = await ctx.send(embed=embed)

                embed = discord.Embed()
                embed.title = f'Money Request #{dbutils.read("requests")["nextrequest"]}'
                embed.description = f'{sender} is requesting {arg} from the faction vault. To fulfill this request, ' \
                                    f'enter `?f {requestid}` in this channel.'
                message = await channel.send(dbutils.get_vault(ctx.guild.id, "role"), embed=embed)

                data = dbutils.read("requests")
                data["nextrequest"] += 1
                data[requestid] = {
                    "requester": ctx.message.author.id,
                    "timerequested": time.ctime(),
                    "fulfiller": None,
                    "timefulfilled": "",
                    "requestmessage": original.id,
                    "withdrawmessage": message.id,
                    "fulfilled": False,
                    "faction": 1
                }
                dbutils.write("requests", data)

        elif str(senderid) in secondary_faction["donations"]:
            if int(value) > secondary_faction["donations"][str(senderid)]["money_balance"]:
                self.logger.warning(f'{sender} has requested {arg}, but only has '
                                    f'{secondary_faction["donations"][str(senderid)]["money_balance"]} in the vault.')
                await ctx.send(f'You do not have {arg} in the faction vault.')
                return None
            else:
                channel = discord.utils.get(ctx.guild.channels, name=dbutils.get_vault(ctx.guild.id, "channel2"))

                self.logger.info(f'{sender} has successfully requested {arg} from the faction vault.')

                requestid = dbutils.read("requests")["nextrequest"]

                embed = discord.Embed()
                embed.title = f'Money Request #{dbutils.read("requests")["nextrequest"]}'
                embed.description = "Your request has been forwarded to the faction leadership."
                original = await ctx.send(embed=embed)

                embed = discord.Embed()
                embed.title = f'Money Request #{dbutils.read("requests")["nextrequest"]}'
                embed.description = f'{sender} is requesting {arg} from the faction vault. To fulfill this request, ' \
                                    f'enter `?f {requestid}` in this channel.'
                message = await channel.send(dbutils.get_vault(ctx.guild.id, "role2"), embed=embed)

                data = dbutils.read("requests")
                data["nextrequest"] += 1
                data[requestid] = {
                    "requester": ctx.message.author.id,
                    "timerequested": time.ctime(),
                    "fulfiller": None,
                    "timefulfilled": "",
                    "requestmessage": original.id,
                    "withdrawmessage": message.id,
                    "fulfilled": False,
                    "faction": 2
                }
                dbutils.write("requests", data)
        elif str(senderid) in tertiary_faction["donations"]:
            if int(value) > tertiary_faction["donations"][str(senderid)]["money_balance"]:
                self.logger.warning(f'{sender} has requested {arg}, but only has '
                                    f'{tertiary_faction["donations"][str(senderid)]["money_balance"]} in the vault.')
                await ctx.send(f'You do not have {arg} in the faction vault.')
                return None
            else:
                channel = discord.utils.get(ctx.guild.channels, name=dbutils.get_vault(ctx.guild.id, "channel3"))

                self.logger.info(f'{sender} has successfully requested {arg} from the faction vault.')

                requestid = dbutils.read("requests")["nextrequest"]

                embed = discord.Embed()
                embed.title = f'Money Request #{dbutils.read("requests")["nextrequest"]}'
                embed.description = "Your request has been forwarded to the faction leadership."
                original = await ctx.send(embed=embed)

                embed = discord.Embed()
                embed.title = f'Money Request #{dbutils.read("requests")["nextrequest"]}'
                embed.description = f'{sender} is requesting {arg} from the faction vault. To fulfill this request, ' \
                                    f'enter `?f {requestid}` in this channel.'
                message = await channel.send(dbutils.get_vault(ctx.guild.id, "role3"), embed=embed)

                data = dbutils.read("requests")
                data["nextrequest"] += 1
                data[requestid] = {
                    "requester": ctx.message.author.id,
                    "timerequested": time.ctime(),
                    "fulfiller": None,
                    "timefulfilled": "",
                    "requestmessage": original.id,
                    "withdrawmessage": message.id,
                    "fulfilled": False,
                    "faction": 3
                }
                dbutils.write("requests", data)
        else:
            self.logger.warning(f'{sender} who is not a member of stored factions has requested {arg}.')

            embed = discord.Embed()
            embed.title = "Money Request"
            embed.description = f'{sender} is not a member of stored factions has requested {arg}.'
            await ctx.send(embed=embed)
            return None

    @commands.command(aliases=['f'])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def fulfill(self, ctx, request):
        '''
        Indicates the fulfillment of the specified request
        '''

        if dbutils.read("requests")[request]["fulfilled"]:
            embed = discord.Embed()
            embed.title = "Request Already Fulfilled"
            embed.description = f'Request #{request} has already been fulfilled by ' \
                                f'{ctx.guild.get_member(dbutils.read("requests")[request]["fulfiller"]).name} ' \
                                f'at {dbutils.read("requests")[request]["timefulfilled"]}.'
            await ctx.send(embed=embed)
            return None

        await ctx.message.delete()

        if dbutils.read("requests")[request]["faction"] == 1:
            channel = discord.utils.get(ctx.guild.channels, id=int(dbutils.get_vault(ctx.guild.id, "banking")))
        elif dbutils.read("requests")[request]["faction"] == 2:
            channel = discord.utils.get(ctx.guild.channels, id=int(dbutils.get_vault(ctx.guild.id, "banking2")))
        else:
            channel = discord.utils.get(ctx.guild.channels, id=int(dbutils.get_vault(ctx.guild.id, "banking3")))
        original = await channel.fetch_message(int(dbutils.read("requests")[request]["requestmessage"]))

        embed = discord.Embed()
        embed.title = original.embeds[0].title

        if dbutils.read("requests")[request]["faction"] == 1:
            channel = discord.utils.get(ctx.guild.channels, name=dbutils.get_vault(ctx.guild.id, "channel"))
        elif dbutils.read("requests")[request]["faction"] == 2:
            channel = discord.utils.get(ctx.guild.channels, name=dbutils.get_vault(ctx.guild.id, "channel2"))
        else:
            channel = discord.utils.get(ctx.guild.channels, name=dbutils.get_vault(ctx.guild.id, "channel3"))
        message = await channel.fetch_message(int(dbutils.read("requests")[request]["withdrawmessage"]))

        embed.add_field(name='Original Message', value=message.embeds[0].description.split(".")[0])
        embed.description = f'The request has been fulfilled by {ctx.message.author.name} at {time.ctime()}.'
        await message.edit(embed=embed)

        embed.description = f'The request has been fulfilled by {ctx.message.author.name} at {time.ctime()}.'
        embed.clear_fields()
        await original.edit(embed=embed)

        data = dbutils.read("requests")
        data[request]["fulfiller"] = ctx.message.author.id
        data[request]["fulfilled"] = True
        data[request]["timefulfilled"] = time.ctime(),
        dbutils.write("requests", data)

        await asyncio.sleep(60)
        await original.delete()

    @commands.command(pass_context=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def b(self, ctx):
        '''
        Returns a simplified version of the balance of your funds in the vault (assuming you are a member of the
        specific faction)
        '''

        await ctx.message.delete()

        sender = None
        message = None
        if ctx.message.author.nick is None:
            sender = ctx.message.author.name
        else:
            sender = ctx.message.author.nick

        senderid = get_torn_id(sender)
        sender = remove_torn_id(sender)

        if dbutils.get_user(ctx.message.author.id, "tornid") == "":
            verification = await tornget(ctx, f'https://api.torn.com/user/{senderid}?selections=discord&key=',
                                         self.logger)
            if verification["discord"]["discordID"] != str(ctx.message.author.id) and \
                    verification["discord"]["discordID"] != "":
                embed = discord.Embed()
                embed.title = "Permission Denied"
                embed.description = f'The nickname of {ctx.message.author.name} in {ctx.guild.name} does not reflect ' \
                                    f'the Torn ID and username. Please update the nickname (i.e. through YATA) or add' \
                                    f' your ID to the database via the `?addid` or `addkey` commands (NOTE: the ' \
                                    f'`?addkey` command requires your Torn API key). This interaction has been logged.'
                await ctx.send(embed=embed)
                self.logger.warning(
                    f'{ctx.message.author.id} does not have an accurate nickname, and attempted to withdraw'
                    f' some money from the faction vault.')
                return None

        self.logger.info(f'{sender} is checking their balance in the faction vault.')

        response = await tornget(ctx, "https://api.torn.com/faction/?selections=donations&key=", self.logger)
        response = response["donations"]

        primary_balance = 0
        secondary_balance = 0
        tertiary_balance = 0
        member = False

        for user in response:
            if response[user]["name"] == sender:
                self.logger.info(f'{sender} has {num_to_text(response[user]["money_balance"])} in the faction vault.')

                primary_balance = response[user]["money_balance"]
                member = True
                break

        if dbutils.get_guild(ctx.guild.id, "tornapikey2") == "" and member:
            embed = discord.Embed()
            embed.title = f'Vault Balance for {sender}'
            embed.description = f'Faction vault balance: {num_to_text(primary_balance)}'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()
            return None
        elif dbutils.get_guild(ctx.guild.id, "tornapikey2") == "" and not member:
            self.logger.log(
                f'{sender} who is not a member of any of the stored factions has requested their vault balance.')

            embed = discord.Embed()
            embed.title = "Vault Balance for " + sender
            embed.description = f'{sender} is not a member of any of the stored factions.'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()

        response = await tornget(ctx, "https://api.torn.com/faction/?selections=donations&key=", self.logger, 2)
        response = response['donations']

        for user in response:
            if response[user]["name"] == sender:
                self.logger.info(f'{sender} has {num_to_text(response[user]["money_balance"])} in the secondary faction'
                                 f' vault.')
                secondary_balance = response[user]["money_balance"]
                member = True

        if dbutils.get_guild(ctx.guild.id, "tornapikey3") == "" and member:
            embed = discord.Embed()
            embed.title = f'Vault Balance for {sender}'
            embed.description = f'Faction vault balance: {num_to_text(primary_balance)}'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()
            return None
        elif dbutils.get_guild(ctx.guild.id, "tornapikey3") == "" and not member:
            self.logger.log(
                f'{sender} who is not a member of any of the stored factions has requested their vault balance.')

            embed = discord.Embed()
            embed.title = "Vault Balance for " + sender
            embed.description = f'{sender} is not a member of any of the stored factions.'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()

        response = await tornget(ctx, "https://api.torn.com/faction/?selections=donations&key=", self.logger, 3)
        response = response['donations']

        for user in response:
            if response[user]["name"] == sender:
                self.logger.info(f'{sender} has {num_to_text(response[user]["money_balance"])} in the teritary faction'
                                 f' vault.')
                tertiary_balance = response[user]["money_balance"]
                member = True

        if not member:
            self.logger.log(
                f'{sender} who is not a member of any of the stored factions has requested their vault balance.')

            embed = discord.Embed()
            embed.title = "Vault Balance for " + sender
            embed.description = f'{sender} is not a member of any of the stored factions.'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()
        else:
            embed = discord.Embed()
            embed.title = f'Vault Balance for {sender}'
            embed.description = f'Primary faction vault balance: {num_to_text(primary_balance)}\nSecondary ' \
                                f'faction vault balance: {num_to_text(secondary_balance)}\nTertiary faction vault ' \
                                f'balance: {num_to_text(tertiary_balance)}'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()

    @commands.command(aliases=["balance"], pass_context=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def bal(self, ctx):
        '''
        Returns the exact balance of your funds in the vault (assuming you are a member of the specific faction)
        '''

        await ctx.message.delete()

        sender = None
        message = None
        if ctx.message.author.nick is None:
            sender = ctx.message.author.name
        else:
            sender = ctx.message.author.nick

        senderid = get_torn_id(sender)
        sender = remove_torn_id(sender)

        if dbutils.get_user(ctx.message.author.id, "tornid") == "":
            verification = await tornget(ctx, f'https://api.torn.com/user/{senderid}?selections=discord&key=',
                                         self.logger)
            if verification["discord"]["discordID"] != str(ctx.message.author.id) and \
                    verification["discord"]["discordID"] != "":
                embed = discord.Embed()
                embed.title = "Permission Denied"
                embed.description = f'The nickname of {ctx.message.author.name} in {ctx.guild.name} does not reflect ' \
                                    f'the Torn ID and username. Please update the nickname (i.e. through YATA) or add' \
                                    f' your ID to the database via the `?addid` or `addkey` commands (NOTE: the ' \
                                    f'`?addkey` command requires your Torn API key). This interaction has been logged.'
                await ctx.send(embed=embed)
                self.logger.warning(
                    f'{ctx.message.author.id} does not have an accurate nickname, and attempted to withdraw'
                    f' some money from the faction vault.')
                return None

        self.logger.info(f'{sender} is checking their balance in the faction vault.')

        response = await tornget(ctx, "https://api.torn.com/faction/?selections=donations&key=", self.logger)
        response = response["donations"]

        primary_balance = 0
        secondary_balance = 0
        tertiary_balance = 0
        member = False

        for user in response:
            if response[user]["name"] == sender:
                self.logger.info(f'{sender} has {num_to_text(response[user]["money_balance"])} in the faction vault.')

                primary_balance = response[user]["money_balance"]
                member = True
                break

        if dbutils.get_guild(ctx.guild.id, "tornapikey2") == "" and member:
            embed = discord.Embed()
            embed.title = f'Vault Balance for {sender}'
            embed.description = f'Faction vault balance: {commas(primary_balance)}'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()
            return None
        elif dbutils.get_guild(ctx.guild.id, "tornapikey2") == "" and not member:
            self.logger.log(
                f'{sender} who is not a member of any of the stored factions has requested their vault balance.')

            embed = discord.Embed()
            embed.title = "Vault Balance for " + sender
            embed.description = f'{sender} is not a member of any of the stored factions.'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()

        response = await tornget(ctx, "https://api.torn.com/faction/?selections=donations&key=", self.logger, 2)
        response = response['donations']

        for user in response:
            if response[user]["name"] == sender:
                self.logger.info(f'{sender} has {num_to_text(response[user]["money_balance"])} in the secondary faction'
                                 f' vault.')
                secondary_balance = response[user]["money_balance"]
                member = True

        if dbutils.get_guild(ctx.guild.id, "tornapikey3") == "" and member:
            embed = discord.Embed()
            embed.title = f'Vault Balance for {sender}'
            embed.description = f'Faction vault balance: {commas(primary_balance)}'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()
            return None
        elif dbutils.get_guild(ctx.guild.id, "tornapikey3") == "" and not member:
            self.logger.log(
                f'{sender} who is not a member of any of the stored factions has requested their vault balance.')

            embed = discord.Embed()
            embed.title = "Vault Balance for " + sender
            embed.description = f'{sender} is not a member of any of the stored factions.'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()

        response = await tornget(ctx, "https://api.torn.com/faction/?selections=donations&key=", self.logger, 3)
        response = response['donations']

        for user in response:
            if response[user]["name"] == sender:
                self.logger.info(f'{sender} has {num_to_text(response[user]["money_balance"])} in the teritary faction'
                                 f' vault.')
                tertiary_balance = response[user]["money_balance"]
                member = True

        if not member:
            self.logger.log(
                f'{sender} who is not a member of any of the stored factions has requested their vault balance.')

            embed = discord.Embed()
            embed.title = "Vault Balance for " + sender
            embed.description = f'{sender} is not a member of any of the stored factions.'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()
        else:
            embed = discord.Embed()
            embed.title = f'Vault Balance for {sender}'
            embed.description = f'Primary faction vault balance: {commas(primary_balance)}\nSecondary ' \
                                f'faction vault balance: {commas(secondary_balance)}\nTertiary faction vault ' \
                                f'balance: {commas(tertiary_balance)}'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()
