import os, sqlite3, sys, pathlib

class SQLite:
    def __init__(self, settingsvariable=False, path=False, filename=None, settings_file=True):
        self.dev_mode = True if 'dev_mode' in sys.argv else False
        self.techdict = {}

        if settings_file:
            self.load_from_these_settings(settingsvariable, path, filename)
        elif filename:
            self.load_without_ini_file(filename)

    def load_without_ini_file(self, filename):
        self.connection = sqlite3.connect(filename)
        self.cursor = self.connection.cursor()

    def error_and_quit(self):
        print(f"error in {os.environ['INI_FILE']}, may be resolved by deleting the file (program will use defaults if settings-file is missing)")
        sys.exit()

    def connection_and_cursor(self, path):
        try:
            self.connection = sqlite3.connect(path)
            self.cursor = self.connection.cursor()
            return True
        except:
            print(f'SQLite couldnt load: {path}')
            return False

    def load_from_these_settings(self, settingsvariable, path, filename):
        with open(os.environ['INI_FILE']) as f:
            cont = f.read().split('\n')
            cont = [x.strip() for x in cont]

        found = [x for x in cont if x.startswith(settingsvariable)]
        if not found:
            with open(os.environ['INI_FILE'], 'w') as f:
                if path:
                    cont.append(f'{settingsvariable} = "{path}"\n')
                elif filename:
                    cont.append(f'{settingsvariable} = "{os.environ["DATABASE_DIR"]}{os.sep}{filename}"\n')
                else:
                    cont.append(f'{settingsvariable} = "{os.environ["DATABASE_DIR"]}{os.sep}{settingsvariable}.sqlite"\n')

                f.write('\n'.join(cont))

            with open(os.environ['INI_FILE']) as f:
                cont = f.read().split('\n')
                cont = [x.strip() for x in cont]

            found = [x for x in cont if x.startswith(settingsvariable)]

        if not found or [x for x in {os.sep, '='} if found[0].find(x) == -1]:
            self.error_and_quit()

        if found and os.sep in found[-1]:
            found = found[-1].split('=')
            found = found[-1].strip().strip('"')

            for i in range(2):
                if os.path.exists(found) and self.connection_and_cursor(found):
                    return True
                else:
                    foundpath = found.split(os.sep)
                    folders = os.sep.join(foundpath[0:-1])
                    if not os.path.exists(folders):
                        try: pathlib.Path(folders).mkdir(parents=True)
                        except PermissionError:
                            found = path if path else found
                            found = f'{os.environ["DATABASE_DIR"]}{os.sep}{filename}' if filename else found
                            found = f'{os.environ["DATABASE_DIR"]}{os.sep}{settingsvariable}.sqlite' if settingsvariable else found
                            print(f'settingsfile points {folders} they cannot be accessed and/or created, trying default database location: {found}')

                    if os.path.exists(folders) and self.connection_and_cursor(found):
                        return True

        self.error_and_quit()

    def empty_insert_query(self, table):
        query = 'PRAGMA table_info("' + str(table,) + '")'
        tables = self.cursor.execute(query)
        tables = [x for x in tables]
        query_part1 = "insert into " + table + " values"
        query_part2 = "(" + ','.join(['?'] * len(tables)) + ")"
        values = [None] * len(tables)

        return query_part1 + query_part2, values

    def get_all_tables_and_columns(self, raw=False):
        rvdict = {}
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = self.cursor.fetchall()

        for table in [x[0] for x in tables if 'sqlite_sequence' not in x]:
            query = 'PRAGMA table_info("' + str(table) + '")'
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            if raw:
                rvdict[table] = tuple(x for x in data)
            else:
                rvdict[table] = tuple(x[1] for x in data)

        return rvdict

    def sqlite_superfunction(self, table, column, type, auto):
        def soft_update():
            data = self.get_all_tables_and_columns()
            if table in data:
                self.techdict[table] = {k:count for count, k in enumerate(data[table])}

        def hard_update(query):
            with self.connection:
                self.cursor.execute(query)

        if table not in self.techdict:
            soft_update()

        if table not in self.techdict:
            hard_update('create table ' + table + auto)
            soft_update()

        if column not in self.techdict[table]:
            hard_update('alter table ' + table + ' add column "' + column + '" ' + type.upper())
            soft_update()

        return self.techdict[table][column]

    def db_sqlite(self, table, column, type='text', auto=' (id INTEGER PRIMARY KEY AUTOINCREMENT)'):
        return self.sqlite_superfunction(table, column, type, auto or "")

    def execute(self, query, values=False, all=False):
        if query.lower().startswith('select'):
            if values:
                self.cursor.execute(query, tuple(values))
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall() if all else self.cursor.fetchone()
        else:
            with self.connection:
                if type(values) == list:
                    self.cursor.executemany(query, values)
                elif values:
                    self.cursor.execute(query, values)
                else:
                    self.cursor.execute(query)

            self.dev_mode_print(query, values)

    def dev_mode_print(self, query, values, hide_bytes=True):
        if not self.dev_mode:
            return

        if values and type(values[0]) == bytes and hide_bytes:
            print('SQLITE execute QUERY:', query, ':::BYTES:::')

        elif type(values) == list and hide_bytes:
            print('SQLITE executemany QUERY:', query, 'LENGHT:', len(values))

        elif type(values) == tuple and hide_bytes:
            proxyvalues = [x for x in values]
            for count in range(len(proxyvalues)):
                if type(proxyvalues[count]) == bytes:
                    proxyvalues[count] = ':::BYTES:::'
            print('SQLITE execute QUERY:', query, proxyvalues)

        else:
            print('SQLITE event QUERY:', query, values)
