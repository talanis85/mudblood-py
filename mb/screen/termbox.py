import termbox
import event
import linebuffer
import modes
import screen
import keys
import colors
import map

from mudblood import MB

termbox.DEFAULT = 0x09

class TermboxSource(event.AsyncSource):
    def __init__(self, tb):
        self.tb = tb
        super().__init__()

    def poll(self):
        ret = self.tb.poll_event()
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
        self.updateSize()

        # Initialize the main linebuffer
        self.lb = linebuffer.Linebuffer()

        # Create a source for user input
        self.source = TermboxSource(self.tb)
        self.source.start()

        # Create the mode manager
        self.modeManager = modes.ModeManager(normalMode)
    
    def destroy(self):
        self.tb.close()

    def mode(self, m):
        if m == "map":
            self.modeManager.setMode(mapMode)

    def updateSize(self):
        self.width = self.tb.width()
        self.height = self.tb.height()

    def update(self):
        self.tb.clear()

        x = 0
        y = 0

        windowArea = self.height - 2

        windows = None

        # Draw session windows
        # If in consoleMode, draw mudblood windows

        if self.modeManager.getMode() == consoleMode:
            windows = MB().windows
        else:
            windows = MB().session.windows

        ratioWhole = 0.0
        for w in windows:
            if w.visible:
                ratioWhole += w.ratio

        for w in reversed(windows):
            if w.visible:
                wh = int(windowArea * (w.ratio / ratioWhole))

                if w.type == "linebuffer":
                    lines = w.linebuffer.render(self.width, 0, wh)
                    if len(lines) < wh:
                        y += wh - len(lines)

                    for l in lines:
                        x = 0
                        for c in l:
                            if c[1] == "\t":
                                x += 8 - (x % 8)
                            else:
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
        if self.modeManager.getMode() == normalMode:
            self.tb.set_cursor(x + normalMode.getCursor(), y)
            for c in normalMode.getBuffer():
                self.tb.change_cell(x, y, ord(c), termbox.YELLOW, termbox.DEFAULT)
                x += 1
            x = 0
            y += 1
        elif self.modeManager.getMode() == luaMode:
            x = 0
            y += 1

            self.tb.change_cell(x, y, ord("\\"), termbox.RED, termbox.DEFAULT)
            x += 1

            self.tb.set_cursor(x + luaMode.getCursor(), y)
            for c in luaMode.getBuffer():
                self.tb.change_cell(x, y, ord(c), termbox.RED, termbox.DEFAULT)
                x += 1

        # Status line
        x = 0
        y += 1
        x += (self.width - len(MB().session.status)) / 2
        for c in MB().session.status:
            self.tb.change_cell(x, y, ord(c), termbox.DEFAULT, termbox.DEFAULT)
            x += 1
        
        self.tb.present()

    def keyEvent(self, key):
        self.modeManager.key(key)

class NormalMode(modes.BufferMode):
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
                MB().drain.put(event.ModeEvent(luaMode))
            elif key == keys.KEY_ESC:
                MB().drain.put(event.ModeEvent(consoleMode))
            else:
                super().onKey(key)
        else:
            MB().session.bindings.reset()
            if callable(bindret):
                bindret()
            elif isinstance(bindret, str):
                MB().drain.put(event.InputEvent(bindret + "\n"))
            else:
                MB().drain.put(event.LogEvent("Invalid binding.", "err"))

normalMode = NormalMode()

class ConsoleMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent(normalMode))
        else:
            super().onKey(key)

consoleMode = ConsoleMode()

class LuaMode(modes.BufferMode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent(normalMode))
        elif key == ord("\r"):
            self.addHistory()

            MB().session.luaEval(self.getBuffer() + "\n")
            self.clearBuffer()
            MB().drain.put(event.ModeEvent(normalMode))
        else:
            super().onKey(key)

luaMode = LuaMode()

class MapMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent(normalMode))
        else:
            super().onKey(key)

mapMode = MapMode()
