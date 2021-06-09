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

import datetime
import logging

from flask import render_template

from utils.errors import *
from utils.tornget import *


def get_logger():
    return logging.getLogger("server")


def handle_torn_error(error: int):
    if error == 0:
        return render_template('/errors/error.html', title='Unknown Error',
                               error='The Torn API has returned an unknown error.')
    elif error == 1:
        return render_template('/errors/error.html', title='Empty Key',
                               error='The passed Torn API key was empty (i.e. no Torn API key was passed).')
    elif error == 2:
        return render_template('/errors/error.html', title='Incorrect Key',
                               error='The passed Torn API key was not a valid key.')
    elif error == 5:
        return render_template('/errors/error.html', title='Too Many Requests',
                               error='The passed Torn API key has had more than 100 requests sent to the Torn '
                                     'API server. Please try again in a couple minutes.')
    elif error == 8:
        return render_template('/errors/error.html', title='IP Block',
                               error='The server on which this site is hosted has made more than 2000 API calls '
                                     'this minute has has been temporarily banned by Torn\'s servers for a minute. '
                                     'Please contact the administrators of this site to inform them of this so '
                                     'that changes can be made.')
    elif error == 9:
        return render_template('/errors/error.html', title='API System Disabled',
                               error='Torn\'s API system has been temporarily disabled. Please try again in a '
                                     'couple minutes.')
    elif error == 10:
        return render_template('/errors/error.html', title='Key Owner Fedded',
                               error='The owner of the passed API key has been fedded. Please verify that the '
                                     'inputted API key is correct.')
    elif error == 11:
        return render_template('/errors/error.html', title='Key Change Error',
                               error='You can only change your API key once every 60 seconds.')
    elif error == 13:
        return render_template('/errors/error.html', title='Key Change Error',
                               error='The owner of the passed API key has not been online for more than 7 days. '
                                     'Please verify that the inputted API key is correct.')
    else:
        return render_template('/errors/error.html', title='Miscellaneous Error',
                               error=f'The Torn API has responded with error code {error}')


def now():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
