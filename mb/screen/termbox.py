import termbox
import event
import linebuffer
import modes
import screen
import keys
import colors
import map

import subprocess
import tempfile

from mudblood import MB

termbox.DEFAULT = 0x09

class TermboxSource(event.AsyncSource):
    def __init__(self, tb):
        self.tb = tb
        super().__init__()

    def poll(self):
        ret = self.tb.peek_event(1000)
        if ret == None:
            return None

        t, ch, key, mod, w, h = ret
        if t == termbox.EVENT_KEY:
            if ch:
                return event.KeyEvent(ord(ch))
            else:
                return event.KeyEvent(key)
        elif t == termbox.EVENT_RESIZE:
            return event.ResizeEvent(w, h)

class TermboxScreen(screen.Screen):
    def __init__(self):
        # Initialize Termbox
        self.tb = termbox.Termbox()
        self.tb.set_clear_attributes(termbox.DEFAULT, termbox.DEFAULT)

        # Get window size
        self.updateSize(self.tb.width(), self.tb.height())

        # Initialize the main linebuffer
        self.lb = linebuffer.Linebuffer()

        # Create a source for user input
        self.source = TermboxSource(self.tb)
        self.source.start()
        self.source.bind(MB().drain)

        # Create the mode manager
        self.modeManager = modes.ModeManager("normal", {
            "normal": normalMode,
            "console": consoleMode,
            "lua": luaMode,
            "prompt": promptMode,
            })
    
    def destroy(self):
        self.tb.close()

    def updateSize(self, w, h):
        self.width = w
        self.height = h
        #self.width = self.tb.width()
        #self.height = self.tb.height()

    def update(self):
        x = 0
        y = 0

        windowArea = self.height - 2

        windows = None

        # Draw session windows
        # If in consoleMode, draw mudblood windows

        if self.modeManager.getMode() == "console":
            windows = MB().windows
        else:
            windows = MB().session.windows

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
                              + [MB().session.getPromptLine()]
                    else:
                        lines = w.linebuffer.render(self.width, w.scroll, wh) \
                              + [MB().session.getPromptLine()]
                    if len(lines) < wh:
                        y += wh - len(lines)

                    for l in lines:
                        x = 0
                        for c in l:
                            if c[1] == "\t":
                                x += 8 - (x % 8)
                            else:
                                if not (ord(c[1]) >= ord(" ") and ord(c[1]) <= ord("~")):
                                    self.tb.close()
                                    import pdb; pdb.set_trace()
                                    raise Exception("Non printable char {}. Line is: '{}'".format(ord(c[1]), [ord(x[1]) for x in l]))

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
            self.tb.set_cursor(x + normalMode.getCursor(), y)
            for c in normalMode.getBuffer():
                self.tb.change_cell(x, y, ord(c), termbox.YELLOW, termbox.DEFAULT)
                x += 1
            x = 0
            y += 1
        elif self.modeManager.getMode() == "lua":
            x = 0
            y += 1

            self.tb.change_cell(x, y, ord("\\"), termbox.RED, termbox.DEFAULT)
            x += 1

            self.tb.set_cursor(x + luaMode.getCursor(), y)
            for c in luaMode.getBuffer():
                self.tb.change_cell(x, y, ord(c), termbox.RED, termbox.DEFAULT)
                x += 1
        elif self.modeManager.getMode() == "prompt":
            x = 0
            y += 1

            for c in promptMode.getText():
                self.tb.change_cell(x, y, ord(c), termbox.RED, termbox.DEFAULT)
                x += 1

            self.tb.set_cursor(x + promptMode.getCursor(), y)
            for c in promptMode.getBuffer():
                self.tb.change_cell(x, y, ord(c), termbox.DEFAULT, termbox.DEFAULT)
                x += 1

        # System status
        x = self.width - 1
        for c in reversed(MB().session.getStatusLine()):
            self.tb.change_cell(x, y, ord(c), termbox.DEFAULT, termbox.DEFAULT)
            x -= 1

        # Status line
        x = 0
        y += 1
        x += (self.width - len(MB().session.userStatus)) / 2
        for c in MB().session.userStatus:
            self.tb.change_cell(x, y, ord(c), termbox.DEFAULT, termbox.DEFAULT)
            x += 1
        
        self.tb.present()

    def keyEvent(self, key):
        if key == keys.KEY_CTRL_C:
            self.tb.close()
            raise KeyboardInterrupt()

        self.modeManager.key(key)

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
            self.source.bind(MB().drain)
            self.tb.set_clear_attributes(termbox.DEFAULT, termbox.DEFAULT)
            self.tb.set_cursor(-1, -1)

            tmp.seek(0)
            ret = tmp.read().decode('utf8')
        return ret

class NormalMode(modes.BufferMode):
    def __init__(self):
        super().__init__()

    def onKey(self, key):
        bindret = MB().session.bindings.key(key)

        if bindret == True:
            pass
        elif bindret == False:
            MB().session.bindings.reset()
            if key == ord("\r"):
                self.addHistory()

                MB().drain.put(event.InputEvent(self.getBuffer()))
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
                super().onKey(key)
        else:
            MB().session.bindings.reset()
            if callable(bindret):
                MB().drain.put(event.CallableEvent(bindret))
            elif isinstance(bindret, str):
                MB().drain.put(event.InputEvent(bindret))
            else:
                MB().drain.put(event.LogEvent("Invalid binding.", "err"))

normalMode = NormalMode()

class ConsoleMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent("normal"))
        else:
            super().onKey(key)

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
            super().onKey(key)

luaMode = LuaMode()

class MapMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent("normal"))
        else:
            super().onKey(key)

mapMode = MapMode()

class PromptMode(modes.BufferMode):
    def __init__(self):
        super().__init__()
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
            super().onKey(key)

promptMode = PromptMode()
