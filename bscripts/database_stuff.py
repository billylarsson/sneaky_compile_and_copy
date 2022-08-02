from bscripts.sqlite_handler import SQLite
import os, sys

sqlite = SQLite(settingsvariable='local_database', path=os.environ['DATABASE_FILE'])

class DB:  # local database
    class settings:
        config = sqlite.db_sqlite('settings', 'config', 'blob')
