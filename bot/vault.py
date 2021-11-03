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
import random
import sys
import time

import discord
from discord.ext import commands

sys.path.append('..')

from bot import botutils
from models.faction import Faction
from models.server import Server
from models.user import User
from models.usermodel import UserModel
from models.withdrawalmodel import WithdrawalModel
import utils


class Vault(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger

    @commands.command(aliases=["req", "with", "w", "W", "Withdraw"])
    async def withdraw(self, ctx, arg):
        await ctx.message.delete()

        server = Server(ctx.message.guild.id)
        user = utils.first(UserModel.objects(discord_id=ctx.message.author.id))

        if user.tid == 0:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'You are required to be verified officially through the ' \
                                '[official Torn Discord server](https://www.torn.com/discord) before being able to ' \
                                'utilize the banking features of this bot. If you have recently verified, please ' \
                                'wait for a minute or two before trying again.'
            await ctx.send(embed=embed)
            return None
        elif user is None:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'NYI. Contact tiksan for more details.'
            await ctx.send(embed=embed)
            return None

        cash = botutils.text_to_num(arg)
        user = User(user.tid)
        user.refresh(key=User(random.choice(server.admins)).key)

        if user.factiontid == 0:
            user.refresh(key=User(random.choice(server.admins)).key, force=True)

            if user.factiontid == 0:
                embed = discord.Embed()
                embed.title = 'Faction ID Error'
                embed.description = f'The faction ID of {ctx.message.author.name} is not set regardless of the ' \
                                    f'forced refresh.'
                await ctx.send(embed=embed)
                return None

        faction = Faction(user.factiontid, key=User(random.choice(server.admins)).key)
        vault_config = faction.get_vault_config()
        config = faction.get_config()

        if vault_config.get('banking') == 0 or vault_config.get('banker') == 0 or config.get('vault') == 0:
            embed = discord.Embed()
            embed.title = 'Server Configuration Required'
            embed.description = f'{ctx.guild.name} needs to be added to {faction.name}\'s bot configuration and to ' \
                                f'the server. Please contact the server administrators to do this via ' \
                                f'[the dashboard](https://torn.deek.sh/).'
            await ctx.send(embed=embed)
            return None

        vault_balances = await botutils.tornget(ctx, self.logger, f'faction/?selections=donations', faction.rand_key())

        if str(user.tid) in vault_balances['donations']:
            if cash > vault_balances['donations'][str(user.tid)]['money_balance']:
                embed = discord.Embed()
                embed.title = 'Not Enough Money'
                embed.description = f'You have requested {arg}, but only have ' \
                                    f'{botutils.commas(vault_balances["donations"][str(user.tid)]["money_balance"])} ' \
                                    f'in the vault.'
                message = await ctx.send(embed=embed)
                await asyncio.sleep(30)
                await message.delete()
                return None

            channel = discord.utils.get(ctx.guild.channels, id=vault_config['banking'])
            request_id = WithdrawalModel.objects().count()

            embed = discord.Embed()
            embed.title = f'Vault Request #{request_id}'
            embed.description = 'Your request has been forwarded to the faction leadership.'
            original = await ctx.send(embed=embed)

            embed = discord.Embed()
            embed.title = f'Vault Request #{request_id}'
            embed.description = f'{user.name if user.name != "" else ctx.message.author.nick} is requesting {arg} ' \
                                f'from the faction vault. To fulfill this request, ' \
                                f'enter `?f {request_id}` in this channel.'
            message = await channel.send(f'<@&{vault_config["banker"]}>', embed=embed)

            withdrawal = WithdrawalModel(
                wid=request_id,
                amount=cash,
                requester=user.tid,
                factiontid=user.factiontid,
                time_requested=utils.now(),
                fulfiller=0,
                time_fulfilled=0,
                withdrawal_message=message.id
            )
            withdrawal.save()
            await asyncio.sleep(30)
            await original.delete()
        else:
            embed = discord.Embed()
            embed.title = 'Money Request Failed'
            embed.description = 'You are not a member of any stored factions. This requires your faction leadership ' \
                                'to set up banking.'
            message = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await message.delete()

    @commands.command(aliases=['f'])
    async def fulfill(self, ctx, request):
        await ctx.message.delete()

        server = Server(ctx.message.guild.id)
        user = utils.first(UserModel.objects(discord_id=ctx.message.author.id))

        if user.tid == 0:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'You are required to be verified officially through the ' \
                                '[official Torn Discord server](https://www.torn.com/discord) before being able to ' \
                                'utilize the banking features of this bot. If you have recently verified, please ' \
                                'wait for a minute or two before trying again.'
            await ctx.send(embed=embed)
            return None
        elif user is None:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'NYI. Contact tiksan for more details.'
            await ctx.send(embed=embed)
            return None

        user = User(user.tid)
        user.refresh(key=User(random.choice(server.admins)).key)

        if user.factiontid == 0:
            user.refresh(key=User(random.choice(server.admins)).key, force=True)

            if user.factiontid == 0:
                embed = discord.Embed()
                embed.title = 'Faction ID Error'
                embed.description = f'The faction ID of {ctx.message.author.name} is not set regardless of the ' \
                                    f'forced refresh.'
                await ctx.send(embed=embed)
                return None

        faction = Faction(user.factiontid, key=User(random.choice(server.admins)).key)
        vault_config = faction.get_vault_config()
        config = faction.get_config()

        if vault_config.get('banking') == 0 or vault_config.get('banker') == 0 or config.get('vault') == 0:
            embed = discord.Embed()
            embed.title = 'Server Configuration Required'
            embed.description = f'{ctx.guild.name} needs to be added to {faction.name}\'s bot configuration and to ' \
                                f'the server. Please contact the server administrators to do this via ' \
                                f'[the dashboard](https://torn.deek.sh/).'
            await ctx.send(embed=embed)
            return None

        banking_channel = discord.utils.get(ctx.guild.channels, id=vault_config['banking'])
        withdrawal = utils.first(WithdrawalModel.objects(wid=int(request)))

        if withdrawal is None:
            embed = discord.Embed()
            embed.title = 'Request Does not Exist'
            embed.description = f'Vault Request #{request} does not currently exist. Please verify that you entered ' \
                                f'the curred vault request ID.'
            await ctx.send(embed=embed)
            return None

        # Message posted in banking channel
        withdrawal_message = await banking_channel.fetch_message(withdrawal['withdrawalmessage'])

        if withdrawal['fulfiller'] == 0:
            embed = discord.Embed()
            embed.title = 'Request Already Fulfilled'
            embed.description = f'Vault request #{request} has already been fulfilled by ' \
                                f'{User(withdrawal["fulfiller"]).name} at ' \
                                f'{withdrawal["timefulfilled"]}.'
            await ctx.send(embed=embed)
            return None

        embed = discord.Embed()
        embed.title = withdrawal_message.embeds[0].title
        embed.add_field(name='Original Message', value=withdrawal_message.embeds[0].description)
        embed.description = f'This request has been fulfilled by {ctx.message.author.name} at {time.ctime()}.'
        await withdrawal_message.edit(embed=embed)

        withdrawal.fulfiller = user.tid
        withdrawal.timefulfilled = utils.now()
        withdrawal.save()

    @commands.command(pass_context=True, aliases=['balance', 'bal'])
    async def fullbalance(self, ctx):
        await ctx.message.delete()

        server = Server(ctx.message.guild.id)
        user = utils.first(UserModel.objects(discord_id=ctx.message.author.id))

        if user.tid == 0:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'You are required to be verified officially through the ' \
                                '[official Torn Discord server](https://www.torn.com/discord) before being able to ' \
                                'utilize the banking features of this bot. If you have recently verified, please ' \
                                'wait for a minute or two before trying again.'
            await ctx.send(embed=embed)
            return None
        elif user is None:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'NYI. Contact tiksan for more details.'
            await ctx.send(embed=embed)
            return None

        user = User(user.tid)
        user.refresh(key=User(random.choice(server.admins)).key)

        if user.factiontid == 0:
            user.refresh(key=User(random.choice(server.admins)).key, force=True)

            if user.factiontid == 0:
                embed = discord.Embed()
                embed.title = 'Faction ID Error'
                embed.description = f'The faction ID of {ctx.message.author.name} is not set regardless of the ' \
                                    f'forced refresh.'
                await ctx.send(embed=embed)
                return None

        faction = Faction(user.factiontid, key=User(random.choice(server.admins)).key)
        config = faction.get_config()

        if config.get('vault') == 0:
            embed = discord.Embed()
            embed.title = 'Server Configuration Required'
            embed.description = f'{ctx.guild.name} needs to be added to {faction.name}\'s bot configuration and to ' \
                                f'the server. Please contact the server administrators to do this via ' \
                                f'[the dashboard](https://torn.deek.sh/).'
            await ctx.send(embed=embed)
            return None

        faction_balances = (await botutils.tornget(ctx, self.logger,
                                                   'faction/?selections=donations',
                                                   faction.rand_key()))['donations']

        if str(user.tid) not in faction_balances:
            embed = discord.Embed()
            embed.title = 'Error'
            embed.description = f'{user.name} is not in {faction.name}\'s donations list according to the Torn API. ' \
                                f'If you think that this is an error, please report this to the developers of this bot.'
            await ctx.send(embed=embed)
            return None

        embed = discord.Embed()
        embed.title = f'Value Balance of {user.name if user.name != "" else ctx.message.author.name}'
        embed.description = f'{user.name if user.name != "" else ctx.message.author.name} has ' \
                            f'{botutils.commas(faction_balances[str(user.tid)]["money_balance"])} in ' \
                            f'{faction.name}\'s vault.'
        message = await ctx.send(embed=embed)
        await asyncio.sleep(30)
        await message.delete()

    @commands.command(pass_context=True, aliases=['b'])
    async def simplebalance(self, ctx):
        await ctx.message.delete()

        server = Server(ctx.message.guild.id)
        user = utils.first(UserModel.objects(discord_id=ctx.message.author.id))

        if user.tid == 0:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'You are required to be verified officially through the ' \
                                '[official Torn Discord server](https://www.torn.com/discord) before being able to ' \
                                'utilize the banking features of this bot. If you have recently verified, please ' \
                                'wait for a minute or two before trying again.'
            await ctx.send(embed=embed)
            return None
        elif user is None:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'NYI. Contact tiksan for more details.'
            await ctx.send(embed=embed)
            return None

        user = User(user.tid)
        user.refresh(key=User(random.choice(server.admins)).key)

        if user.factiontid == 0:
            user.refresh(key=User(random.choice(server.admins)).key, force=True)

            if user.factiontid == 0:
                embed = discord.Embed()
                embed.title = 'Faction ID Error'
                embed.description = f'The faction ID of {ctx.message.author.name} is not set regardless of the ' \
                                    f'forced refresh.'
                await ctx.send(embed=embed)
                return None

        faction = Faction(user.factiontid, key=User(random.choice(server.admins)).key)
        config = faction.get_config()

        if config.get('vault') == 0:
            embed = discord.Embed()
            embed.title = 'Server Configuration Required'
            embed.description = f'{ctx.guild.name} needs to be added to {faction.name}\'s bot configuration and to ' \
                                f'the server. Please contact the server administrators to do this via ' \
                                f'[the dashboard](https://torn.deek.sh/).'
            await ctx.send(embed=embed)
            return None

        faction_balances = (await botutils.tornget(ctx, self.logger,
                                                   'faction/?selections=donations',
                                                   faction.rand_key()))['donations']

        if str(user.tid) not in faction_balances:
            embed = discord.Embed()
            embed.title = 'Error'
            embed.description = f'{user.name} is not in {faction.name}\'s donations list according to the Torn API. ' \
                                f'If you think that this is an error, please report this to the developers of this bot.'
            await ctx.send(embed=embed)
            return None

        embed = discord.Embed()
        embed.title = f'Value Balance of {user.name if user.name != "" else ctx.message.author.name}'

        embed.description = f'{user.name if user.name != "" else ctx.message.author.name} has ' \
                            f'{botutils.num_to_text(faction_balances[str(user.tid)]["money_balance"])} in ' \
                            f'{faction.name}\'s vault.'
        message = await ctx.send(embed=embed)
        await asyncio.sleep(30)
        await message.delete()
