import sys
import tty
import termios

from mudblood import event
from mudblood import keys
from mudblood import modes
from mudblood import ansi
from mudblood import screen
from mudblood.screen import modalscreen

from mudblood.screen import term

def createScreen(master):
    return TtyScreen(master)

class TtySource(event.AsyncSource):
    def __init__(self, term):
        super(TtySource, self).__init__()
        self.term = term
        self.prefix = ""

    def poll(self):
        c = self.term.read(1)

        self.prefix += c
        isprefix = False
        for k,v in self.term.terminfo.keys().items():
            if v == self.prefix:
                self.prefix = ""
                return event.KeyEvent(getattr(keys, "KEY_" + k))
            if v.startswith(self.prefix):
                isprefix = True
        if isprefix:
            return None

        self.prefix = ""

        return event.KeyEvent(ord(c))

class TtyScreen(modalscreen.ModalScreen):
    def __init__(self, master):
        super(TtyScreen, self).__init__(master)

        self.nlines = 0
        self.lastPromptLen = 0
        self.term = term.Terminal('xterm')

        self.term.setup()

        self.term.enter_keypad()

        # Create a source for user input
        self.source = TtySource(self.term)
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
                self.term.exit_keypad()
                self.term.reset()
                self.doneEvent()
                break
            elif isinstance(ev, screen.ModeScreenEvent):
                self.modeManager.setMode(ev.mode, **ev.args)
            elif isinstance(ev, screen.KeyScreenEvent):
                if ev.key == ord("#"):
                    self.put(event.ModeEvent("lua"))
                else:
                    self.modeManager.key(ev.key)

            self.doneEvent()

    def doUpdate(self):
        lines = self.master.session.windows[0].linebuffer.lines

        self.term.write("\r")
        for l in lines[self.nlines:]:
            self.term.write("{}\n".format(ansi.astringToAnsi(l)))
        self.term.erase_line()
        self.term.write(ansi.astringToAnsi(self.master.session.getPromptLine()))
        
        if self.modeManager.getMode() == 'normal':
            self.term.write(self.normalMode.getBuffer())
        elif self.modeManager.getMode() == 'lua':
            self.term.write("\\" + self.luaMode.getBuffer())
        elif self.modeManager.getMode() == 'prompt':
            self.term.write(self.promptMode.getText() + self.promptMode.getBuffer())

        self.term.flush()

        self.nlines = len(lines)
