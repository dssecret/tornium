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

from discord.ext import commands
import discord

from required import *
import dbutils

import asyncio


class Moderation(commands.Cog):
    def __init__(self, logger):
        self.logger = logger

    @commands.command(pass_context=True)
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def purge(self, ctx, nummessages: int):
        '''
        Purges specified number of messages in the channel the command is invoked in
        '''

        if not check_admin(ctx.message.author) and dbutils.get_superuser() != ctx.message.author.id:
            embed = discord.Embed()
            embed.title = "Permission Denied"
            embed.description = f'This command requires {ctx.message.author.name} to be an Administrator. ' \
                                f'This interaction has been logged.'
            await ctx.send(embed=embed)

            self.logger.warning(f'{ctx.message.author.name} has attempted to run purge, but is not an Administrator.')
            return None

        await ctx.message.delete()
        await ctx.message.channel.purge(limit=nummessages, check=None, before=None)
        self.logger.info(f'{nummessages} messages in {ctx.message.channel.name} have been purged by '
                         f'{ctx.message.author.mention}.')
        message = await ctx.send(f'{nummessages} messages have been purged by {ctx.message.author.mention}.')
        await asyncio.sleep(30)
        await message.delete()
