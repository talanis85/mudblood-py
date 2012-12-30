import sys

from mudblood import event
from mudblood import screen
from mudblood import keys
from mudblood import modes
from mudblood import ansi

from mudblood.main import MB

class SerialSource(event.AsyncSource):
    def __init__(self):
        super(SerialSource, self).__init__()

    def poll(self):
        text = raw_input()

        return event.KeystringEvent([ord(c) for c in text])

class SerialScreen(screen.Screen):
    def __init__(self):
        super(SerialScreen, self).__init__()

        self.nlines = 0

        self.mode = "normal"
        self.prompt_call = None

        # Create a source for user input
        self.source = SerialSource()
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
                pass
            elif isinstance(ev, screen.DestroyScreenEvent):
                self.doneEvent()
                print("Goodbye")
                break
            elif isinstance(ev, screen.ModeScreenEvent):
                self.mode = ev.mode
                if ev.mode == "prompt":
                    self.prompt_call = ev.args['call']
                    sys.stdout.write(ev.args['text'])
                    sys.stdout.flush()
            elif isinstance(ev, screen.KeystringScreenEvent):
                if self.mode == "normal":
                    bindret = MB().session.bindings.getBinding(ev.keystring)
                    if bindret:
                        if callable(bindret):
                            MB().drain.put(event.CallableEvent(bindret))
                        elif isinstance(bindret, basestring):
                            MB().drain.put(event.InputEvent(bindret))
                        else:
                            MB().drain.put(event.LogEvent("Invalid binding.", "err"))
                    else:
                        MB().drain.put(event.InputEvent("".join([chr(c) for c in ev.keystring]), display=False))
                elif self.mode == "prompt":
                    MB().drain.put(event.ModeEvent("normal"))
                    MB().drain.put(event.CallableEvent(self.prompt_call, "".join([chr(c) for c in ev.keystring])))

            self.doneEvent()

    def doUpdate(self):
        lines = MB().session.windows[0].linebuffer.lines

        if self.nlines < len(lines):
            sys.stdout.write("\r")
            for l in lines[self.nlines:]:
                sys.stdout.write("{}\n".format(ansi.astringToAnsi(l)))
            sys.stdout.write(str(MB().session.getPromptLine()))

        sys.stdout.flush()

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
