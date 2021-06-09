# This file is part of torn-command.
#
# torn-command is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# torn-command is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with torn-command.  If not, see <https://www.gnu.org/licenses/>.

from flask import Blueprint, render_template


mod = Blueprint('errors', __name__)


@mod.app_errorhandler(400)
def error400(e):
    """
    Returns the 400 error page

    :param e: HTTP error
    """

    return render_template('/errors/400.html'), 400


@mod.app_errorhandler(403)
def error403(e):
    """
    Returns the 403 error page.

    :param e: HTTP error
    """

    return render_template('/errors/403.html'), 403


@mod.app_errorhandler(404)
def error404(e):
    """
    Returns the 404 error page.

    :param e: HTTP error
    """

    return render_template('/errors/404.html'), 404


@mod.app_errorhandler(422)
def error422(e):
    """
    Returns the 422 error page

    :param e: HTTP error
    """

    return render_template('/errors/422.html'), 422


@mod.app_errorhandler(500)
def error500(e):
    """
    Returns the 500 error page

    :param e: HTTP error
    """

    return render_template('/errors/500.html'), 500


@mod.app_errorhandler(501)
def error501(e):
    """
    Returns the 501 error page

    :param e: HTTP error
    """

    return render_template('/errors/501.html'), 501

