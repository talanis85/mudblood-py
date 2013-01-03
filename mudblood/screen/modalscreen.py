from mudblood import screen
from mudblood import modes
from mudblood import keys
from mudblood import event

class ModalScreen(screen.Screen):
    def __init__(self, master):
        super(ModalScreen, self).__init__(master)

        self.normalMode = NormalMode(self)
        self.consoleMode = ConsoleMode(self)
        self.luaMode = LuaMode(self)
        self.mapMode = MapMode(self)
        self.promptMode = PromptMode(self)

        # Create the mode manager
        self.modeManager = modes.ModeManager("normal", {
            "normal": self.normalMode,
            "console": self.consoleMode,
            "lua": self.luaMode,
            "prompt": self.promptMode,
            })

class NormalMode(modes.BufferMode):
    def __init__(self, screen):
        super(NormalMode, self).__init__(screen)

    def onKey(self, key):
        bindret = self.screen.master.session.bindings.key(key)

        if bindret == True:
            pass
        elif bindret == False:
            self.screen.master.session.bindings.reset()
            if key == ord("\n"):
                self.addHistory()

                self.screen.put(event.InputEvent(self.getBuffer(), display=True))
                self.clearBuffer()
            elif key == keys.KEY_CTRL_BACKSLASH:
                self.screen.put(event.ModeEvent("lua"))
            elif key == keys.KEY_ESC:
                self.screen.put(event.ModeEvent("console"))
            elif key == keys.KEY_PGUP:
                self.screen.master.session.windows[0].scroll += 20
            elif key == keys.KEY_PGDN:
                self.screen.master.session.windows[0].scroll -= 20
                if self.screen.master.session.windows[0].scroll < 0:
                    self.screen.master.session.windows[0].scroll = 0
            else:
                super(NormalMode, self).onKey(key)
        else:
            self.screen.master.session.bindings.reset()
            if callable(bindret):
                self.screen.put(event.CallableEvent(bindret))
            elif isinstance(bindret, basestring):
                self.screen.put(event.InputEvent(bindret))
            else:
                self.screen.put(event.LogEvent("Invalid binding.", "err"))

class ConsoleMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            self.screen.put(event.ModeEvent("normal"))
        else:
            super(ConsoleMode, self).onKey(key)

class LuaMode(modes.BufferMode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            self.screen.put(event.ModeEvent("normal"))
        elif key == ord("\n"):
            self.addHistory()

            self.screen.master.session.luaEval(self.getBuffer() + "\n")
            self.clearBuffer()
            self.screen.put(event.ModeEvent("normal"))
        else:
            super(LuaMode, self).onKey(key)

class MapMode(modes.Mode):
    def onKey(self, key):
        if key == keys.KEY_ESC:
            self.screen.put(event.ModeEvent("normal"))
        else:
            super(MapMode, self).onKey(key)

class PromptMode(modes.BufferMode):
    def __init__(self, screen):
        super(PromptMode, self).__init__(screen)
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
            self.screen.put(event.ModeEvent("normal"))
        elif key == ord("\n"):
            self.screen.put(event.ModeEvent("normal"))
            if self.call:
                self.screen.put(event.CallableEvent(self.call, self.getBuffer()))
            self.clearBuffer()
        else:
            super(PromptMode, self).onKey(key)
