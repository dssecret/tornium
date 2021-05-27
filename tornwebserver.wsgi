activate_this = '/var/torn-command/venv/bin/activate_this.py'
with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))

import sys
import os

# os.environ.setdefault("SETTINGSDIR", "/var/torn-command/")

sys.path.insert(0, "/var/torn-command")

from app import app as application