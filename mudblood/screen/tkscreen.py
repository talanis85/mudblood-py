from Tka11y import *

from mudblood import event
from mudblood import screen
from mudblood import keys
from mudblood import modes
from mudblood import ansi

from mudblood.screen import modalscreen

class TkScreen(modalscreen.ModalScreen):
    def __init__(self, master):
        super(TkScreen, self).__init__(master)

        self.nlines = 0
    
    def updateScreen(self):
        self.root.event_generate("<<Update>>", when="tail")

    def run(self):
        self.root = Tk()
        self.text = Text(self.root)
        self.text.config(state=DISABLED)
        self.text.pack()

        self.root.bind("<<Update>>", self.doUpdate)
        self.root.bind("<<Destroy>>", self.doDestroy)
        self.root.bind("<<Mode>>", self.doMode)
        self.root.bind("<Key>", self.doKey)

        self.root.mainloop()

    def doMode(self):
        pass

    def doDestroy(self):
        self.root.quit()

    def doKey(self, ev):
        if ev.char != '':
            self.modeManager.key(ord(ev.char))
        self.doUpdate(None)

    def doUpdate(self, ev):
        lines = self.master.session.windows[0].linebuffer.lines

        self.text.config(state=NORMAL)
        print(self.text.index("end -1l"))
        print(self.text.index("end"))
        self.text.insert(END, "\n")
        self.text.delete("end -2l", "end -1l")
        for l in lines[self.nlines:]:
            self.text.insert(END, str(l) + "\n")
        self.text.insert(END, str(self.master.session.getPromptLine()))
        self.text.insert(END, self.normalMode.getBuffer())
        self.text.config(state=DISABLED)

        self.text.see(END)

        self.nlines = len(lines)


#class NormalMode(modes.BufferMode):
#    def __init__(self):
#        super(NormalMode, self).__init__()
#
#    def onKey(self, key):
#        bindret = MB().session.bindings.key(key)
#
#        if bindret == True:
#            pass
#        elif bindret == False:
#            MB().session.bindings.reset()
#            if key == ord("\n"):
#                self.addHistory()
#
#                MB().drain.put(event.InputEvent(self.getBuffer(), display=False))
#                self.clearBuffer()
#            elif key == keys.KEY_CTRL_BACKSLASH:
#                MB().drain.put(event.ModeEvent("lua"))
#            elif key == keys.KEY_ESC:
#                MB().drain.put(event.ModeEvent("console"))
#            elif key == keys.KEY_PGUP:
#                MB().session.windows[0].scroll += 20
#            elif key == keys.KEY_PGDN:
#                MB().session.windows[0].scroll -= 20
#                if MB().session.windows[0].scroll < 0:
#                    MB().session.windows[0].scroll = 0
#            else:
#                super(NormalMode, self).onKey(key)
#        else:
#            MB().session.bindings.reset()
#            if callable(bindret):
#                MB().drain.put(event.CallableEvent(bindret))
#            elif isinstance(bindret, basestring):
#                MB().drain.put(event.InputEvent(bindret))
#            else:
#                MB().drain.put(event.LogEvent("Invalid binding.", "err"))
#
#normalMode = NormalMode()
#
#class ConsoleMode(modes.Mode):
#    def onKey(self, key):
#        if key == keys.KEY_ESC:
#            MB().drain.put(event.ModeEvent("normal"))
#        else:
#            super(ConsoleMode, self).onKey(key)
#
#consoleMode = ConsoleMode()
#
#class LuaMode(modes.BufferMode):
#    def onKey(self, key):
#        if key == keys.KEY_ESC:
#            MB().drain.put(event.ModeEvent("normal"))
#        elif key == ord("\r"):
#            self.addHistory()
#
#            MB().session.luaEval(self.getBuffer() + "\n")
#            self.clearBuffer()
#            MB().drain.put(event.ModeEvent("normal"))
#        else:
#            super(LuaMode, self).onKey(key)
#
#luaMode = LuaMode()
#
#class MapMode(modes.Mode):
#    def onKey(self, key):
#        if key == keys.KEY_ESC:
#            MB().drain.put(event.ModeEvent("normal"))
#        else:
#            super(MapMode, self).onKey(key)
#
#mapMode = MapMode()
#
#class PromptMode(modes.BufferMode):
#    def __init__(self):
#        super(PromptMode, self).__init__()
#        self.call = None
#        self.text = ""
#
#    def getText(self):
#        return self.text
#
#    def getCall(self):
#        return self.call
#
#    def onEnter(self, text="", call=None):
#        self.call = call
#        self.text = text
#
#    def onKey(self, key):
#        if key == keys.KEY_ESC:
#            MB().drain.put(event.ModeEvent("normal"))
#        elif key == ord("\r"):
#            MB().drain.put(event.ModeEvent("normal"))
#            if self.call:
#                MB().drain.put(event.CallableEvent(self.call, self.getBuffer()))
#            self.clearBuffer()
#        else:
#            super(PromptMode, self).onKey(key)
#
#promptMode = PromptMode()
