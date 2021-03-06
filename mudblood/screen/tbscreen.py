import termbox
from mudblood import event
from mudblood import linebuffer
from mudblood import modes
from mudblood import screen
from mudblood.screen import modalscreen
from mudblood import keys
from mudblood import colors
from mudblood import map
from mudblood import window
from mudblood import lua

import traceback
import subprocess
import tempfile
import os

termbox.DEFAULT = 0x09

def createScreen(master):
    return TermboxScreen(master)

class TermboxSource(event.AsyncSource):
    def __init__(self, tb):
        self.tb = tb
        super(TermboxSource, self).__init__()

    def poll(self):
        ret = self.tb.peek_event(1000)
        if ret == None:
            return None

        t, ch, key, mod, w, h = ret
        if t == termbox.EVENT_KEY:
            if key == ord('\r'):
                key = ord('\n')

            if ch:
                return event.KeyEvent(ord(ch))
            else:
                return event.KeyEvent(key)
        elif t == termbox.EVENT_RESIZE:
            return event.ResizeEvent(w, h)

class Lua_Screen(lua.LuaExposedObject):
    def __init__(self, luaob, screen):
        super(Lua_Screen, self).__init__(luaob)
        self._screen = screen

    def windowVisible(self, name, value=None):
        if value is None:
            if name == 'main':
                return True
            return (name in self._screen.windows)
        else:
            if name == 'main':
                return

            if value == False and name in self._screen.windows:
                self._screen.windows.remove(name)

            if value == True:
                if name not in self._screen.windows:
                    self._screen.windows.append(name)
                if name not in self._screen.window_sizes:
                    self._screen.window_sizes[name] = 10

    def windowSize(self, name, value=None):
        if value == None:
            if name in self._screen.window_sizes:
                return self._screen.window_sizes[name]
            else:
                return None
        else:
            self._screen.window_sizes[name] = value

    def height(self):
        return self._screen.height

    def width(self):
        return self._screen.width

    def scroll(self, value, name='main'):
        self._screen.moveScroll(name, value)

class TermboxScreen(modalscreen.ModalScreen):
    def __init__(self, master):
        super(TermboxScreen, self).__init__(master)

        self.modeManager.addMode("editor", EditorMode(self))

        # Initialize Termbox
        self.tb = termbox.Termbox()
        self.tb.set_clear_attributes(termbox.DEFAULT, termbox.DEFAULT)

        # Get window size
        self.updateSize(self.tb.width(), self.tb.height())

        # Initialize the main linebuffer
        self.logbuffer = linebuffer.Linebuffer()

        # Create a source for user input
        self.source = TermboxSource(self.tb)
        self.source.start()
        self.source.bind(self.master.drain)

        self.map_visible = False
        self.windows = []
        self.window_sizes = {}

    def getLuaScreen(self, lua):
        return Lua_Screen(lua, self)

    def run(self):
        while True:
            ev = self.nextEvent()

            if ev is None:
                continue

            if isinstance(ev, screen.UpdateScreenEvent):
                self.doUpdate()
            elif isinstance(ev, screen.SizeScreenEvent):
                self.width, self.height = ev.w, ev.h
            elif isinstance(ev, screen.DestroyScreenEvent):
                self.tb.close()
                self.doneEvent()
                break
            elif isinstance(ev, screen.ModeScreenEvent):
                try:
                    self.modeManager.setMode(ev.mode, **ev.args)
                except modes.UnsupportedModeException:
                    self.put(event.LogEvent("Unsupported mode: {}".format(ev.mode), "err"))
            elif isinstance(ev, screen.KeyScreenEvent):
                self.modeManager.key(ev.key)

            self.doneEvent()
    
    def log(self, text):
        self.logbuffer.echo(text)

    def doUpdate(self):
        mainlb = self.master.session.linebuffers['main']

        self.tb.clear()

        # Get Status line
        status = [l for l in self.master.session.userStatus.splitLines()]

        # Draw main linebuffer

        mainarea = self.height - 1 - len(status)

        x = 0
        y = 0

        scroll = self.getScroll('main')

        lines = None
        if scroll > 0:
            fixh = 5
            lines = mainlb.render(self.width, scroll, mainarea - fixh) \
                  + mainlb.render(self.width, 0, fixh) \
                  + [self.master.session.getPromptLine()]
        else:
            lines = mainlb.render(self.width, scroll, mainarea) \
                  + [self.master.session.getPromptLine()]
        if len(lines) < mainarea:
            y += mainarea - len(lines)

        for l in lines:
            x = 0
            for c in l:
                if c[1] == "\t":
                    x += 8 - (x % 8)
                else:
                    if not (ord(c[1]) >= ord(" ") and ord(c[1]) <= ord("~")):
                        continue
                        #self.tb.close()
                        #raise Exception("Non printable char {}. Line is: '{}'".format(ord(c[1]), [ord(x[1]) for x in l]))

                    self.tb.change_cell(x, y, ord(c[1]), c[0][0] | c[0][2], c[0][1])
                    x += 1
            y += 1

        y -= 1

        # Draw Prompts

        if self.modeManager.getMode() == "normal":
            buf = self.normalMode.getBuffer()
            cur = self.normalMode.getCursor()

            start = max(0, cur + x - self.width + 1)

            self.tb.set_cursor(min(self.width-1, x + cur), y)

            if start > 0:
                self.tb.change_cell(x, y, ord('$'), termbox.DEFAULT, termbox.YELLOW)
                x += 1
                start += 1

            end = start + self.width - x - 1

            for c in buf[start:end]:
                self.tb.change_cell(x, y, ord(c), termbox.YELLOW, termbox.DEFAULT)
                x += 1

            if end < len(buf)-2:
                self.tb.change_cell(x, y, ord('$'), termbox.DEFAULT, termbox.YELLOW)

            x = 0
            y += 1
        elif self.modeManager.getMode() == "lua":
            x = 0
            y += 1

            self.tb.change_cell(x, y, ord("\\"), termbox.RED, termbox.DEFAULT)
            x += 1

            self.tb.set_cursor(x + self.luaMode.getCursor(), y)
            for c in self.luaMode.getBuffer():
                self.tb.change_cell(x, y, ord(c), termbox.RED, termbox.DEFAULT)
                x += 1
        elif self.modeManager.getMode() == "prompt":
            x = 0
            y += 1

            sel, cl = self.promptMode.getCompletionInfo()
            if cl != []:
                self.displayCompletionList(x, y, 20, sel, cl)

            x = 0

            for c in self.promptMode.getText():
                self.tb.change_cell(x, y, ord(c), termbox.RED, termbox.DEFAULT)
                x += 1

            self.tb.set_cursor(x + self.promptMode.getCursor(), y)
            for c in self.promptMode.getBuffer():
                self.tb.change_cell(x, y, ord(c), termbox.DEFAULT, termbox.DEFAULT)
                x += 1

        # Status lines
        y = self.height - len(status)
        for statusl in status:
            x = 0
            x += (self.width - len(statusl)) / 2
            if x < 0:
                x = 0
            for c in statusl:
                self.tb.change_cell(x, y, ord(c[1]), c[0][0] | c[0][2], c[0][1])
                x += 1
            y += 1
        
        # WINDOWS

        ratioWhole = 0.0
        for w in self.windows:
            ratioWhole += self.window_sizes[w]

        windowArea = mainarea / 2

        x = 0
        y = 0
        for w in self.windows:
            x = 0

            wh = self.window_sizes[w]
            if w == 'map':
                # TODO: Race condition! Map must be rendered in session thread!
                m = map.AsciiMapRenderer(self.master.session.map).render(self.width, wh)
                for i in range(self.width * wh):
                    self.tb.change_cell(x, y, m[i], colors.DEFAULT, colors.DEFAULT)
                    x += 1
                    if x == self.width:
                        x = 0
                        y += 1
            else:
                lines = []

                if w in self.master.session.linebuffers or w == "log":
                    if w == "log":
                        lb = self.logbuffer
                        scroll = 0
                    else:
                        lb = self.master.session.linebuffers[w]
                        scroll = self.getScroll(w)

                    if scroll > 0:
                        fixh = 5
                        lines = lb.render(self.width, scroll, wh - fixh) \
                              + lb.render(self.width, 0, fixh)
                    else:
                        lines = lb.render(self.width, scroll, wh)
                if len(lines) < wh:
                    for i in range(wh - len(lines)):
                        x = 0
                        while x < self.width:
                            self.tb.change_cell(x, y, ord(' '), termbox.DEFAULT, termbox.DEFAULT)
                            x += 1
                        y += 1

                for l in lines:
                    x = 0
                    for c in l:
                        if c[1] == "\t":
                            x += 8 - (x % 8)
                        else:
                            if not (ord(c[1]) >= ord(" ") and ord(c[1]) <= ord("~")):
                                continue
                                #self.tb.close()
                                #raise Exception("Non printable char {}. Line is: '{}'".format(ord(c[1]), [ord(x[1]) for x in l]))

                            self.tb.change_cell(x, y, ord(c[1]), c[0][0] | c[0][2], c[0][1])
                            x += 1
                    while x < self.width:
                        self.tb.change_cell(x, y, ord(' '), termbox.DEFAULT, termbox.DEFAULT)
                        x += 1
                    y += 1
            x = 0
            while x < self.width:
                self.tb.change_cell(x, y, ord('-'), termbox.DEFAULT, termbox.DEFAULT)
                x += 1
            y += 1
                

        self.tb.present()

    def displayCompletionList(self, x, y, h, sel, cl):
        clw = max([len(i) for i in cl])

        start = 0
        if h > len(cl):
            h = len(cl)
        elif h < len(cl):
            if sel > h / 2:
                start = sel - h / 2
            if sel > len(cl) - h / 2:
                start = len(cl) - h

        y -= h

        i = 0
        for l in range(start, start+h):
            x = 0

            col = termbox.WHITE
            if l == sel:
                col = termbox.CYAN

            for c in cl[l]:
                self.tb.change_cell(x, y, ord(c), termbox.BLACK, col)
                x += 1
            while x < clw:
                self.tb.change_cell(x, y, ord(' '), termbox.BLACK, col)
                x += 1
            y += 1

    def editor(self, content):
        ret = None
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(content.encode('utf8'))
            tmp.flush()

            self.source.stop()
            self.tb.close()

            subprocess.call(["vim", tmp.name])

            self.tb = termbox.Termbox()
            self.source = TermboxSource(self.tb)
            self.source.start()
            self.source.bind(self.master.drain)
            self.tb.set_clear_attributes(termbox.DEFAULT, termbox.DEFAULT)
            self.tb.set_cursor(-1, -1)

            tmp.seek(0)
            ret = tmp.read().decode('utf8')
        return ret

class EditorMode(modes.Mode):
    def __init__(self, screen):
        self.screen = screen

    def onEnter(self, content, callback):
        tname = None
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(content)
            tname = tf.name

        self.screen.source.stop()
        self.screen.tb.close()

        subprocess.call(["/usr/bin/gvim", "--nofork", tname])

        self.screen.tb = termbox.Termbox()
        self.screen.source = TermboxSource(self.screen.tb)
        self.screen.source.start()
        self.screen.source.bind(self.screen.master.drain)
        self.screen.tb.set_clear_attributes(termbox.DEFAULT, termbox.DEFAULT)
        self.screen.tb.set_cursor(-1, -1)

        with open(tname, "r") as tf:
            self.screen.put(event.ModeEvent("normal"))
            self.screen.put(event.CallableEvent(callback, tf.read()))

        os.unlink(tname)
