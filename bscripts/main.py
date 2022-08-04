from PyQt5                     import QtCore, QtGui, QtWidgets
from bscripts.database_stuff   import DB, sqlite
from bscripts.preset_colors    import *
from bscripts.settings_widgets import EventFilter, HighlightLabel
from bscripts.settings_widgets import HighlightTipLabel, Label, LineEdit
from bscripts.settings_widgets import MovableScrollWidget, SliderWidget
from bscripts.settings_widgets import TipLabel
from bscripts.tricks           import tech as t
from pathlib                   import Path
import os
import screeninfo
import shutil
import sys
import time

pos = t.pos
style = t.style

class CustomStatusBar(Label):
    def __init__(s, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pos(s, height=32)
        style(s, background='rgba(51,51,51,50)', color=WHITE, border='gray', px=1)
        EventFilter(s.main, resize=True, fn=s.position)
        s.dark = time.time() - 1

    def display(s, text="", timer=10, *args, **kwargs):
        s.show()
        s.setText(text)
        t.shrink_label_to_text(s, y_margin=8, x_margin=28, height=True)
        s.position()
        s.dark = time.time() + timer
        s.putaway()

    def putaway(s):
        if time.time() > s.dark:
            s.hide()
        else:
            t.thread(dummy=s.dark - time.time(), master_fn=s.putaway, name='statusbar')

    def position(s):
        pos(s, right=s.main.width(), bottom=s.main.height(), move=[-5, -5])

class FadeLabel(Label):
    def mouseReleaseEvent(s, ev):
        s.close()

def make_fadelabel(s, text='BE CAREFUL NOW!', fontsize=96):
    try: s.fadelabel.close()
    except: pass

    s.fadelabel = FadeLabel(s, center=True, text=text, fontsize=fontsize, background='rgba(10,10,10,220)', color=WHITE)
    pos(s.fadelabel, size=s)

class ToFromLineEdits(LineEdit):
    def textchanged(s, text):
        if os.path.exists(text):
            style(s, color=WHITE)
        else:
            style(s, color=GRAY)
class FromEdit(ToFromLineEdits):
    def textchanged(s, text):
        if os.path.exists(text):
            for i in [s.main.loadbtn]:
                i.activation_toggle(force=True)
            style(s, color=WHITE)
        else:
            for i in [s.main.loadbtn, s.main.copybtn, s.main.deletebtn, s.main.zipbtn]:
                i.activation_toggle(force=False)
            style(s, color=GRAY)
        t.signal_highlight()

class ToEdit(FromEdit):
    """"""
class ZipEdit(ToFromLineEdits):
    """"""

class FileLabel(HighlightLabel):
    def __init__(s, place, included, fullpath, *args, **kwargs):
        super().__init__(place, *args, **kwargs)
        s.setText(str(fullpath))
        s.included = included
        s.hash = t.md5_hash_file(fullpath) if os.path.isfile(fullpath) else False

        if os.path.isfile(fullpath):
            if os.path.getsize(fullpath) / 1000 > 1000:
                text = f"{round(os.path.getsize(fullpath)/1000000, 1)} mb"
            else:
                text = f"{round(os.path.getsize(fullpath)/1000) if round(os.path.getsize(fullpath)/1000) > 0 else 1} kb"

            kwgs = dict(text=text, background=DARKCYAN, right=True, vcenter=True, indent=9)
        else:
            kwgs = dict(text=f"FOLDER", background=GRAY, center=True, fontsize=9)

        s.size = Label(s, border='black', color=BLACK, monospace=True, **kwgs)
        EventFilter(s, resize=True, fn=lambda:pos(s.size, height=s, width=70, sub=8, top=4, right=s, x_margin=5))
        t.highlight_style(s, name='includefile' if included else 'excludefile')

    def mouseReleaseEvent(s, ev):
        fullpath = s.text()
        if s.main.exclude_this_file(fullpath) if s.included else s.main.include_this_file(fullpath):
            s.close()
            s.parent.widgets = [x for x in s.parent.widgets if x != s]

        t.close_and_pop(s.main.deleting.widgets)
        s.main.deletable_files()
        s.main.rearrange_include_and_exclude()
        s.main.visualize_difference()

class DeleteFileLabel(FileLabel):
    def mouseReleaseEvent(s, ev):
        s.parent.widgets = [x for x in s.parent.widgets if x != s]
        for cnt, i in enumerate(s.parent.widgets):
            pos(i, width=s.parent.backplate, height=32, left=2)
            pos(i, width=i, sub=4, top=cnt*i.height())
        s.main.rearrange_include_and_exclude(specific=[s.parent])
        s.close()

class PresetBTN(HighlightLabel):
    def __init__(s, place, *args, **kwargs):
        super().__init__(place, *args, **kwargs)
        store = t.config(s.name)

    def mouseReleaseEvent(s, ev):
        if ev.button() == 1:
            s.load_config()
        elif ev.button() == 2:
            s.store_config()
        else:
            t.save_config(s.name, delete=True)
            s.activation_toggle(force=False)

    def load_config(s):
        store = t.config(s.name)
        def splitsort(string):
            string = string.split()
            string.sort()
            return " ".join(string)

        if store:

            t.save_config('recent', s.name)

            s.main.fromedit.setText(store['source'])
            s.main.toedit.setText(store['destination'])
            s.main.zipedit.setText(store['zipfile'])

            s.main.included_extensions.setText(splitsort(store['incextensions']))
            s.main.included_filenames.setText(splitsort(store['incfiles']))
            s.main.included_foldernames.setText(splitsort(store['incfolders']))

            s.main.excluded_extensions.setText(splitsort(store['excextensions']))
            s.main.excluded_filenames.setText(splitsort(store['excfiles']))
            s.main.excluded_foldernames.setText(splitsort(store['excfolders']))

            s.activation_toggle(force=True)
            [x.activation_toggle(force=False) for x in s.main.presets if x != s]

            s.main.loadbtn.do_loaded_folder()
            t.signal_highlight()

    def store_config(s):
        store = dict(
            source=s.main.fromedit.text(),
            destination=s.main.toedit.text(),
            zipfile=s.main.zipedit.text(),

            incextensions=s.main.included_extensions.text(),
            incfiles=s.main.included_filenames.text(),
            incfolders=s.main.included_foldernames.text(),

            excextensions=s.main.excluded_extensions.text(),
            excfiles=s.main.excluded_filenames.text(),
            excfolders=s.main.excluded_foldernames.text(),
        )
        t.save_config(s.name, store)
        if store['source']:
            s.set_ai_colors(store['source'])
            t.signal_highlight()

class LoadBTN(HighlightLabel):
    def mouseReleaseEvent(s, ev):
        if s.activated:
            s.do_loaded_folder()

    def do_loaded_folder(s):
        s.main.get_files_and_folders()
        if s.main.included.widgets:
            for i in [s.main.copybtn]:
                i.activation_toggle(force=True)
        if s.main.deleting.widgets:
            for i in [s.main.deletebtn]:
                i.activation_toggle(force=True)
        s.main.zipbtn.activation_toggle(force=False)
        s.main.customstatusbar.display(text=f"Proposing: {len([x for x in s.main.included.widgets if os.path.isfile(x.text())])} files")
        t.signal_highlight()

class DeleteBTN(HighlightLabel):
    def mouseReleaseEvent(s, ev):
        if s.activated and s.main.deleting.widgets:
            delete = [x.text() for x in s.main.deleting.widgets]
            delete = [x for x in delete if x not in (y.text() for y in s.main.included.widgets)]
            delete = [x for x in delete if x not in (y.text() for y in s.main.excluded.widgets)]
            folders = [x for x in delete if os.path.isdir(x)]
            files = [x for x in delete if x not in folders]

            if len(delete) >= 10:
                make_fadelabel(s.main, text='BE CAREFUL NOW!')
                return
            else:
                for i in files:

                    try: os.remove(i)
                    except FileNotFoundError:
                        make_fadelabel(s.main, 'FILE NOT FOUND!')
                        return
                    except PermissionError:
                        make_fadelabel(s.main, 'COULD NOT DELETE!')
                        return
                    except:
                        make_fadelabel(s.main, 'A SWAMP THING ERROR HAS OCCURRED FOR:' + i, fontsize=36)
                        return

                    for killed in [x for x in s.main.deleting.widgets if x.text() == i]:
                        s.main.deleting.widgets = [x for x in s.main.deleting.widgets if x != killed]
                        killed.close()

                for i in folders:
                    must_be_empty = []

                    for walk in os.walk(i):
                        must_be_empty += [x for x in walk[1] + walk[2]]

                    if not must_be_empty:
                        try: os.rmdir(i)
                        except FileNotFoundError:
                            make_fadelabel(s.main, 'FILE NOT FOUND!')
                            return
                        except PermissionError:
                            make_fadelabel(s.main, 'COULD NOT DELETE!')
                            return
                        except:
                            make_fadelabel(s.main, 'A SWAMP THING ERROR HAS OCCURRED FOR:\n' + i, fontsize=36)
                            return

                        for killed in [x for x in s.main.deleting.widgets if x.text() == i]:
                            s.main.deleting.widgets = [x for x in s.main.deleting.widgets if x != killed]
                            killed.close()
                    else:
                        make_fadelabel(s.main, 'FOLDER NOT EMTPY!')
                        return

                s.main.customstatusbar.display(text="Successfully deleted listed files and folders")

class StartBTN(HighlightLabel):
    def mouseReleaseEvent(s, ev):

        if s.activated and s.main.included.widgets:

            tofolder = s.main.toedit.text()
            src = [x.text().rstrip(os.sep) for x in s.main.included.widgets]
            dst_startswith = s.main.toedit.text().rstrip(os.sep)
            combo = [dict(source=x, destination=dst_startswith + os.sep + x[len(s.main.fromedit.text()):].strip(os.sep)) for x in src]

            for i in [x for x in combo if os.path.isdir(x['source'])]:
                src = i['source']
                dst = i['destination']

                if os.path.exists(dst) and os.path.isdir(dst):
                    continue
                else:
                    try: Path(dst).mkdir(parents=True, exist_ok=True)
                    except PermissionError:
                        make_fadelabel(s.main, 'COULD MAKE FOLDER:\n' + dst, fontsize=36)
                        return
                    except:
                        make_fadelabel(s.main, 'A SWAMP THING ERROR HAS OCCURRED FOR:\n' + dst, fontsize=36)
                        return
                    finally:
                        if not os.path.exists(dst):
                            try: os.sync()
                            except: pass
                            time.sleep(1)
                        if not os.path.exists(dst):
                            make_fadelabel(s.main, 'A SWAMP THING ERROR HAS OCCURRED WITH:\n' + dst, fontsize=36)
                            return

            for i in [x for x in combo if not os.path.isdir(x['source'])]:

                src = i['source']
                dst = i['destination']

                if os.path.exists(dst) and os.path.isfile(dst):

                    if t.md5_hash_file(src) == t.md5_hash_file(dst):  # carry on, file is unchanged
                        continue

                    try: os.remove(dst)
                    except PermissionError:
                        make_fadelabel(s.main, 'COULD NOT DELETE PRESENT:\n' + dst, fontsize=36)
                        return
                    except:
                        make_fadelabel(s.main, 'A SWAMP THING ERROR HAS OCCURRED FOR:\n' + dst, fontsize=36)
                        return
                    finally:
                        if os.path.exists(dst):
                            try: os.sync()
                            except: pass
                            time.sleep(1)
                        if os.path.exists(dst):
                            make_fadelabel(s.main, 'FILE RESISTING SUFFOCATION:\n' + dst, fontsize=36)
                            return

                if not os.path.exists(dst):
                    try: shutil.copy(src, dst)
                    except PermissionError:
                        make_fadelabel(s.main, 'NO PERMISSION TO COPY!')
                        return
                    except: pass
                    finally:

                        if not os.path.exists(dst):
                            try: os.sync()
                            except: pass
                            time.sleep(1)

                        if os.path.exists(dst):
                            if t.md5_hash_file(src) != t.md5_hash_file(dst):
                                make_fadelabel(s.main, 'A HASH THING ERROR HAS OCCURRED FOR:\n' + dst, fontsize=36)
                                return
                        else:
                            make_fadelabel(s.main, 'COPY FAILED FROM:\n' + src, fontsize=36)
                            return

        s.activation_toggle(force=False)
        s.main.loadbtn.do_loaded_folder()
        s.main.zipbtn.activation_toggle(force=True)
        s.main.customstatusbar.display(text="Successfully copied listed files and folders to given location")

class ZipBTN(HighlightLabel):
    def mouseReleaseEvent(s, ev):
        if s.activated:

            destination = s.main.zipedit.text().strip()

            if os.path.exists(destination):
                try: os.remove(destination)
                except: pass

            folder = destination.split(os.sep)[0:-1]
            folder = os.sep.join(folder)

            if not os.path.isdir(folder):
                Path(folder).mkdir(parents=True, exist_ok=True)
            if not os.path.isdir(folder):
                try: os.sync
                except: pass
                time.sleep(1)
            if not os.path.isdir(folder):
                make_fadelabel(s.main, 'PATHLIB MKDIR FAILED WHEN:\n' + folder, fontsize=36)
                return

            folder = s.main.toedit.text().strip()
            tmpfile = t.tmp_file(destination, delete=True)
            compressed_file = shutil.make_archive(tmpfile, 'zip', folder)

            if not os.path.exists(compressed_file):
                try: os.sync
                except: pass
                time.sleep(1)
            if not os.path.exists(compressed_file):
                make_fadelabel(s.main, 'RANDOM ZIP FUCK-UP:\n' + compressed_file, fontsize=36)
                return

            try: shutil.move(compressed_file, destination)
            except: destination = compressed_file

            s.main.zipedit.setText(destination)
            s.main.customstatusbar.display(text="Successfully created/updated zip-archive")

default_whitelist = dict(
    fileextensions=['py', 'webp', 'png', 'jpg', 'jpeg', 'bmp', 'gif'],
    foldernames=['img'],
    filenames=['requirements.txt'],
)

default_blacklist = dict(
    fileextensions=['pyc'],
    file_startswith=['__'],
    folder_startswith=['__', '.'],
    foldernames=[],
    filenames=['settings.ini'],
)

class Sneaky(QtWidgets.QMainWindow):
    def __init__(s, *args, **kwargs):
        super().__init__(*args, **kwargs)
        s.center_window(factorx=0.5, factory=0.8)
        s.setWindowTitle(os.environ['PROGRAM_NAME'] + ' ' + os.environ['PROGRAM_VERSION'])
        s.customstatusbar = CustomStatusBar(s, main=s, center=True, fontsize=12, monospace=True, bold=True)
        style(s, background='rgb(11,22,33)', color=WHITE)

        s.show()

        s.make_to_from_lineedits()
        s.make_buttons()
        s.make_included_excluded()

        s.make_included_keywords()
        s.make_excluded_keywords()

        s.make_presets_buttons()
        EventFilter(s, resize=True, fn=s.resize_filters)
        t.thread(dummy=True, master_fn=s.resize_filters)

        for i in [x for x in s.presets if x.name == t.config('recent')]:
            t.thread(dummy=True, master_fn=i.load_config)

        t.signal_highlight()

    def make_presets_buttons(s):
        s.presets = []
        for i in range(10):
            thing = PresetBTN(s, name=f'preset_{i}', main=s, qframebox=True)
            store = t.config(thing.name)
            thing.set_ai_colors(store['source']) if store and 'source' in store else None
            s.presets.append(thing)

    def make_included_keywords(s):
        s.included_extensions = LineEdit(s, background='rgba(10,30,10,220)', color='rgb(200,200,200)', fontsize=12)
        s.included_extensions.tiplabel = TipLabel(s.included_extensions, text='FILE EXTENSIONS', autohide=False)
        default_whitelist['fileextensions'].sort()
        s.included_extensions.setText(" ".join(default_whitelist['fileextensions']))

        s.included_filenames = LineEdit(s, background='rgba(10,35,10,220)', color='rgb(200,200,200)', fontsize=12)
        s.included_filenames.tiplabel = TipLabel(s.included_filenames, text='FILE NAMES', autohide=False)
        default_whitelist['filenames'].sort()
        s.included_filenames.setText(" ".join(default_whitelist['filenames']))

        s.included_foldernames = LineEdit(s, background='rgba(10,40,10,220)', color='rgb(200,200,200)', fontsize=12)
        s.included_foldernames.tiplabel = TipLabel(s.included_foldernames, text='FOLDER NAMES', autohide=False)
        default_whitelist['foldernames'].sort()
        s.included_foldernames.setText(" ".join(default_whitelist['foldernames']))

        for i in [s.included_extensions, s.included_filenames, s.included_foldernames]:
            i.bottom = Label(s, background='rgb(150,150,10)')
            i.bottom.lower()

    def make_excluded_keywords(s):
        s.excluded_extensions = LineEdit(s, background='rgba(50,30,10,220)', color='rgb(200,200,200)', fontsize=12)
        s.excluded_extensions.tiplabel = TipLabel(s.excluded_extensions, text='FILE EXTENSIONS', autohide=False)
        default_blacklist['fileextensions'].sort()
        s.excluded_extensions.setText(" ".join(default_blacklist['fileextensions']))

        s.excluded_filenames = LineEdit(s, background='rgba(60,35,10,220)', color='rgb(200,200,200)', fontsize=12)
        s.excluded_filenames.tiplabel = TipLabel(s.excluded_filenames, text='FILE STARTSWITH', autohide=False)
        default_blacklist['file_startswith'].sort()
        s.excluded_filenames.setText(" ".join(default_blacklist['file_startswith']))

        s.excluded_foldernames = LineEdit(s, background='rgba(70,40,10,220)', color='rgb(200,200,200)', fontsize=12)
        s.excluded_foldernames.tiplabel = TipLabel(s.excluded_foldernames, text='FOLDER STARTSWITH', autohide=False)
        default_blacklist['folder_startswith'].sort()
        s.excluded_foldernames.setText(" ".join(default_blacklist['folder_startswith']))

        for i in [s.excluded_extensions, s.excluded_filenames, s.excluded_foldernames]:
            i.bottom = Label(s, background='rgb(150,150,10)')
            i.bottom.lower()

    def make_included_excluded(s):
        s.included = MovableScrollWidget(s, fortified=True, title=dict(text='', height=25), main=s)
        s.excluded = MovableScrollWidget(s, fortified=True, title=dict(text='', height=25), main=s)
        s.deleting = MovableScrollWidget(s, title=dict(text='', height=25), main=s)
        style(s.included.title, background=DARKGREEN, color=WHITE, border='black', px=2)
        style(s.excluded.title, background=DARKGOLDENROD, color=BLACK, border='black', px=2)
        style(s.deleting.title, background=ORANGERED3, color=WHITE, border='black', px=2)

        for count, thing in enumerate([s.included, s.excluded, s.deleting]):
            style(thing.backplate, background=f"rgb({15*count+1},{15*count+1},{15*count+1})")

        for i in [s.included, s.excluded, s.deleting]:

            i.filescountholder = Label(s)

            i.filescount = Label(i.filescountholder, center=True)
            style(i.filescount, background='rgb(201,171,11)', color=BLACK, border='black')
            i.fileslabel = Label(i.filescountholder, center=True, text='FILES', fontsize=8)
            style(i.fileslabel, background='rgb(31,31,31)', color=WHITE, border='black')

            i.folderscountholder = Label(s)

            i.folderscount = Label(i.folderscountholder, center=True)
            style(i.folderscount, background='rgb(201,171,11)', color=BLACK, border='black')
            i.folderslabel = Label(i.folderscountholder, center=True, text='FOLDERS', fontsize=8)
            style(i.folderslabel, background='rgb(31,31,31)', color=WHITE, border='black')

            i.filesizeholder = Label(s)

            i.filessize = Label(i.filesizeholder, center=True)
            style(i.filessize, background='rgb(201,171,11)', color=BLACK, border='black')
            i.sizelabel = Label(i.filesizeholder, center=True, text='SIZE', fontsize=8)
            style(i.sizelabel, background='rgb(31,31,31)', color=WHITE, border='black')

        for i in [s.included.filescount, s.included.folderscount, s.included.filessize]:
            style(i, background='rgb(95,121,11)')

        for i in [s.deleting.filescount, s.deleting.folderscount, s.deleting.filessize]:
            style(i, background='rgb(195,30,0)')

        def deletefollow():
            pos(s.deleting.filescountholder, above=s.deleting, center=[s.deleting, s.deleting], move=[0,8])
            pos(s.deleting.folderscountholder, before=s.deleting.filescountholder, move=[2,0])
            pos(s.deleting.filesizeholder, after=s.deleting.filescountholder, move=[-1,0])
            [x.raise_() for x in (s.deleting.filescountholder, s.deleting.folderscountholder, s.deleting.filesizeholder)]

        EventFilter(s.deleting, move=True, fn=deletefollow)

    def make_to_from_lineedits(s):
        s.fromedit = FromEdit(s, background='rgb(15,15,15)', color=WHITE, fontsize=16, main=s)
        s.fromedit.tiplabel = TipLabel(s.fromedit, text='SOURCE FOLDER', autohide=False)
        s.toedit = ToEdit(s, background='rgb(15,15,15)', color=WHITE, fontsize=16, main=s)
        s.toedit.tiplabel = TipLabel(s.toedit, text='DESTINATION FOLDER', autohide=False)
        s.zipedit = ZipEdit(s, background='rgb(15,15,15)', color=WHITE, fontsize=16, main=s)
        s.zipedit.tiplabel = TipLabel(s.zipedit, text='ZIPFILE OUTPUT', autohide=False)

        [x.setTextMargins(10,0,10,0) for x in (s.fromedit, s.toedit, s.zipedit)]
        [x.textChanged.connect(x.textchanged) for x in (s.fromedit, s.toedit, s.zipedit)]

        for i in [s.fromedit, s.toedit, s.zipedit]:
            i.bottom = Label(s, background='rgb(150,150,10)')
            i.bottom.lower()

    def make_buttons(s):
        s.loadbtn = LoadBTN(s, text='LOAD', center=True, fontsize=14, border='black', px=1, main=s)
        s.copybtn = StartBTN(s, text='COPY', center=True, fontsize=14, border='black', px=1, main=s)
        s.deletebtn = DeleteBTN(s, text='DELETE', center=True, fontsize=14, border='black', px=1, main=s)
        s.zipbtn = ZipBTN(s, text='ZIPFILE', center=True, fontsize=14, border='black', px=1, main=s)

        for i in [s.loadbtn, s.copybtn, s.deletebtn, s.zipbtn]:
            t.highlight_style(i, name='startbtn')
            i.bottom = Label(s, background='rgb(50,150,210)')
            i.bottom.lower()

    def get_files_and_folders(s):
        [t.close_and_pop(x.widgets) for x in (s.included, s.excluded, s.deleting)]

        incfol = [x.lower() for x in s.included_foldernames.text().split()]
        incfil = [x.lower() for x in s.included_filenames.text().split()]
        incext = s.included_extensions.text().split()
        incext = {'.' + x.lower().lstrip('.') for x in incext}

        excfol = [x.lower() for x in s.excluded_foldernames.text().split()]
        excfil = [x.lower() for x in s.excluded_filenames.text().split()]
        excext = [x.lower() for x in s.excluded_extensions.text().split()]
        excext = {'.' + x.lower().lstrip('.') for x in excext}

        folders = []
        for walk in os.walk(s.fromedit.text().rstrip(os.sep)):

            for f in [walk[0] + os.sep + x for x in walk[2]] + [walk[0]]:

                if os.path.isfile(f):
                    if any(x for x in excfol if f.split(os.sep)[-2].lower().startswith(x)):
                        s.exclude_this_file(f)
                    elif any(x for x in excfil if f.split(os.sep)[-1].lower().startswith(x)):
                        s.exclude_this_file(f)
                    elif any(x for x in excext if f.split(os.sep)[-1].lower().endswith(x)):
                        s.exclude_this_file(f)
                    elif any(x for x in incext if f.split(os.sep)[-1].lower().endswith(x)):
                        s.include_this_file(f)
                    elif any(x for x in incfil if f.split(os.sep)[-1].lower().find(x) > -1):
                        s.include_this_file(f)
                    else:
                        s.exclude_this_file(f)
                else:
                    if any(x for x in excfol if f.split(os.sep)[-1].lower().startswith(x)):
                        s.exclude_this_file(f)
                    elif any(x for x in incfol if f.split(os.sep)[-1].lower().find(x) > -1):
                        s.include_this_file(f)
                    else:
                        folders.append(f) if f not in folders else None

        for f in folders:
            if any(x for x in s.included.widgets if x.text().startswith(f)):
                s.include_this_file(f)
            if any(x for x in s.excluded.widgets if x.text().startswith(f)):
                s.exclude_this_file(f)

        s.deletable_files()
        s.rearrange_include_and_exclude()
        s.visualize_difference()

    def deletable_files(s):
        tofolder = s.toedit.text()
        if not os.path.exists(tofolder):
            return

        files = []
        for walk in os.walk(tofolder.rstrip(os.sep)):
            files += [walk[0] + os.sep + x for x in walk[2]] + [walk[0]]

        if files:
            source = [(x.text()[len(s.fromedit.text()):], x) for x in s.included.widgets]
            combo = [(tofolder.rstrip(os.sep) + os.sep + x[0].lstrip(os.sep), x[1]) for x in source]

            for i in [x for x in files if x not in (y[0] for y in combo) and x != s.toedit.text()]:
                s.deletable_this_file(i)

    def visualize_difference(s):
        tofolder = s.toedit.text()
        if not os.path.exists(tofolder):
            return

        source = [(x.text()[len(s.fromedit.text()):], x) for x in s.included.widgets]
        combo = [(tofolder.rstrip(os.sep) + os.sep + x[0].lstrip(os.sep), x[1]) for x in source]

        for i in [x for x in combo if os.path.exists(x[0]) and os.path.isfile(x[0])]:
            thing = i[1]
            if t.md5_hash_file(i[0]) != thing.hash:
                t.highlight_style(thing, name='includefilechanged')
            else:
                t.highlight_style(thing, name='includefileunchanged')

        for i in [x for x in combo if os.path.exists(x[0]) and os.path.isdir(x[0])]:
            t.highlight_style(i[1], name='includefileunchanged')

        t.signal_highlight()

    def rearrange_include_and_exclude(s, specific=[]):
        for thing in specific or [s.included, s.excluded, s.deleting]:

            thing.widgets.sort(key=lambda x:x.text())
            thing.widgets.sort(key=lambda x:x.text().count(os.sep), reverse=True)
            thing.widgets.sort(key=lambda x:os.path.isdir(x.text()), reverse=True)

            for cnt, i in enumerate(thing.widgets):
                pos(i, width=thing.backplate, height=32, left=2)
                pos(i, width=i, sub=4, top=cnt*i.height())
            thing.expand_me(max_bottom=s.height() - 50)

        for i in specific or [s.included, s.excluded, s.deleting]:
            i.filescount.setText(f"{len([x for x in i.widgets if os.path.isfile(x.text())])}")
            i.folderscount.setText(f"{len([x for x in i.widgets if os.path.isdir(x.text())])}")
            size = sum([os.path.getsize(x.text()) for x in i.widgets if os.path.isfile(x.text())])
            i.filessize.setText(f"{round(size / 1000)} kb")

        s.resize_filters()
        t.signal_highlight()

    def include_this_file(s, fullpath):
        if any(x for x in s.included.widgets if x.text() == fullpath):
            return False

        kwgs = dict(fullpath=fullpath, indent=10, included=True, border='black', fontsize=14, main=s)
        l = FileLabel(s.included.backplate, parent=s.included, **kwgs)
        s.included.widgets.append(l)
        return True

    def deletable_this_file(s, fullpath):
        if any(x for x in s.deleting.widgets if x.text() == fullpath):
            return False

        kwgs = dict(fullpath=fullpath, indent=10, included=-1, border='black', fontsize=14, main=s)
        l = DeleteFileLabel(s.deleting.backplate, parent=s.deleting, **kwgs)
        t.highlight_style(l, name='includefiledelete')
        s.deleting.widgets.append(l)
        return True

    def exclude_this_file(s, fullpath):
        if any(x for x in s.excluded.widgets if x.text() == fullpath):
            return False

        kwgs = dict(fullpath=fullpath, indent=10, included=False, border='black', fontsize=14, main=s)
        l = FileLabel(s.excluded.backplate, parent=s.excluded, **kwgs)
        s.excluded.widgets.append(l)
        return True

    def center_window(s, factorx, factory, primary=True):
        monitors = [x for x in screeninfo.get_monitors() if x.is_primary]
        if monitors:
            monitor = monitors[0] if primary or len(monitors) == 1 else monitors[1]

            s.resize(int(monitor.width * factorx), int(monitor.height * factory))

            xrest = monitor.width - s.width()
            yrest = monitor.height - s.height()

            x = 0 if xrest <= 0 else xrest/2
            y = 0 if yrest <= 0 else yrest/2

            s.setGeometry(int(x)+monitor.x, int(y)+monitor.y, s.width(), s.height())

    def resize_filters(s):
        pos(s.fromedit, left=210, top=10, height=40)
        pos(s.fromedit, reach=dict(right=s.width() - 10))
        pos(s.toedit, size=s.fromedit, below=s.fromedit, y_margin=5)
        pos(s.zipedit, size=s.toedit, below=s.toedit, y_margin=5)

        for count, i in enumerate([s.loadbtn, s.deletebtn, s.copybtn, s.zipbtn]):
            pos(i, width=190, height=33, top=s.fromedit, left=10, move=[0, count * 33 + count])

        pos(s.included, below=s.zipbtn, reach=dict(right=s.fromedit), y_margin=10)
        pos(s.included, width=(s.included.width() / 2) - 5)
        pos(s.excluded, after=s.included, x_margin=10)
        pos(s.excluded, reach=dict(right=s.fromedit))

        pos(s.included_extensions, coat=s.included, height=30)
        pos(s.included_filenames, coat=s.included_extensions, below=s.included_extensions, y_margin=3)
        pos(s.included_foldernames, coat=s.included_extensions, below=s.included_filenames, y_margin=3)
        pos(s.included, below=s.included_foldernames, y_margin=40)

        pos(s.excluded_extensions, coat=s.excluded, height=30)
        pos(s.excluded_filenames, coat=s.excluded_extensions, below=s.excluded_extensions, y_margin=3)
        pos(s.excluded_foldernames, coat=s.excluded_extensions, below=s.excluded_filenames, y_margin=3)
        pos(s.excluded, below=s.excluded_foldernames, y_margin=40)

        pos(s.deleting, below=s.excluded, width=s.excluded, y_margin=35)

        for i in [s.included, s.excluded, s.deleting]:
            pos(i.filescountholder, width=100, height=22+16, above=i, center=[i, i], move=[0,8])
            pos(i.fileslabel, width=i.filescountholder, height=16)
            pos(i.filescount, below=i.fileslabel, width=i.filescountholder, height=22)
            i.filescountholder.raise_()

            pos(i.folderscountholder, size=i.filescountholder, before=i.filescountholder, move=[2,0])
            pos(i.folderslabel, width=i.filescountholder, height=16)
            pos(i.folderscount, below=i.folderslabel, width=i.folderscountholder, height=22)
            i.folderscountholder.raise_()

            pos(i.filesizeholder, size=i.filescountholder, after=i.filescountholder, move=[-1,0])
            pos(i.sizelabel, width=i.filescountholder, height=16)
            pos(i.filessize, below=i.sizelabel, width=i.folderscountholder, height=22)
            i.filesizeholder.raise_()

        for i in [s.excluded_extensions, s.excluded_filenames, s.excluded_foldernames, s.fromedit, s.toedit, s.included_extensions, s.included_filenames, s.included_foldernames, s.zipedit, s.loadbtn, s.copybtn, s.deletebtn, s.zipbtn]:
            pos(i.bottom, size=i, left=i, top=i, add=2, move=[-1,-1])

        for count, i in enumerate(s.presets):
            pos(i, size=[15,15], bottom=s.height() - 20, left=20 + (20 * count))
