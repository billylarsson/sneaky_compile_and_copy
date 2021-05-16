#!/usr/bin/env python3
from PyQt5        import QtWidgets, uic
from PyQt5.Qt     import QObject, QRunnable, QThreadPool
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from functools    import partial
from sqlite3      import Error
import concurrent.futures
import hashlib
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback

if os.path.exists('/home/plutonergy/Documents'):
    sqlite_path = '/home/plutonergy/Documents/sneaky_compiler_v2.sqlite'
else:
    sqlite_path = 'sneaky_compiler_v2.sqlite'

sqliteconnection = sqlite3.connect(sqlite_path)
sqlitecursor = sqliteconnection.cursor()

white_extensions = ['.ui', '.py', '.so', '.pyx', '.zip', '.txt', '.ini']
white_dirs = ['gui', 'img', 'mkm_expansion_data']
black_dirs = ['__pycache__']

global techdict
techdict = {}

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):
    def __init__(self, function):
        super(Worker, self).__init__()
        self.fn = function
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

def sqlite_superfunction(connection, cursor, table, column, type):
    global techdict

    try: return techdict[connection][table][column]
    except KeyError:
        if connection not in techdict:
            techdict.update({connection: {}})
        if table not in techdict[connection]:
            techdict[connection].update({table : {}})

    query_one = 'select * from ' + table
    try: cursor.execute(query_one)
    except Error:

        with connection:
            query_two = 'create table ' + table + ' (id INTEGER PRIMARY KEY AUTOINCREMENT)'
            cursor.execute(query_two)

            if table == 'settings':
                query_three = 'insert into settings values(?)'
                sqlitecursor.execute(query_three, (None,))

    cursor.execute(query_one)

    col_names = cursor.description

    for count, row in enumerate(col_names):
        if row[0] not in techdict[connection][table]:
            techdict[connection][table].update({row[0] : count})

    try: return techdict[connection][table][column]
    except KeyError:
        with connection:
            query = 'alter table ' +  table + ' add column ' + column + ' ' + type.upper()
            cursor.execute(query)

    return len(col_names)

def db_sqlite(table, column, type='text'):
    return sqlite_superfunction(sqliteconnection, sqlitecursor, table, column, type)

class DB: # local database

    location = db_sqlite('local_files', 'location')
    md5 = db_sqlite('local_files', 'md5')

    copy_pyx_files = db_sqlite('settings', 'copy_pyx_files', 'integer')
    copy_ini_files = db_sqlite('settings', 'copy_ini_files', 'integer')
    force_update = db_sqlite('settings', 'force_update', 'integer')
    program_name = db_sqlite('settings', 'program_name')
    presets = db_sqlite('settings', 'presets')
    recent_job = db_sqlite('settings', 'recent_job')

class tech:
    global techdict
    @staticmethod
    def md5_hash(local_path):
        hash_md5 = hashlib.md5()
        with open(local_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    @staticmethod
    def save_setting(setting_column, object):
        """
        updates sqlite settings table with the column and bool or other value from object
        if object is string, that works!
        :param setting_column: string
        :param object: any Qt-object or string
        """
        def update(column, value):
            with sqliteconnection:
                query = f'update settings set {column} = (?) where id is 1'
                sqlitecursor.execute(query, (value,))

        if type(object) == str:
            update(setting_column, object)

        try:
            if object.isChecked():
                update(setting_column, object.isChecked())
            else:
                update(setting_column, object.isChecked())
        except:
            pass

        try:
            if object.currentText():
                update(setting_column, object.currentText())
        except:
            pass

        try:
            if object.toPlainText():
                update(setting_column, object.toPlainText())
        except:
            pass

    @staticmethod
    def retrieve_setting(index):
        """
        :param index: integer
        :return: column
        """
        sqlitecursor.execute('select * from settings where id is 1')
        data = sqlitecursor.fetchone()
        if data:
            return data[index]

    @staticmethod
    def empty_insert_query(cursor, table):
        cursor.execute('PRAGMA table_info("{}")'.format(table,))
        tables = cursor.fetchall()
        query_part1 = "insert into " + table + " values"
        query_part2 = "(" + ','.join(['?']*len(tables)) + ")"
        values = [None] * len(tables)
        return query_part1 + query_part2, values

def create_shared_object(path):
    subprocess.run(['cythonize', '-i', '-3', path])

class main(QtWidgets.QMainWindow):
    def __init__(self):
        super(main, self).__init__()
        uic.loadUi('main_program_v1.ui', self)
        self.move(1200,150)
        self.setStyleSheet('background-color: gray; color: black')
        self.threadpool_main = QThreadPool()
        self.threadpool_status = QThreadPool()
        self.status_bar = self.statusBar()
        self.preset_settings()

        # TRIGGERS >
        self.btn_kill.clicked.connect(self.delete_preset)
        self.btn_save_preset.clicked.connect(self.save_current_job)
        self.btn_start_compile.clicked.connect(self.start_compiling)
        self.check_copy_pyx.clicked.connect(partial(tech.save_setting, 'copy_pyx_files', self.check_copy_pyx))
        self.check_copy_ini.clicked.connect(partial(tech.save_setting, 'copy_ini_files', self.check_copy_ini))
        self.check_force.clicked.connect(partial(tech.save_setting, 'force_update', self.check_force))
        self.combo_name.currentIndexChanged.connect(self.load_preset)
        # TRIGGER <

        self.show()

    def mousePressEvent(self, QMouseEvent):
        self.load_preset()

    def delete_preset(self):
        """
        deletes the current preset from presets
        """
        name = self.combo_name.currentText()
        data = tech.retrieve_setting(DB.presets)

        if data:
            presets = data.split('\n')
            for c in range(len(presets)-1,-1,-1):
                if presets[c].find(name) > -1 and presets[c][0:len(name) +1] == f'{name},':
                    presets.pop(c)
                    break

            values = '\n'.join(presets)
            with sqliteconnection:
                sqlitecursor.execute('update settings set presets = (?) where id is 1', (values,))

    def preset_settings(self):
        """
        set gui according to sqlite settings table
        :return:
        """
        cycle = {
            self.check_force: 'force_update',
            self.combo_name: 'program_name',
            self.check_copy_pyx: 'copy_pyx_files',
            self.check_copy_ini: 'copy_ini_files'
        }

        for widget, string in cycle.items():
            rv = tech.retrieve_setting(getattr(DB, string))
            if rv:
                if rv == True or rv == False:
                    widget.setChecked(rv)

                elif type(rv) == str:
                    try:
                        widget.setCurrentText(rv)
                        continue
                    except:
                        pass

                    try:
                        widget.setPlainText(rv)
                        continue
                    except:
                        pass

        data = tech.retrieve_setting(DB.presets)
        if data:
            presets = data.split('\n')
            saves = []
            for i in presets:
                j = i.split(',')
                saves.append(j[0])
            saves.sort()
            self.combo_name.clear()
            for ii in saves:
                self.combo_name.addItem(ii)

            recent_job = tech.retrieve_setting(DB.recent_job)
            if recent_job:
                for count, ii in enumerate(saves):
                    if recent_job == ii:
                        self.combo_name.setCurrentIndex(count)
                        self.load_preset()

    def load_preset(self):
        """
        looks in sqlitedatabase for the name thats in the combobox and sets the
        data accordingly, its a CSV 0: name, 1: source, 2: destination
        """
        name = self.combo_name.currentText()
        data = tech.retrieve_setting(DB.presets)
        if data:
            presets = data.split('\n')
            for c in range(len(presets)-1,-1,-1):
                if presets[c].find(name) > -1 and presets[c][0:len(name) +1] == f'{name},':
                    this_job = presets[c].split(',')
                    self.te_source.setPlainText(this_job[1])
                    self.te_dest.setPlainText(this_job[2])
                    tech.save_setting('recent_job', name)
                    break

    def delete_and_fresh_copy(self, source_path, new_path):
        """
        deletes tmporary working directory and copies
        the entire tree from source directory here
        :param source_path: string
        :param new_path: string
        """
        if os.path.exists(new_path):
            shutil.rmtree(new_path)
        shutil.copytree(source_path, new_path)

    def find_files_of_interest(self, tmp_dir):
        """
        returns a list of files that was hit from your white_extensions and white_dirs
        meaning all trash files are excluded from the list
        :param tmp_dir: folder as string
        :return: list of files
        """
        save_files = []
        for walk in os.walk(tmp_dir):
            for file in walk[2]:

                current_file = f'{walk[0]}/{file}'
                top_dir = walk[0][walk[0].rfind('/') +1:]


                for ext in white_extensions:
                    if file.lower().find(ext) > -1 and file[-len(ext):len(file)].lower() == ext:
                        save_files.append(current_file)

                for folder in white_dirs:
                    if top_dir == folder and current_file not in save_files:
                        save_files.append(current_file)

        return save_files

    def check_if_file_is_interesting(self, file_or_list_of_files):
        """
        if file_or_list_of_files == str, returns True if file not exists or md5 is changed
        if file_or_list_of_files == list, pops files from the list that is SAME as database
        :param file_or_list_of_files: file as string or list of files
        :return: bool or list
        """
        def quick(file):
            sqlitecursor.execute('select * from local_files where location = (?)', (file,))
            data = sqlitecursor.fetchone()
            if not data:
                return True
            else:
                hash = tech.md5_hash(file)
                if data[DB.md5] != hash:
                    return True

        if type(file_or_list_of_files) == str:

            if self.check_force.isChecked(): # force recompile
                return False

            rv = quick(file_or_list_of_files)
            return rv

        elif type(file_or_list_of_files) == list:

            if self.check_force.isChecked():  # force recompile
                return file_or_list_of_files

            for c in range(len(file_or_list_of_files) - 1, -1, -1):
                if not quick(file_or_list_of_files[c]):
                    file_or_list_of_files.pop(c)

        return file_or_list_of_files

    def save_md5_hashes(self, file_list):
        """
        save all hashes for the current job
        :param file_list:
        """
        query, values = tech.empty_insert_query(sqlitecursor, 'local_files')
        for file in file_list:
            values[DB.location] = file
            values[DB.md5] = tech.md5_hash(file)

            with sqliteconnection:
                sqlitecursor.execute('delete from local_files where location = (?)', (file,))
                sqlitecursor.execute(query, values)

    def determine_which_files_to_be_compiled(self, list_of_files):
        """
        :param list_of_files:
        :return: a list of pyx files
        """
        pyx_files = []
        for i in list_of_files:
            if len(i) > len('.pyx') and i[-len('.pyx'):len(i)].lower() == '.pyx':
                pyx_files.append(i)
        return pyx_files

    def compile_list_of_pyxfiles(self, single_or_list):
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for _, _ in zip(single_or_list, executor.map(create_shared_object, single_or_list)):
                pass

    def delete_unwanted_files_from_tmp_dir(self, all_files, tmp_dir):
        """
        removes all unwanted files first, then removes all unwanted dirs
        :param all_files: list
        :param tmp_dir: string
        """
        for walk in os.walk(tmp_dir):
            for file in walk[2]:
                current_file = f'{walk[0]}/{file}'
                if current_file not in all_files:
                    os.remove(current_file)

        for walk in os.walk(tmp_dir):
            for dir in walk[1]:
                iterdir = f'{walk[0]}/{dir}'
                for walkwalk in os.walk(iterdir):
                    if walkwalk[1] == [] and walkwalk[2] == []:
                        shutil.rmtree(walkwalk[0])

    def remove_ext_files_before_final(self, all_files, ext):
        """
        parameter needed, but asks the gui checkboxes if we keep them
        :param all_files: list
        :param ext: string
        :return: list
        """
        def remover(all_files, ext):
            for c in range(len(all_files)-1,-1,-1):
                if all_files[c].find(ext) > -1 and all_files[c][-len(ext):len(all_files[c])] == ext:
                    all_files.pop(c)

        if not self.check_copy_pyx.isChecked() and ext == '.pyx':
            remover(all_files, ext)

        if not self.check_copy_ini.isChecked() and ext == '.ini':
            remover(all_files, ext)

        return all_files

    def copy_tree(self, source_dir, destination_dir):
        shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)

    def pre_checking(self, source_path, destination_path):
        """
        checks that all paths seems ok
        :param source_path: string
        :param destination_path: string
        :return: bool
        """
        if not os.path.exists(source_path):
            self.status_bar.showMessage('Source path has covid!')
            return False

        if not os.path.exists(destination_path):
            if len(destination_path) < 5:
                self.status_bar.showMessage('Destination path short!')
                return False

            try:
                pathlib.Path(destination_path).mkdir(parents=True)
                if not os.path.exists(destination_path):
                    self.status_bar.showMessage('Destination path shit on floor!')
                    return False

            except:
                self.status_bar.showMessage('Destination path has rabies!')
                return False

        if self.combo_name.currentText().replace(" ", "") == "":
            self.combo_name.setCurrentText('SNEAKY_TMP_FOLDER')

        return True

    def save_current_job(self):
        """
        saves in sqlite a string that later is split('\n') and then split again(',')
        0: name, 1: source, 2: destination
        """
        name = self.combo_name.currentText()
        source_path = self.te_source.toPlainText()
        destination_path = self.te_dest.toPlainText()
        presets = []

        data = tech.retrieve_setting(DB.presets)

        if data:
            presets = data.split('\n')
            for c in range(len(presets)-1,-1,-1):
                if presets[c].find(name) > -1 and presets[c][0:len(name) +1] == f'{name},':
                    presets.pop(c)
                    break

        presets.append(f'{name},{source_path},{destination_path}')
        values = '\n'.join(presets)
        with sqliteconnection:
            sqlitecursor.execute('update settings set presets = (?) where id is 1', (values,))

    def start_compiling(self):
        """
        everything starts here
        """
        source_path = self.te_source.toPlainText()
        destination_path = self.te_dest.toPlainText()

        if not self.pre_checking(source_path, destination_path):
            return

        if os.path.exists('/mnt/ramdisk'):
            tmp_dir = f'/mnt/ramdisk/{self.combo_name.currentText()}'
        else:
            tmp_dir = f'{tempfile.gettempdir()}/{self.combo_name.currentText()}'

        def finished(self):
            complete_files = self.find_files_of_interest(tmp_dir)
            complete_files = self.remove_ext_files_before_final(complete_files, '.pyx')
            complete_files = self.remove_ext_files_before_final(complete_files, '.ini')
            self.delete_unwanted_files_from_tmp_dir(complete_files, tmp_dir)
            self.copy_tree(tmp_dir, destination_path)

            end_time = time.time() - self.start_time
            message = f'Completed in: {round(end_time, 2)}s... {len(complete_files)} has been updated!'
            self.status_bar.showMessage(message)
            self.save_current_job()

        self.start_time = time.time()

        self.delete_and_fresh_copy(source_path, tmp_dir)
        save_files = self.find_files_of_interest(tmp_dir)
        save_files = self.check_if_file_is_interesting(save_files)
        pyx_files = self.determine_which_files_to_be_compiled(save_files)
        self.save_md5_hashes(save_files)

        thread = Worker(partial(self.compile_list_of_pyxfiles, pyx_files))
        thread.signals.finished.connect(partial(finished, self))
        self.threadpool_main.start(thread)


app = QtWidgets.QApplication(sys.argv)
window = main()
app.exec_()