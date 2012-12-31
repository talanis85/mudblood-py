import sys
import tty
import termios

from mudblood import event
from mudblood import keys
from mudblood import modes
from mudblood import ansi
from mudblood import screen
from mudblood.screen import modalscreen

from mudblood.main import MB

from mudblood.screen import term

class TtySource(event.AsyncSource):
    def __init__(self, terminfo):
        super(TtySource, self).__init__()
        self.terminfo = terminfo
        self.prefix = ""

    def poll(self):
        c = sys.stdin.read(1)

        self.prefix += c
        #print("Prefix: {}".format([ord(c) for c in self.prefix]))
        isprefix = False
        for k,v in self.terminfo['keys'].items():
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
    def __init__(self):
        super(TtyScreen, self).__init__()

        self.nlines = 0
        self.lastPromptLen = 0
        self.terminfo = term.terminfo['xterm']

        sys.stdout.write(self.terminfo['functions']['ENTER_KEYPAD'])
        sys.stdout.flush()

        # Unix only
        self.old_tty = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        # /Unix only

        # Create a source for user input
        self.source = TtySource(self.terminfo)
        self.source.start()
        self.source.bind(MB().drain)

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
                sys.stdout.write(self.terminfo['functions']['EXIT_KEYPAD'])
                sys.stdout.flush()
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_tty)
                self.doneEvent()
                break
            elif isinstance(ev, screen.ModeScreenEvent):
                self.modeManager.setMode(ev.mode, **ev.args)
            elif isinstance(ev, screen.KeyScreenEvent):
                #if ev.key < 128:
                #    sys.stdout.write(chr(ev.key))
                #sys.stdout.write("KeyEvent: {}\n".format(ev.key))
                self.modeManager.key(ev.key)

            self.doneEvent()

    def doUpdate(self):
        lines = MB().session.windows[0].linebuffer.lines

        #if self.nlines < len(lines):
        sys.stdout.write("\r")
        for l in lines[self.nlines:]:
            sys.stdout.write("{}\n".format(ansi.astringToAnsi(l)))
        sys.stdout.write(ansi.astringToAnsi(MB().session.getPromptLine()))
        
        sys.stdout.write(self.normalMode.getBuffer())
        if len(self.normalMode.getBuffer()) < self.lastPromptLen:
            for i in range(self.lastPromptLen - len(self.normalMode.getBuffer())):
                sys.stdout.write(" ")
            for i in range(self.lastPromptLen - len(self.normalMode.getBuffer())):
                sys.stdout.write("\b")
        self.lastPromptLen = len(self.normalMode.getBuffer())

        sys.stdout.flush()

        self.nlines = len(lines)
