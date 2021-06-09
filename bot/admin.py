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


class Admin(commands.Cog):
    def __init__(self, logger, bot, client):
        self.logger = logger
        self.bot = bot
        self.client = client

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def config(self, ctx, arg=None, value=None):
        '''
        Returns the current configuration of the bot
        '''

        if not check_admin(ctx.message.author) and dbutils.get_superuser() != ctx.message.author.id:
            embed = discord.Embed()
            embed.title = "Permission Denied"
            embed.description = f'This command requires {ctx.message.author.name} to be an Administrator. ' \
                                f'This interaction has been logged.'
            await ctx.send(embed=embed)

            self.logger.warning(f'{ctx.message.author.name} has attempted to run config, but is not an Administrator')
            return None

        embed = discord.Embed()

        if not arg:
            embed = None
            page1 = discord.Embed(
                title="Configuration",
                description=f'''Torn API Key: Classified
                Bot Token: Classified
                Prefix: {get_prefix(self.bot, ctx.message)}
                Superuser: {dbutils.get_superuser()}''',
                ).set_footer(text="Page 1/2")
            page2 = discord.Embed(
                title="Configuration: Vault",
                description=f'''Vault Channel: {dbutils.read("vault")[str(ctx.guild.id)]["channel"]}
                Vault Channel 2: {dbutils.read("vault")[str(ctx.guild.id)]["channel2"]}
                Vault Role: {dbutils.read("vault")[str(ctx.guild.id)]["role"]}
                Vault Role 2: {dbutils.read("vault")[str(ctx.guild.id)]["role2"]}
                Banking Channel: {dbutils.read("vault")[str(ctx.guild.id)]["banking"]}'''
            ).set_footer(text="Page 2/2")

            pages = [page1, page2]

            message = await ctx.send(embed=page1)
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
                    if i < 2:
                        i += 1
                        await message.edit(embed=pages[i])
                elif str(reaction) == '⏭':
                    i = 2
                    await message.edit(embed=pages[i])

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                    await message.remove_reaction(reaction, user)
                except:
                    break

            await message.clear_reactions()
        # Configurations that require a value below here
        elif not value:
            embed.title = "Value Error"
            embed.description = "A value must be passed"
        elif arg == "vc":
            for channel in ctx.guild.channels:
                if str(channel.id) != value[2:-1]:
                    continue
                data = dbutils.read("vault")
                data[str(ctx.guild.id)]["channel"] = channel.name
                dbutils.write("vault", data)
                self.logger.info(f'Vault Channel has been set to {data[str(ctx.guild.id)]["channel"]}.')
                embed.title = "Vault Channel"
                embed.description = f'Vault Channel has been set to {data[str(ctx.guild.id)]["channel"]}.'
        elif arg == "vc2":
            for channel in ctx.guild.channels:
                if str(channel.id) != value[2:-1]:
                    continue
                data = dbutils.read("vault")
                data[str(ctx.guild.id)]["channel2"] = channel.name
                dbutils.write("vault", data)
                self.logger.info(f'Vault Channel 2 has been set to {data[str(ctx.guild.id)]["channel2"]}.')
                embed.title = "Vault Channel 2"
                embed.description = f'Vault Channel 2 has been set to {data[str(ctx.guild.id)]["channel2"]}.'
        elif arg == "vc3":
            for channel in ctx.guild.channels:
                if str(channel.id) != value[2:-1]:
                    continue
                data = dbutils.read("vault")
                data[str(ctx.guild.id)]["channel3"] = channel.name
                dbutils.write("vault", data)
                self.logger.info(f'Vault Channel 3 has been set to {data[str(ctx.guild.id)]["channel3"]}.')
                embed.title = "Vault Channel 3"
                embed.description = f'Vault Channel 3 has been set to {data[str(ctx.guild.id)]["channel3"]}.'
        elif arg == "vr":
            for role in ctx.guild.roles:
                if role.mention != value:
                    continue
                data = dbutils.read("vault")
                data[str(ctx.guild.id)]["role"] = str(role.mention)
                dbutils.write("vault", data)
                self.logger.info(f'Vault Role has been set to {data[str(ctx.guild.id)]["role"]}.')
                embed.title = "Vault Role"
                embed.description = f'Vault Role has been set to {data[str(ctx.guild.id)]["role"]}.'
        elif arg == "vr2":
            for role in ctx.guild.roles:
                if role.mention != value:
                    continue
                data = dbutils.read("vault")
                data[str(ctx.guild.id)]["role2"] = str(role.mention)
                dbutils.write("vault", data)
                self.logger.info(f'Vault Role has been set to {data[str(ctx.guild.id)]["role2"]}.')
                embed.title = "Vault Role"
                embed.description = f'Vault Role has been set to {data[str(ctx.guild.id)]["role2"]}.'
        elif arg == "vr3":
            for role in ctx.guild.roles:
                if role.mention != value:
                    continue
                data = dbutils.read("vault")
                data[str(ctx.guild.id)]["role3"] = str(role.mention)
                dbutils.write("vault", data)
                self.logger.info(f'Vault Role has been set to {data[str(ctx.guild.id)]["role3"]}.')
                embed.title = "Vault Role"
                embed.description = f'Vault Role has been set to {data[str(ctx.guild.id)]["role3"]}.'
        elif arg == "prefix":
            data = dbutils.read("guilds")

            for guild in data["guilds"]:
                if guild["id"] == str(ctx.guild.id):
                    guild["prefix"] = str(value)

            dbutils.write("guilds", data)
            self.logger.info(f'Bot Prefix has been set to {value}.')
            embed.title = "Bot Prefix"
            embed.description = f'Bot Prefix has been set to {value}.'
        elif arg == "key":
            data = dbutils.read("guilds")

            for guild in data["guilds"]:
                if guild["id"] == str(ctx.guild.id):
                    guild["tornapikey"] = str(value)

            dbutils.write("guilds", data)
            self.logger.info(f'{ctx.message.author.name} has set the primary Torn API Key.')
            embed.title = "Torn API Key"
            embed.description = f'The Torn API key for the primary faction has been set by {ctx.message.author.name}.'
            await ctx.message.delete()
        elif arg == "key2":
            data = dbutils.read("guilds")

            for guild in data["guilds"]:
                if guild["id"] == str(ctx.guild.id):
                    guild["tornapikey2"] = str(value)

            dbutils.write("guilds", data)
            self.logger.info(f'{ctx.message.author.name} has set the secondary Torn API Key.')
            embed.title = "Torn API Key"
            embed.description = f'The Torn API key for the secondary faction has been set by {ctx.message.author.name}.'
            await ctx.message.delete()
        elif arg == "key3":
            data = dbutils.read("guilds")

            for guild in data["guilds"]:
                if guild["id"] == str(ctx.guild.id):
                    guild["tornapikey3"] = str(value)

            dbutils.write("guilds", data)
            self.logger.info(f'{ctx.message.author.name} has set the secondary Torn API Key.')
            embed.title = "Torn API Key"
            embed.description = f'The Torn API key for the secondary faction has been set by {ctx.message.author.name}.'
            await ctx.message.delete()
        elif arg == "bc":
            for channel in ctx.guild.channels:
                if str(channel.id) != value[2:-1]:
                    continue
                data = dbutils.read("vault")
                data[str(ctx.guild.id)]["banking"] = str(channel.id)
                dbutils.write("vault", data)
                self.logger.info(f'Banking Channel has been set to {data[str(ctx.guild.id)]["banking"]}.')
                embed.title = "Banking Channel"
                embed.description = f'Banking Channel has been set to {channel.name}.'
        elif arg == "bc2":
            for channel in ctx.guild.channels:
                if str(channel.id) != value[2:-1]:
                    continue
                data = dbutils.read("vault")
                data[str(ctx.guild.id)]["banking2"] = str(channel.id)
                dbutils.write("vault", data)
                self.logger.info(f'Banking Channel 2 has been set to {data[str(ctx.guild.id)]["banking2"]}.')
                embed.title = "Banking Channel 2"
                embed.description = f'Banking Channel 2 has been set to {channel.name}.'
        elif arg == "bc3":
            for channel in ctx.guild.channels:
                if str(channel.id) != value[2:-1]:
                    continue
                data = dbutils.read("vault")
                data[str(ctx.guild.id)]["banking3"] = str(channel.id)
                dbutils.write("vault", data)
                self.logger.info(f'Banking Channel 3 has been set to {data[str(ctx.guild.id)]["banking3"]}.')
                embed.title = "Banking Channel 3"
                embed.description = f'Banking Channel 3 has been set to {channel.name}.'
        else:
            embed.title = "Configuration"
            embed.description = "This key is not a valid configuration key."

        if embed is not None:
            await ctx.send(embed=embed)
