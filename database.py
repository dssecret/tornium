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

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from models import settingsmodel

if settingsmodel.is_dev():
    engine = create_engine('sqlite+pysqlite:///data.sql', connect_args={'check_same_thread': False})
else:
    engine = create_engine(f'mysql+pymysql://{settingsmodel.get("settings", "username")}:'
                           f'{settingsmodel.get("settings", "password")}@localhost/Tornium',
                           pool_pre_ping=True, 
                           pool_recycle=3600)

session_local = scoped_session(sessionmaker(autocommit=True, autoflush=False, bind=engine))
base = declarative_base()

from models.factionmodel import FactionModel
from models.servermodel import ServerModel
from models.usermodel import UserModel

base.metadata.create_all(engine)
