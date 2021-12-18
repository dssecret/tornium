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

from flask import render_template, request
from flask_login import login_required

from controllers.faction.decorators import *
from models.faction import Faction
from models.factionmodel import FactionModel
import utils


@aa_required
@login_required
def bot():
    faction = Faction(current_user.factiontid)

    if request.method == 'POST':
        faction_model = utils.first(FactionModel.objects(tid=current_user.factiontid))

        if request.form.get('guildid') is not None:
            try:
                utils.tasks.discordget.call_local(f'guilds/{request.form.get("guildid")}')
            except utils.DiscordError as e:
                return utils.handle_discord_error(str(e))
            except utils.NetworkingError as e:
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code '
                                             f'{utils.remove_str(str(e))}.')
            except Exception as e:
                raise e

            faction.guild = request.form.get('guildid')
            faction_model.guild = request.form.get('guildid')
            faction_model.save()
        elif request.form.get('withdrawal') is not None:
            try:
                channel = utils.tasks.discordget.call_local(f'channels/{request.form.get("withdrawal")}')
            except utils.DiscordError as e:
                return utils.handle_discord_error(str(e))
            except utils.NetworkingError as e:
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code '
                                             f'{utils.remove_str(str(e))}.')
            except Exception as e:
                raise e

            faction_model.vaultconfig['withdrawal'] = int(channel['id'])
            faction_model.save()
        elif request.form.get('banking') is not None:
            try:
                channel = utils.tasks.discordget.call_local(f'channels/{request.form.get("banking")}')
            except utils.DiscordError as e:
                return utils.handle_discord_error(str(e))
            except utils.NetworkingError as e:
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code '
                                             f'{utils.remove_str(str(e))}.')
            except Exception as e:
                raise e

            faction_model.vaultconfig['banking'] = int(channel['id'])
            faction_model.save()
        elif request.form.get('banker') is not None:
            try:
                roles = utils.tasks.discordget.call_local(f'guilds/{faction.guild}/roles')
            except utils.DiscordError as e:
                return utils.handle_discord_error(str(e))
            except utils.NetworkingError as e:
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code '
                                             f'{utils.remove_str(str(e))}.')
            except Exception as e:
                raise e

            for role in roles:  # TODO: Add error message for role not found in server
                if role['id'] == request.form.get('banker'):
                    faction_model.vaultconfig['banker'] = int(request.form.get('banker'))
                    faction_model.save()
        elif (request.form.get('enabled') is not None) ^ (request.form.get('disabled') is not None):
            if request.form.get('enabled') is not None:
                faction_model.config['vault'] = 1
            else:
                faction_model.config['vault'] = 0

            faction_model.save()

    return render_template('faction/bot.html', guildid=faction.guild, vault_config=faction.get_vault_config(),
                           config=faction.get_config())