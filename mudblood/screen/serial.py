import sys

from mudblood import event
from mudblood import screen
from mudblood import keys
from mudblood import modes
from mudblood import ansi

def createScreen(master):
    return SerialScreen(master)

class SerialSource(event.AsyncSource):
    def __init__(self):
        super(SerialSource, self).__init__()

    def poll(self):
        text = raw_input()

        return event.KeystringEvent([ord(c) for c in text])

class SerialScreen(screen.Screen):
    def __init__(self, master):
        super(SerialScreen, self).__init__(master)

        self.nlines = 0

        self.mode = "normal"
        self.prompt_call = None

        # Create a source for user input
        self.source = SerialSource()
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
                pass
            elif isinstance(ev, screen.DestroyScreenEvent):
                self.doneEvent()
                break
            elif isinstance(ev, screen.ModeScreenEvent):
                self.mode = ev.mode
                if ev.mode == "prompt":
                    self.prompt_call = ev.args['call']
                    sys.stdout.write(ev.args['text'])
                    sys.stdout.flush()
            elif isinstance(ev, screen.KeystringScreenEvent):
                if self.mode == "normal":
                    bindret = self.master.session.bindings.getBinding(ev.keystring)
                    if bindret:
                        if callable(bindret):
                            self.put(event.CallableEvent(bindret))
                        elif isinstance(bindret, basestring):
                            self.put(event.InputEvent(bindret))
                        else:
                            self.put(event.LogEvent("Invalid binding.", "err"))
                    else:
                        self.master.drain.put(event.InputEvent("".join([chr(c) for c in ev.keystring]), display=False))
                elif self.mode == "prompt":
                    self.put(event.ModeEvent("normal"))
                    self.put(event.CallableEvent(self.prompt_call, "".join([chr(c) for c in ev.keystring])))

            self.doneEvent()

    def doUpdate(self):
        lines = self.master.session.windows[0].linebuffer.lines

        if self.nlines < len(lines):
            sys.stdout.write("\r")
            for l in lines[self.nlines:]:
                sys.stdout.write("{}\n".format(ansi.astringToAnsi(l)))
            sys.stdout.write(str(self.master.session.getPromptLine()))

        sys.stdout.flush()

        self.nlines = len(lines)
