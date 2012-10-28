def MB():
    return Mudblood()

import sys
import os

import event
import session
import linebuffer
import window
import errors

class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None 

    def __call__(cls,*args,**kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance

class Mudblood(metaclass=Singleton):
    def __init__(self, screenType):
        self.session = None
        self.drain = event.Drain()
        self.console = linebuffer.Linebuffer()
        self.windows = [window.LinebufferWindow(self.console)]
        self.screenType = screenType
        self.path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def run(self, config):
        if self.screenType == "termbox":
            import screen.termbox
            self.screen = screen.termbox.TermboxScreen()
        else:
            self.screen = None

        self.screen.source.bind(self.drain)

        # Initialize session
        try:
            os.chdir(os.path.join(os.environ['HOME'], ".config/mudblood-py"))
        except:
            self.log("Creating ~/.config/mudblood-py", "info")
            try:
                try:
                    os.mkdir(os.path.join(os.environ['HOME'], ".config"))
                except OSError:
                    pass
                os.mkdir(os.path.join(os.environ['HOME'], ".config/mudblood-py"))
                os.chdir(os.path.join(os.environ['HOME'], ".config/mudblood-py"))
            except:
                raise Exception("Could not create configuration directory.")

        self.session = session.Session(config['script'])

        self.screen.update()

        while True:
            ev = self.drain.get(1)

            if ev:
                if not (isinstance(ev, event.RawEvent) or isinstance(ev, event.KeyEvent)):
                    self.log(str(ev), "debug3")

                if isinstance(ev, event.LogEvent):
                    self.log(ev.msg, ev.level)
                elif isinstance(ev, event.KeyEvent):
                    self.screen.keyEvent(ev.key)
                elif isinstance(ev, event.ResizeEvent):
                    self.screen.updateSize()
                elif isinstance(ev, event.ModeEvent):
                    self.screen.modeManager.setMode(ev.mode)
                elif isinstance(ev, event.QuitEvent):
                    break
                else:
                    self.session.event(ev)

            self.screen.update()

            # TODO: multiple sessions
            self.session.luaHook("heartbeat")

        self.screen.destroy()

    def log(self, msg, level="debug"):
        if level == "debug3":
            self.console.echo("-- DEBUG: " + msg)
        elif level == "debug2":
            self.console.echo("-- DEBUG: " + msg)
        elif level == "debug":
            self.console.echo("-- DEBUG: " + msg)
        elif level == "info":
            self.console.echo("-- INFO: " + msg)
        elif level == "warn":
            self.console.echo("-- WARNING: " + msg)
        elif level == "err":
            self.console.echo("-- ERROR: " + msg)
        else:
            self.console.echo("-- CRITICAL: " + msg)
