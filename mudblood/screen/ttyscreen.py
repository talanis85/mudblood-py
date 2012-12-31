import sys
import tty
import termios

from mudblood import event
from mudblood import screen
from mudblood import keys
from mudblood import modes
from mudblood import ansi

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

class TtyScreen(screen.Screen):
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

        # Create the mode manager
        self.modeManager = modes.ModeManager("normal", {
            "normal": normalMode,
            "console": consoleMode,
            "lua": luaMode,
            "prompt": promptMode,
            })

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
        
        sys.stdout.write(normalMode.getBuffer())
        if len(normalMode.getBuffer()) < self.lastPromptLen:
            for i in range(self.lastPromptLen - len(normalMode.getBuffer())):
                sys.stdout.write(" ")
            for i in range(self.lastPromptLen - len(normalMode.getBuffer())):
                sys.stdout.write("\b")
        self.lastPromptLen = len(normalMode.getBuffer())

        sys.stdout.flush()

        self.nlines = len(lines)


class NormalMode(modes.BufferMode):
    def __init__(self):
        super(NormalMode, self).__init__()

    def onKey(self, key):
        bindret = MB().session.bindings.key(key)

        if bindret == True:
            pass
        elif bindret == False:
            MB().session.bindings.reset()
            if key == ord("\n"):
                self.addHistory()

                MB().drain.put(event.InputEvent(self.getBuffer(), display=True))
                self.clearBuffer()
            elif key == keys.KEY_CTRL_BACKSLASH:
                MB().drain.put(event.ModeEvent("lua"))
            elif key == keys.KEY_ESC:
                MB().drain.put(event.ModeEvent("console"))
            elif key == keys.KEY_PGUP:
                MB().session.windows[0].scroll += 20
            elif key == keys.KEY_PGDN:
                MB().session.windows[0].scroll -= 20
                if MB().session.windows[0].scroll < 0:
                    MB().session.windows[0].scroll = 0
            else:
                super(NormalMode, self).onKey(key)
        else:
            MB().session.bindings.reset()
            if callable(bindret):
                MB().drain.put(event.CallableEvent(bindret))
            elif isinstance(bindret, basestring):
                MB().drain.put(event.InputEvent(bindret))
            else:
                MB().drain.put(event.LogEvent("Invalid binding.", "err"))

normalMode = NormalMode()

class ConsoleMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent("normal"))
        else:
            super(ConsoleMode, self).onKey(key)

consoleMode = ConsoleMode()

class LuaMode(modes.BufferMode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent("normal"))
        elif key == ord("\r"):
            self.addHistory()

            MB().session.luaEval(self.getBuffer() + "\n")
            self.clearBuffer()
            MB().drain.put(event.ModeEvent("normal"))
        else:
            super(LuaMode, self).onKey(key)

luaMode = LuaMode()

class MapMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent("normal"))
        else:
            super(MapMode, self).onKey(key)

mapMode = MapMode()

class PromptMode(modes.BufferMode):
    def __init__(self):
        super(PromptMode, self).__init__()
        self.call = None
        self.text = ""

    def getText(self):
        return self.text

    def getCall(self):
        return self.call

    def onEnter(self, text="", call=None):
        self.call = call
        self.text = text

    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent("normal"))
        elif key == ord("\r"):
            MB().drain.put(event.ModeEvent("normal"))
            if self.call:
                MB().drain.put(event.CallableEvent(self.call, self.getBuffer()))
            self.clearBuffer()
        else:
            super(PromptMode, self).onKey(key)

promptMode = PromptMode()
