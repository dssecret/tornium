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
from models.usermodel import UserModel


@login_required
@fac_required
def members(*args, **kwargs):
    fac_members = UserModel.objects(factionid=kwargs['faction'].tid)
    return render_template('faction/members.html', members=fac_members)