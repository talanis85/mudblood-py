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

import subprocess
import tempfile

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

class TermboxScreen(modalscreen.ModalScreen):
    def __init__(self, master):
        super(TermboxScreen, self).__init__(master)

        # Initialize Termbox
        self.tb = termbox.Termbox()
        self.tb.set_clear_attributes(termbox.DEFAULT, termbox.DEFAULT)

        # Get window size
        self.updateSize(self.tb.width(), self.tb.height())

        # Initialize the main linebuffer
        self.console = window.LinebufferWindow(linebuffer.Linebuffer())

        # Create a source for user input
        self.source = TermboxSource(self.tb)
        self.source.start()
        self.source.bind(self.master.drain)

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
                self.modeManager.setMode(ev.mode, **ev.args)
            elif isinstance(ev, screen.KeyScreenEvent):
                self.modeManager.key(ev.key)

            self.doneEvent()
    
    def log(self, text):
        self.console.linebuffer.echo(text)

    def doUpdate(self):
        x = 0
        y = 0

        windowArea = self.height - 2

        windows = None

        # Draw session windows
        # If in consoleMode, draw mudblood windows

        if self.modeManager.getMode() == "console":
            windows = [self.console]
        else:
            windows = self.master.session.windows

        self.tb.clear()

        ratioWhole = 0.0
        for w in windows:
            if w.visible:
                ratioWhole += w.ratio

        for w in reversed(windows):
            if w.visible:
                wh = int(windowArea * (w.ratio / ratioWhole))

                if w.type == "linebuffer":
                    if w.scroll > 0:
                        fixh = 5
                        lines = w.linebuffer.render(self.width, w.scroll, wh - fixh) \
                              + w.linebuffer.render(self.width, 0, fixh) \
                              + [self.master.session.getPromptLine()]
                    else:
                        lines = w.linebuffer.render(self.width, w.scroll, wh) \
                              + [self.master.session.getPromptLine()]
                    if len(lines) < wh:
                        y += wh - len(lines)

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
                elif w.type == "map":
                    m = map.AsciiMapRenderer(w.map).render(self.width, wh)
                    for i in range(self.width * wh):
                        self.tb.change_cell(x, y, m[i], colors.DEFAULT, colors.DEFAULT)
                        x += 1
                        if x == self.width:
                            x = 0
                            y += 1

        y -= 1

        # Prompt line
        if self.modeManager.getMode() == "normal":
            self.tb.set_cursor(x + self.normalMode.getCursor(), y)
            for c in self.normalMode.getBuffer():
                self.tb.change_cell(x, y, ord(c), termbox.YELLOW, termbox.DEFAULT)
                x += 1
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

            for c in self.promptMode.getText():
                self.tb.change_cell(x, y, ord(c), termbox.RED, termbox.DEFAULT)
                x += 1

            self.tb.set_cursor(x + self.promptMode.getCursor(), y)
            for c in self.promptMode.getBuffer():
                self.tb.change_cell(x, y, ord(c), termbox.DEFAULT, termbox.DEFAULT)
                x += 1

        # System status
        x = self.width - 1
        for c in reversed(self.master.session.getStatusLine()):
            self.tb.change_cell(x, y, ord(c), termbox.DEFAULT, termbox.DEFAULT)
            x -= 1

        # Status line
        x = 0
        y += 1
        x += (self.width - len(self.master.session.userStatus)) / 2
        for c in self.master.session.userStatus:
            self.tb.change_cell(x, y, ord(c), termbox.DEFAULT, termbox.DEFAULT)
            x += 1
        
        self.tb.present()

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

