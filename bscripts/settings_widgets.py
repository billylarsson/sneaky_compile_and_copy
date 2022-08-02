from PyQt5                  import QtCore, QtGui, QtWidgets
from PyQt5.QtCore           import QEvent, QObject, pyqtSignal
from bscripts.preset_colors import *
from bscripts.tricks        import tech as t
import os, random
import time

pos = t.pos
style = t.style

class EventFilter(QObject):
    event_highjack = pyqtSignal()

    def __init__(self, eventparent, master_fn=None, resize=False, move=False, eventtype=None, fn=None):
        super().__init__(eventparent)
        self.eventtype = QEvent.Resize if resize else QEvent.Move if move else eventtype
        self.master_fn = master_fn or fn
        self._widget = eventparent
        self.widget.installEventFilter(self)
        if self.master_fn:
            self.event_highjack.connect(self.master_fn)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, widget, event) -> bool:
        if widget == self._widget and event.type() == self.eventtype:
            self.event_highjack.emit()
        return super().eventFilter(widget, event)

class GOD:
    def __init__(self,
            name=False,
            inherit_name=False,
            parent=False,
            main=False,
            signal=False,
            autoload=True,
            dieswith=None,
            *args,
            **kwargs
        ):
        self._define_parent(parent)
        self._define_name(name, inherit_name, parent)
        self._define_main(main)
        self._define_signal(signal)
        self._activation(autoload)
        self._dieswith(dieswith)
        super().__init__(*args, **kwargs)

    def _dieswith(self, dieswith):
        if dieswith:
            self._killfilter1 = EventFilter(dieswith, eventtype=QEvent.Close, master_fn=lambda: self.close())
            self._killfilter2 = EventFilter(self, eventtype=QEvent.Close, master_fn=lambda: self._killfilter1.event_highjack.disconnect())

    def _activation(self, autoload):
        if autoload and t.config(self.name):
            self.activated = True
        else:
            self.activated = False

    def activation_toggle(self, force=None):
        if type(force) == bool:
            self.activated = force
        elif self.activated:
            self.activated = False
        else:
            self.activated = True

    def _define_signal(self, signal):
        if signal == True:
            self.signal = t.signals()
        elif 'signal' in dir(signal):
            self.signal = signal.signal

    def _define_main(self, main):
        if main:
            self.main = main

    def _define_parent(self, parent):
        if parent:
            self.parent = parent
        elif 'parent' not in dir(self):
            self.parent = None

    def _define_name(self, name, inherit_name, parent):
        if name:
            self.name = name

        elif 'name' in dir(inherit_name):
            self.name = inherit_name.name

        elif inherit_name and 'name' in dir(parent):
            self.name = parent.name

        elif inherit_name and 'parent' in dir(self) and 'name' in dir(self.parent):
            self.name = self.parent.name

        else:
            self.name = t.md5_hash_string(random=True, under=True)

class LOOKS:
    def __init__(self, *args, **kwargs):
        self(**kwargs)
        self.show()

    def __call__(self,
            center=False,
            left=False,
            right=False,
            top=False,
            bottom=False,
            monospace=False,
            bold=False,
            qframebox=False,
            background=False,
            color=False,
            border=False,
            font=False,
            fontsize=False,
            vcenter=False,
            hcenter=False,
            px=0,
            **kwargs
        ):
        align_tmp = []
        if center:
            align_tmp.append(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        else:
            if vcenter:
                align_tmp.append(QtCore.Qt.AlignVCenter)
            if hcenter:
                align_tmp.append(QtCore.Qt.AlignHCenter)
            if left:
                align_tmp.append(QtCore.Qt.AlignLeft)
            if right:
                align_tmp.append(QtCore.Qt.AlignRight)
            if top:
                align_tmp.append(QtCore.Qt.AlignTop)
            if bottom:
                align_tmp.append(QtCore.Qt.AlignBottom)

        if align_tmp:
            self.setAlignment(align_tmp[0]|align_tmp[1] if len(align_tmp) == 2 else align_tmp[0])

        if qframebox:
            self.setFrameShape(QtWidgets.QFrame.Box)

        if bold:
            my_font = QtGui.QFont()
            my_font.setBold(True)
            self.setFont(my_font)

        if monospace:
            self.setFont(QtGui.QFont('Monospace', QtGui.QFont.Monospace))

        if background or color or border or font or fontsize or px:
            style(self, background=background, border=border, color=color, font=font or fontsize, px=px)


class Label(QtWidgets.QLabel, GOD, LOOKS):
    def __init__(self,
            place,
            *args,
            **kwargs
        ):
        super().__init__(place, *args, **kwargs)
        self.setAttribute(55)  # delete on close

class LineEdit(QtWidgets.QLineEdit, GOD, LOOKS):
    def __init__(self,
            place,
            qframebox=False,
            *args,
            **kwargs
        ):
        super().__init__(place, *args, **kwargs)

class HighlightLabel(Label):

    _signals = []
    _decaylamp_timer = 0
    _decaylamp_runner = False

    def __init__(self,
            place,
            mouse=True,
            signal=False,
            highlight_signal='_global',
            activated_on=None,
            activated_off=None,
            deactivated_on=None,
            deactivated_off=None,
            *args, **kwargs
        ):
        super().__init__(place, signal=False, *args, **kwargs)

        self.setMouseTracking(mouse)
        self.signal = t.signals(highlight_signal)
        self.signal.highlight.connect(self._highlight)
        self._mousepresent = False

        for k,v in {
            'activated_on': activated_on,
            'activated_off': activated_off,
            'deactivated_on': deactivated_on,
            'deactivated_off': deactivated_off}.items():
            if v:
                setattr(self, k, v)
            else:
                t.highlight_style(self, 'globlahighlight', specific=k)

        t.style(self, **self.deactivated_on if self.activated else self.deactivated_off)

    def _highlight(self, string):
        if string == '_' and self._mousepresent:
            return

        elif string == self.name:
            if self.activated:
                t.style(self, **self.activated_on)
            else:
                t.style(self, **self.deactivated_on)
        else:
            if self.activated:
                t.style(self, **self.activated_off)
            else:
                t.style(self, **self.deactivated_off)

    def _highlight_power_saver(self, runner=False, delay=2):
        if HighlightLabel._decaylamp_runner and time.time() > HighlightLabel._decaylamp_timer:
            HighlightLabel._decaylamp_runner = False
            [(self._signals[c].highlight.emit('_'), self._signals.pop(c)) for c in range(len(self._signals)-1,-1,-1)]
        else:
            if not runner:
                HighlightLabel._decaylamp_timer = time.time() + delay
                if self.signal not in self._signals:
                    self._signals.append(self.signal)

            if not HighlightLabel._decaylamp_runner or runner:
                HighlightLabel._decaylamp_runner = True

                delay = HighlightLabel._decaylamp_timer - time.time()
                kwgs = dict(master_fn=self._highlight_power_saver, name='_climate_changer', master_kwargs={'runner':True})
                t.thread(pre_sleep=delay if delay > 0.3 else 0.3, **kwgs)

    def set_ai_colors(self, variable=None, change_to_gray=150, least_max=100):
        rgb = t.random_rgb(variable or str(self.name))
        red, green, blue = rgb[0], rgb[1], rgb[2]

        rgb1 = f'rgb({red if red > 30 else 30},{green if green > 30 else 30},{blue if blue > 30 else 30})'
        rgb2 = f'rgb({red+15 if red > 45 else 45},{green+15 if green > 45 else 45},{blue if blue+15 > 45 else 45})'

        if sum([red, green, blue]) < change_to_gray and max(red, green, blue) < least_max:
            self.deactivated_on = dict(background=rgb2, color=GRAY)
            self.deactivated_off = dict(background=rgb1, color=GRAY)
        else:
            self.deactivated_on = dict(background=rgb2, color=BLACK)
            self.deactivated_off = dict(background=rgb1, color=BLACK)

    def enterEvent(self, ev):
        self._mousepresent = True
        self.signal.highlight.emit(self.name)
        self._highlight_power_saver()

    def leaveEvent(self, a0):
        self._mousepresent = False

class TipLabel(Label):
    def __init__(self, place, background=TRANSPARENT, color=GRAY, x_margin=10, autohide=True, *args, **kwargs):
        super().__init__(place, background=background, color=color, *args, **kwargs)
        self._parent = place

        if 'tiplabel' not in dir(place):
            place.tiplabel = self

        if autohide:
            try: self._parent.textChanged.connect(self._text_changed)
            except AttributeError: pass

        fontsize = t.fontsize(self._parent)
        if fontsize:
            t.style(self, font=fontsize - 4)

        self._eventfilter_resize = EventFilter(place, resize=True, master_fn=self._follow_parent)
        t.shrink_label_to_text(self, x_margin=x_margin) if self.text() else None
        self._follow_parent()

    def _text_changed(self, text):
        if text:
            self.hide()
        else:
            self.show()

    def _follow_parent(self):
        pos(self, height=self._parent, right=self._parent.width() - 1)

class HighlightTipLabel(HighlightLabel, TipLabel):
    def __init__(self, place, *args, **kwargs):
        super().__init__(place, *args, **kwargs)

 # <<======ABOVE:ME=======<{ [               OTHERS              ] ==============================<<
 # >>======================= [        MOVABLESCROLLWIDGET        ] }>============BELOW:ME========>>

class MovableScrollWidget(Label):
    def __init__(self, place, gap=0, toolplate={}, backplate={}, title={}, scrollarea={}, scroller={}, fortified=False, *args, **kwargs):
        super().__init__(place, *args, **kwargs)
        self.fortified = fortified
        self.place = place  # earlier self.parent wich conflicts if parent in kwargs
        self.gap = gap
        self.toolplate = self.ToolPlate(self, parent=self, **toolplate)
        self.title = self.Title(self.toolplate, parent=self, **title)
        self.backplate = self.BackPlate(self, parent=self, **backplate)
        self.scroller = self.ScrollThiney(place, parent=self, dieswith=self, **scroller)
        self.scrollarea = self.ScrollArea(self, **scrollarea)
        self.widgets = []
        self.toolplate.widgets = [self.title]
        self.steady = True
        self._resizeEvent = EventFilter(eventparent=self, eventtype=QEvent.Resize, master_fn=self._resize_to_parent)

    def _resize_to_parent(self):
        if self.steady:
            self.toolplate.take_place()
            self.title.take_place()
            pos(self.backplate, width=self)
            self.scrollarea.take_place()

    def mousePressEvent(self, ev):
        self.old_position = ev.globalPos()
        self.raise_()

    def mouseMoveEvent(self, ev):
        if 'old_position' in dir(self) and not self.fortified:
            delta = QtCore.QPoint(ev.globalPos() - self.old_position)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_position = ev.globalPos()

    class ToolPlate(Label):
        def take_place(self):
            pos(self, height=max(x.geometry().bottom()+1 for x in self.parent.toolplate.widgets), width=self.parent)

    class Title(Label):
        def __init__(self, place, center=True, height=30, *args, **kwargs):
            super().__init__(place, center=center, *args, **kwargs)
            pos(self, height=height)

        def take_place(self):
            pos(self, width=self.parent.toolplate)

    class BackPlate(Label):
        def take_place(self):
            construct = style(self.parent.scrollarea, curious=True)
            if construct and 'base' in construct and 'border:' in construct['base'] and construct['base']['border:']:
                border = int("".join([x for x in construct['base']['border:'] if x.isdigit()]))
            else:
                border = 0

            if self.parent.widgets:
                height = max(x.geometry().bottom()+1 for x in self.parent.widgets)
                pos(self, width=self.parent.scrollarea, height=height, sub=border*2)

            if self.parent.height() - self.parent.toolplate.height() > self.height():
                pos(self, height=self.parent.height() - self.parent.toolplate.height(), sub=border*2)

    class ScrollArea(QtWidgets.QScrollArea):
        def __init__(self, place, *args, **kwargs):
            super().__init__(place, *args, **kwargs)
            self.parent = place
            self.setWidget(self.parent.backplate)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.setFrameShape(QtWidgets.QScrollArea.NoFrame)
            self.setLineWidth(0)
            self.setStyleSheet('background-color:rgba(0,0,0,0);color:rgba(0,0,0,0)')
            self.verticalScrollBar().valueChanged.connect(self.parent.scroller.change_position)
            self.show()

        def take_place(self):
            w = self.parent.width()
            h = self.parent.height() - self.parent.toolplate.height()
            pos(self, size=[w, h], below=self.parent.toolplate)

    def expand_me(self, collapse=False, min_bottom=False, max_bottom=False):
        self.steady = False

        self.toolplate.take_place()
        self.title.take_place()

        if collapse:
            pos(self, height=self.toolplate)
            pos(self.backplate, height=0, width=self, below=self.toolplate)
            pos(self.scrollarea, height=0, width=self, below=self.toolplate)
            self.scroller.hide()
        else:
            if min_bottom:  # uses parent min_bottom isnt a number
                pos(self, reach=dict(bottom=self.place.height() if min_bottom == True else min_bottom))

            elif max_bottom and self.widgets:  # must a number
                bottom = max(x.geometry().bottom() for x in self.widgets) + self.toolplate.height() + self.geometry().top()
                pos(self, reach=dict(bottom=max_bottom if max_bottom < bottom else bottom), y_margin=1)

            elif self.widgets:
                floor =  self.geometry().top() + max(x.geometry().bottom()+1 for x in self.widgets)
                if floor > self.place.height():
                    pos(self, reach=dict(bottom=self.place.height()))
                else:
                    pos(self, height=max(x.geometry().bottom()+1 for x in self.widgets) + self.toolplate.height())
            else:
                pos(self, height=self.toolplate)

            self.organize_children() if self.widgets else None

        self.steady = True

    def organize_children(self):
        self.scrollarea.take_place()
        self.backplate.take_place()
        self.scroller.show_if_needed()
        self.everyone_add_gap()

    def everyone_add_gap(self):
        if self.gap:
            pos(self.scrollarea, below=self.toolplate, y_margin=self.gap)
            pos(self, height=self, add=self.gap)

    class ScrollThiney(Label):
        def __init__(self, place, background=GREEN4, color=BLACK, border='black', px=1, after=True, *args, **kwargs):
            self.old_position, self.holding, self.scroller_offset = None, False, 0
            super().__init__(place, *args, **kwargs)
            self.after = after
            style(self, background=background, color=color, border=border, px=px)
            self.hide()

        def show_if_needed(self):
            floor =  max(x.geometry().bottom() for x in self.parent.widgets) + self.parent.toolplate.height() + self.parent.geometry().top()
            if floor > self.parent.place.height():

                if self.old_position == None:
                    pos(self, size=[7,20])
                    self._eventfilter1 = EventFilter(eventparent=self.parent, eventtype=QEvent.Move, master_fn=self.follow_parent)
                    self._eventfilter2 = EventFilter(eventparent=self.parent, eventtype=QEvent.Resize, master_fn=self.follow_parent)
                    self._eventfilter3 = EventFilter(eventparent=self.parent, eventtype=QEvent.MouseButtonPress, master_fn=self.follow_parent)
                    self.old_position = False
                    self.follow_parent()

                self.show()
            else:
                self.hide()

        def change_position(self, ev):
            if not self.holding and self.parent.scrollarea.verticalScrollBar().maximum() and ev:  # ZeroDivisionError
                top = (self.parent.scrollarea.height() - self.height()) * (ev / self.parent.scrollarea.verticalScrollBar().maximum())
                pos(self, top=self.parent, move=[0,  self.parent.toolplate.height() + top])
                self.scroller_offset = self.geometry().top() - self.parent.geometry().top()
                self.raise_()

        def follow_parent(self, *args, **kwargs):
            if not self.old_position:
                pos(self, after=self.parent, move=[0, self.parent.toolplate.height()], x_margin=-self.width()-2 if not self.after else 0)
            else:
                pos(self, after=self.parent, top=self.parent, move=[0, self.scroller_offset], x_margin=-self.width()-2 if not self.after else 0)

            self.raise_()

        def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
            if not self.old_position:
                self.old_position = ev.globalPos()

            y = self.y() + (QtCore.QPoint(ev.globalPos() - self.old_position)).y()

            top = self.parent.geometry().top() + self.parent.toolplate.height()
            bottom = self.parent.geometry().bottom() - self.height() + self.lineWidth()

            maximum = self.parent.scrollarea.verticalScrollBar().maximum()
            maxpix = self.parent.height() - self.parent.toolplate.height()

            pixels_process = y - top

            if not pixels_process:
                value = 0
            else:
                value = pixels_process / maxpix
                value = int(maximum * value)
                if value > maximum:
                    value = maximum

            self.parent.scrollarea.verticalScrollBar().setValue(value)

            if y >= top and y <= bottom:
                self.move(self.x(), y)
                self.old_position = ev.globalPos()

            self.scroller_offset = self.geometry().top() - self.parent.geometry().top()

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.holding = True
            self.old_position = ev.globalPos()
            if ev.button() == 1:
                self.raise_()

        def mouseReleaseEvent(self, ev):
            self.holding = False

 # <<======ABOVE:ME=======<{ [         MOVABLESCROLLWIDGET       ] ==============================<<
 # >>======================= [              SLIDERS              ] }>============BELOW:ME========>>

class SliderWidget(Label):
    def __init__(
            self,
            place,
            different_states,
            slider={},
            slider_width=False,
            slider_width_factor=False,
            slider_shrink_factor=1,
            snap=True,
            *args, **kwargs
        ):
        """
        :param different_states: list with states (uses len(list) to calculte steps)
        :param slider_width: int (pixels width)
        :param slider_width_factor: float 0.25 (25% of self.width)
        :param slider_shrink: float (0.85 for slightly smaller slider than steps)
        """
        self.steady = False
        super().__init__(place, *args, **kwargs)
        self.slider_width_factor = slider_width_factor
        self.slider_width = slider_width
        self.different_states = different_states
        self.slider_shrink_factor = slider_shrink_factor
        self.slider_rail = self.SliderRail(place=self)
        self.slider = self.Slider(
            place=self,
            name=self.name,
            qframebox=True,
            center=True,
            mouse=True,
            snap=snap,
            parent=self,
            **slider,
        )
        self.slider.different_states = different_states
        self.slider.inrail = self.slider_rail.inrail
        self.steady = True

    class SliderRail(Label):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            t.style(self, background=BLACK)
            self.inrail = Label(place=self)
            t.style(self.inrail, background=GRAY)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        if not self.steady:
            return

        elif self.slider_width_factor:
            width = self.width() / self.slider_width_factor
        elif self.slider_width:
            width = self.slider_width
        else:
            width = self.width() / len(self.different_states)

        t.pos(self.slider, height=self, width=width * self.slider_shrink_factor)
        w = self.width() - (self.slider.width() / 3)
        t.pos(self.slider_rail, height=3, top=self.height() / 2 - 1, width=w, left=self.slider.width()/6)
        self.slider.snap_widget(force=True)
        t.pos(self.slider_rail.inrail, left=1, top=1, width=self.slider.geometry().left(), height=1)

    def mouseMoveEvent(self, ev, *args):
        pass
    def mouseReleaseEvent(self, ev, *args):
        pass
    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        """
        clicking the sliderrail will snap both save that
        state and snap the slider to that position
        """
        for i in range(len(self.different_states)):
            x1 = (self.width() / len(self.different_states)) * i
            x2 = x1 + (self.width() / len(self.different_states))
            if ev.x() >= x1 and ev.x() <= x2:
                self.slider.state = self.different_states[i]
                self.slider.snap_widget(force=True)
                t.save_config(self.slider.name, self.slider.state)
                break

    class Slider(HighlightLabel):
        def __init__(self, snap=True, *args, **kwargs):
            self.hold = False
            self.snap = snap
            super().__init__(*args, **kwargs)

            rv = t.config(self.name, raw=True)
            if rv and rv['value'] != None:
                self.state = rv['value']
            else:
                self.state = self.parent.different_states[0]

        def change_text(self):
            pass

        def snap_widget(self, force=False):
            """
            will adjust the slider so it fits right over the right state
            :param force: overrides non-snapping slider (used for preset)
            """
            if not self.snap and not force:
                return

            if self.state == self.different_states[0]:
                t.pos(self, left=0)
            elif self.state == self.different_states[-1]:
                t.pos(self, right=self.parent.width() - self.lineWidth())
            else:
                for count, i in enumerate(self.different_states):
                    if self.state == i:
                        each = self.parent.width() / len(self.different_states)
                        x1 = each * count
                        x2 = x1 + each
                        if self.width() < each:
                            t.pos(self, center=[x1, x2])
                        else:
                            side = (self.width() - each) / 2
                            t.pos(self, left=x1 - side)
                            if self.geometry().left() < 0:
                                t.pos(self, left=0)
                            elif self.geometry().right() > self.parent.width():
                                t.pos(self, right=self.parent.width() - self.lineWidth())
                        break

            t.pos(self.inrail, width=self.geometry().left())

        def save_state(self):
            """
            if slider is smaller than each state, state is the one that its touches the most (bleed)
            if slider is larger than each state, state is based on what the left side touches
            (self.parent.width() - self.width() since the left side can only reach parent minus self)
            :return:
            """
            each = self.parent.width() / len(self.different_states)
            if self.width() < each:
                for i in range(len(self.different_states)):
                    x1 = each * i
                    x2 = x1 + each
                    bleed = (self.width() * 0.5) + 1
                    if self.geometry().left() >= x1 - bleed and self.geometry().right() <= x2 + bleed:
                        self.state = self.different_states[i]
                        break
            else:
                each = (self.parent.width() - self.width()) / len(self.different_states)
                for i in range(len(self.different_states)):
                    x1 = each * i
                    x2 = x1 + each

                    if self.geometry().left() > x2:
                        continue

                    self.state = self.different_states[i]
                    break

        def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.save_state()
            self.snap_widget()
            self.change_text()
            t.save_config(self.name, self.state)
            self.hold = False

        def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
            if not self.hold:
                self.signal.highlight.emit(self.name)
                return

            delta = QtCore.QPoint(ev.globalPos() - self.old_position)

            if self.x() + delta.x() + self.width() > self.parent.width():
                self.move(self.parent.width() - self.width(), 0)

            elif self.x() + delta.x() < 0:
                self.move(self.x() + 0, 0)

            else:
                self.move(self.x() + delta.x(), 0)

            t.pos(self.inrail, width=self.geometry().left() - self.width() / 6)
            self.old_position = ev.globalPos()

            self.save_state()
            self.change_text()

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.hold = True
            self.old_position = ev.globalPos()

 # <<======ABOVE:ME=======<{ [               SLIDERS             ] ==============================<<
 # >>======================= [            SPAWNSLIDERS           ] }>============BELOW:ME========>>

class SpawnSlider(Label):
    def __init__(self, place, title=False, min_width=10, steps=None, show_beyond=True, left_zero_lock=False, *args, **kwargs):
        """
        :param left_zero_lock, locks the left end of the slider, moving not possible, only resize to the right possible
        """
        super().__init__(place, *args, **kwargs)
        self.show_beyond = show_beyond
        self.left_zero_lock = left_zero_lock
        self.left_press = False
        self.right_press = False
        self.title = title
        self.min_width = min_width
        self.steps = len(steps) if steps else 21
        self.steps_translate = {count:v for count, v in enumerate(steps or [x for x in range(self.steps)])}
        self.incapacitate_thingey()
        EventFilter(eventparent=self.parent, resize=True, master_fn=lambda: pos(self, height=self.parent))

    def incapacitate_thingey(self):
        self.small = None
        self.large = None
        self.setText('')
        self.title.setText('') if self.title else None
        pos(self, width=0)

    def mousePressEvent(self, ev):
        if ev.button() == 2:
            self.incapacitate_thingey()
            return

        self.old_position = ev.globalPos()

        handle = self.width() / 10 if self.width() / 10 > self.min_width / 3 else self.min_width / 3

        if self.left_zero_lock or ev.x() >= self.width() - handle:
            self.right_press = True
            self.left_press = False
        elif ev.x() <= handle and self.geometry().left() >= 0:
            self.left_press = True
            self.right_press = False
        else:
            self.left_press = False
            self.right_press = False

    def mouseDoubleClickEvent(self, a0):
        if a0.button() == 1:
            pos(self, inside=self.parent)
            self.visuals()

    def mouseReleaseEvent(self, ev):
        if self.width() < self.min_width:
            self.incapacitate_thingey()

    def mouseMoveEvent(self, ev):
        if self.right_press or self.left_press:
            self.resize_thingey(ev.x())

        elif 'old_position' in dir(self):
            delta = QtCore.QPoint(ev.globalPos() - self.old_position)
            if self.x() + delta.x() + self.width() >= self.parent.width():
                pos(self, right=self.parent.width()-1)
            else:
                self.move(self.x() + delta.x(), self.y())
            self.old_position = ev.globalPos()

        self.visuals()

    def visuals(self):
        self.thing_inside_parent()
        self.gather_values()
        self.show_beyond_visualization()

    def spawn_thingey(self, x):
        step = self.parent.width() / self.steps if self.parent.width() / self.steps >= self.min_width else self.min_width

        if self.left_zero_lock:
            pos(self, left=0, width=max(step, self.parent.width()/4, x))
        elif self.width() < self.min_width:
            pos(self, left=x-(step / 2), width=max(step, self.parent.width()/4))
        else:
            pos(self, left=x-(self.width()/2))

    def resize_thingey(self, x):
        if self.right_press:
            reach = x+self.geometry().left() if x+self.geometry().left() > 0 else 0
            pos(self, reach=dict(right=reach if reach <= self.parent.width() else self.parent.width()))
        elif self.left_press:
            reach = x+self.geometry().left() if x+self.geometry().left() <= self.parent.width() else self.parent.width()
            pos(self, reach=dict(left=reach if reach >= 0 else 0))

    def thing_inside_parent(self):
        if self.geometry().right() > self.parent.width():
            pos(self, right=self.parent.width()-1)
        elif self.geometry().left() < 0:
            pos(self, left=0)

    def gather_values(self):
        step = self.parent.width() / self.steps
        left = self.geometry().left()
        right = self.geometry().right()

        c = [{'X1': x*step, 'X2': (x*step)+step, 'value': x, 'touch': False} for x in range(0, self.steps)]
        for dd in c:

            if left + (step * 0.43) >= dd['X1'] and left + (step * 0.43) <= dd['X2']:
                dd['touch'] = True
            if right - (step * 0.43) >= dd['X1'] and right - (step * 0.43) <= dd['X2']:
                dd['touch'] = True

        if [x['value'] for x in c if x['touch']]:
            small = min([x['value'] for x in c if x['touch']])
            large = max([x['value'] for x in c if x['touch']])
            self.small, self.large = self.steps_translate[small], self.steps_translate[large]
            self.show_status(self.small, self.large)
        else:
            self.small, self.large = None, None
            self.setText('')
            self.title.setText('') if self.title else None

    def show_status(self, small, large):
        if small == large:
            self.setText(str(small))
            self.title.setText(f"EXACTLY: {str(small)}") if self.title else None
        else:
            self.setText(f"{str(small)} - {str(large)}")
            self.title.setText(f"RANGE: {str(small)} - {str(large)}") if self.title else None

        t.correct_broken_font_size(self, shorten=False, maxsize=20, minsize=6)

    def show_beyond_visualization(self):
        if self.show_beyond:

            for d in [
                {'name': 'right_beyond', 'kwgs': dict(height=self, width=3, right=self.width()-1), 'cond': self.geometry().right() >= self.parent.width()-1},
                {'name': 'left_beyond', 'kwgs': dict(left=0, height=self, width=3), 'cond': self.geometry().left() <= 0},]:

                if d['name'] not in dir(self):
                    setattr(self, d['name'], Label(self, background=GREEN1, color=BLACK, border=BLACK, px=1))
                    getattr(self, d['name']).hide()
                    continue

                label = getattr(self, d['name'])
                label.activation_toggle(force=d['cond'])

                if d['cond']:
                    pos(label, **d['kwgs'])
                    label.show()
                else:
                    label.hide()

class SpawnSliderRail(Label):
    def __init__(self, place, spawnslider=dict(background=ORANGE, border=BLACK, px=1, color=BLACK, center=True, fontsize=7), *args, **kwargs):
        super().__init__(place, *args, **kwargs)
        self.pressed = False
        self.thingey = SpawnSlider(self, parent=self, **spawnslider)
        pos(self.thingey, center=[0,self.width()])
    def mousePressEvent(self, ev):
        self.pressed = ev.x()
        self.grab_child(ev)
    def mouseReleaseEvent(self, ev):
        self.pressed = False
        self.thingey.left_press = False
        self.thingey.right_press = False
    def mouseMoveEvent(self, ev):
        if not self.pressed:
            return
        self.grab_child(ev)
    def grab_child(self, ev):
        self.thingey.spawn_thingey(ev.x())
        self.thingey.visuals()

    def get_beyond_preyond(s):
        preyond = s.thingey.left_beyond.activated if 'left_beyond' in dir(s.thingey) else False
        beyond = s.thingey.right_beyond.activated if 'right_beyond' in dir(s.thingey) else False
        return preyond, beyond
    def get_small_large(s):
        return s.thingey.small, s.thingey.large
    def get_slider_data(s):
        preyond, beyond = s.get_beyond_preyond()
        small, large = s.get_small_large()
        return small, large, preyond, beyond
