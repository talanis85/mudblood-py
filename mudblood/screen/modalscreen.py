from mudblood import screen
from mudblood import modes
from mudblood import keys
from mudblood import event

from mudblood.main import MB

class ModalScreen(screen.Screen):
    def __init__(self):
        super(ModalScreen, self).__init__()

        self.normalMode = NormalMode()
        self.consoleMode = ConsoleMode()
        self.luaMode = LuaMode()
        self.mapMode = MapMode()
        self.promptMode = PromptMode()

        # Create the mode manager
        self.modeManager = modes.ModeManager("normal", {
            "normal": self.normalMode,
            "console": self.consoleMode,
            "lua": self.luaMode,
            "prompt": self.promptMode,
            })

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

class ConsoleMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent("normal"))
        else:
            super(ConsoleMode, self).onKey(key)

class LuaMode(modes.BufferMode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent("normal"))
        elif key == ord("\n"):
            self.addHistory()

            MB().session.luaEval(self.getBuffer() + "\n")
            self.clearBuffer()
            MB().drain.put(event.ModeEvent("normal"))
        else:
            super(LuaMode, self).onKey(key)

class MapMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            MB().drain.put(event.ModeEvent("normal"))
        else:
            super(MapMode, self).onKey(key)

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
        elif key == ord("\n"):
            MB().drain.put(event.ModeEvent("normal"))
            if self.call:
                MB().drain.put(event.CallableEvent(self.call, self.getBuffer()))
            self.clearBuffer()
        else:
            super(PromptMode, self).onKey(key)
