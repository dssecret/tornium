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

import uuid

from flask import render_template, redirect
from flask_login import login_required

from controllers.faction.decorators import *
from models.factiongroupmodel import FactionGroupModel
from models.factionmodel import FactionModel
import utils


@aa_required
def groups():
    return render_template('faction/groups.html',
                           groups=[utils.first(FactionGroupModel.objects(tid=group)) for group in
                                   utils.first(FactionModel.objects(tid=current_user.factiontid)).groups])


@aa_required
def create_group():
    faction: FactionModel = utils.first(FactionModel.objects(tid=current_user.factiontid))

    if faction is None:
        raise Exception

    group = FactionGroupModel(
        tid=FactionGroupModel.objects.count(),
        name=str(FactionGroupModel.objects.count()),
        creator=current_user.factiontid,
        members=[faction.tid],
        invite=uuid.uuid4().hex
    )
    group.save()

    faction.groups.append(group.tid)
    faction.save()

    return redirect(f'/faction/group/{group.tid}')


@aa_required
def group_invite(invite: str):
    dbgroup: FactionGroupModel = utils.first(FactionGroupModel.objects(invite=invite))
    faction: FactionModel = utils.first(FactionModel.objects(tid=current_user.factiontid))

    if faction is None:
        raise Exception
    elif dbgroup is None:
        raise Exception
    elif dbgroup.tid in faction.groups:
        raise Exception

    dbgroup.members.append(current_user.factiontid)
    dbgroup.save()

    faction.groups.append(dbgroup.tid)
    faction.save()

    return redirect(f'/faction/group/{dbgroup.tid}')


@aa_required
def group(tid: int):
    dbgroup: FactionGroupModel = utils.first(FactionGroupModel.objects(tid=tid))
    faction: FactionModel = utils.first(FactionModel.objects(tid=current_user.factiontid))

    if dbgroup is None:
        raise Exception
    elif faction is None:
        raise Exception

    return render_template('faction/group.html', group=dbgroup,
                           members=[utils.first(FactionModel.objects(tid=int(member))) for member in
                                    dbgroup.members],
                           key=current_user.key,
                           faction=faction)
