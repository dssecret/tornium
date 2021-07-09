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
import random
import sys
import time

import discord
from discord.ext import commands

sys.path.append('..')

from bot import botutils
from database import session_local
from models.faction import Faction
from models.factionmodel import FactionModel
from models.server import Server
from models.user import User, DiscordUser


class Vault(commands.Cog):
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger

    @commands.command(aliases=["req", "with", "w"])
    async def withdraw(self, ctx, arg):
        await ctx.message.delete()

        session = session_local()
        server = Server(ctx.message.guild.id)
        user = DiscordUser(ctx.message.author.id, User(random.choice(server.admins)).key)

        if user.tid == 0:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'You are required to be verified officially through the ' \
                                '[official Torn Discord server](https://www.torn.com/discord) before being able to ' \
                                'utilize the banking features of this bot. If you have recently verified, please ' \
                                'wait for a minute or two before trying again.'
            await ctx.send(embed=embed)
            return None

        cash = botutils.text_to_num(arg)
        user = User(user.tid)
        faction = Faction(user.factiontid)
        vault_config = faction.get_vault_config()
        config = faction.get_config()

        if vault_config.get('banking') is None or vault_config.get('banker') is None or config.get('vault') == 0:
            embed = discord.Embed()
            embed.title = 'Server Configuration Required'
            embed.description = f'{ctx.guild.name} needs to be added to {faction.name}\'s bot configuration and to ' \
                                f'the server. Please contact the server administrators to do this via ' \
                                f'[the dashboard](https://torn.deek.sh/].'
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
            request_id = len(faction.withdrawals) + 1

            embed = discord.Embed()
            embed.title = f'Vault Request #{request_id}'
            embed.description = 'Your request has been forwarded to the faction leadership.'
            original = await ctx.send(embed=embed)

            embed = discord.Embed()
            embed.title = f'Vault Request #{request_id}'
            embed.description = f'{user.name} is requesting {arg} from the faction vault. To fulfill this request, ' \
                                f'enter `?f {request_id}` in this channel.'
            message = await channel.send(vault_config['banker'], embed=embed)

            faction.withdrawals.append({
                'id': request_id,
                "amount": cash,
                'requester': user.tid,
                'fulfilled': False,
                'timerequested': time.ctime(),
                'fulfiller': 0,
                'timefulfilled': 0,
                'withdrawalmessage': message.id
            })
            dbfaction = session.query(FactionModel).filter_by(tid=faction.tid).first()
            dbfaction.withdrawals = json.dumps(faction.withdrawals)
            session.flush()

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

        session = session_local()
        server = Server(ctx.message.guild.id)
        user = DiscordUser(ctx.message.author.id, User(random.choice(server.admins)).key)

        if user.tid == 0:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'You are required to be verified officially through the ' \
                                '[official Torn Discord server](https://www.torn.com/discord) before being able to ' \
                                'utilize the banking features of this bot. If you have recently verified, please ' \
                                'wait for a minute or two before trying again.'
            await ctx.send(embed=embed)
            return None

        user = User(user.tid)
        faction = Faction(user.factiontid, key=user.key)
        vault_config = faction.get_vault_config()
        config = faction.get_config()

        if vault_config.get('banking') is None or vault_config.get('banker') is None or config.get('vault') == 0:
            embed = discord.Embed()
            embed.title = 'Server Configuration Required'
            embed.description = f'{ctx.guild.name} needs to be added to {faction.name}\'s bot configuration and to ' \
                                f'the server. Please contact the server administrators to do this via ' \
                                f'[the dashboard](https://torn.deek.sh/).'
            await ctx.send(embed=embed)
            return None

        banking_channel = discord.utils.get(ctx.guild.channels, id=vault_config['banking'])
        withdrawal = faction.withdrawals[int(request) - 1]
        # Message posted in banking channel
        withdrawal_message = await banking_channel.fetch_message(withdrawal['withdrawalmessage'])

        embed = discord.Embed()
        embed.title = withdrawal_message.embeds[0].title
        embed.add_field(name='Original Message', value=withdrawal_message.embeds[0].description.split('.')[0])
        embed.description = f'This request has been fulfilled by {ctx.message.author.name} at {time.ctime()}.'
        await withdrawal_message.edit(embed=embed)

        faction.withdrawals[int(request) - 1]['fulfilled'] = True
        faction.withdrawals[int(request) - 1]['fulfiller'] = user.tid
        faction.withdrawals[int(request) - 1]['timefulfilled'] = time.ctime()
        dbfaction = session.query(FactionModel).filter_by(tid=faction.tid).first()
        dbfaction.withdrawals = json.dumps(faction.withdrawals)
        session.flush()

    @commands.command(pass_context=True, aliases=['balance', 'bal'])
    async def fullbalance(self, ctx):
        await ctx.message.delete()

        server = Server(ctx.message.guild.id)
        user = DiscordUser(ctx.message.author.id, User(random.choice(server.admins)).key)

        if user.tid == 0:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'You are required to be verified officially through the ' \
                                '[official Torn Discord server](https://www.torn.com/discord) before being able to ' \
                                'utilize the banking features of this bot. If you have recently verified, please ' \
                                'wait for a minute or two before trying again.'
            await ctx.send(embed=embed)
            return None

        user = User(user.tid)
        faction = Faction(user.factiontid, user.key)
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
        user = DiscordUser(ctx.message.author.id, User(random.choice(server.admins)).key)

        if user.tid == 0:
            embed = discord.Embed()
            embed.title = 'Requires Verification'
            embed.description = 'You are required to be verified officially through the ' \
                                '[official Torn Discord server](https://www.torn.com/discord) before being able to ' \
                                'utilize the banking features of this bot. If you have recently verified, please ' \
                                'wait for a minute or two before trying again.'
            await ctx.send(embed=embed)
            return None

        user = User(user.tid)
        faction = Faction(user.factiontid, user.key)
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
