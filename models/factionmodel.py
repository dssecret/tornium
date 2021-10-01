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

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.mysql import BIGINT, TEXT, INTEGER, LONGTEXT

from database import base
from models.settingsmodel import is_dev


class FactionModel(base):
    __tablename__ = 'Factions'

    if is_dev():
        tid = Column(Integer, primary_key=True)
        name = Column(String)
        respect = Column(Integer)
        capacity = Column(Integer)
        leader = Column(Integer)
        coleader = Column(Integer)

        keys = Column(String)  # String of list of keys

        last_members = Column(Integer)  # Time of last members update

        withdrawals = Column(String)  # String of list of dictionary of requests

        guild = Column(Integer)  # Guild ID of the faction's guild
        config = Column(String)  # String of dictionary of faction's bot configuration
        vaultconfig = Column(String)  # String of dictionary of vault configuration

        targets = Column(String)  # String of dictionary of targets

        statconfig = Column(String)  # String of dictionary of target config

        chainconfig = Column(String)  # String of dictionary of chain config
        chainod = Column(String)  # String of dictionary of faction member overdoses
    else:
        tid = Column(BIGINT, primary_key=True)
        name = Column(TEXT)
        respect = Column(INTEGER)
        capacity = Column(INTEGER)
        leader = Column(INTEGER)
        coleader = Column(INTEGER)

        keys = Column(TEXT)  # String of list of keys

        last_members = Column(BIGINT)  # Time of last members update

        withdrawals = Column(LONGTEXT)  # String of list of dictionary of requests

        guild = Column(BIGINT)  # Guild ID of the faction's guild
        config = Column(TEXT)  # String of dictionary of faction's bot configuration
        vaultconfig = Column(TEXT)  # String of dictionary of vault configuration

        targets = Column(LONGTEXT)  # String of dictionary of targets

        statconfig = Column(TEXT)  # String of dictionary of target config

        chainconfig = Column(TEXT)  # String of dictionary of chain config
        chainod = Column(TEXT)  # String of dictionary of faction member overdoses
