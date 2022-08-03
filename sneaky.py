#!/usr/bin/env python3
PROGRAM = 'Snakeattack'
VERSION = 'v3.2.2'

import os, sys

os.chdir(os.path.realpath(__file__)[0:os.path.realpath(__file__).rfind(os.sep)])
ROOTDIR = os.path.realpath(__file__)[0:os.path.realpath(__file__).rfind(os.sep)]

os.environ['PROGRAM_DIR'] = ROOTDIR
os.environ['PROGRAM_NAME'] = PROGRAM
os.environ['PROGRAM_VERSION'] = VERSION

if os.path.exists('/home/plutonergy/Documents'):
    os.environ['DATABASE_DIR'] = f"/home/plutonergy/Documents/{PROGRAM}"
else:
    os.environ['DATABASE_DIR'] = ROOTDIR

os.environ['DATABASE_FILE'] = f"{os.environ['DATABASE_DIR']}{os.sep}database.sqlite"
if not os.path.exists(os.environ['DATABASE_DIR']):
    os.mkdir(os.environ['DATABASE_DIR'])

if os.path.exists('/mnt/ramdisk'):
    os.environ['TMP_DIR'] = f"/mnt/ramdisk/{PROGRAM.replace(' ', '_')}"
else:
    import tempfile
    os.environ['TMP_DIR'] = f"{tempfile.gettempdir()}{os.sep}{PROGRAM.replace(' ', '_')}"

if os.path.exists(os.environ['TMP_DIR']) and '--clear-cache' in sys.argv:
    import shutil
    shutil.rmtree(os.environ['TMP_DIR'], ignore_errors=True)

if not os.path.exists(os.environ['TMP_DIR']):
    os.mkdir(os.environ['TMP_DIR'])

customini = [x.strip() for x in sys.argv if x.strip().endswith('settings.ini')]
if customini and os.path.exists(customini[0]):
    os.environ['INI_FILE'] = customini[0]
    print(f"using custom inifile: {customini[0]}")
    sys.argv.remove(customini[0])
else:
    os.environ['INI_FILE'] = f"{ROOTDIR}{os.sep}settings.ini"
    if not os.path.exists(os.environ['INI_FILE']):
        f = open(os.environ['INI_FILE'], 'w')
        f.close()

from PyQt5 import QtWidgets
from bscripts.main import Sneaky

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Sneaky()
    app.exec_()