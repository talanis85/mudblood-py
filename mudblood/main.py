mainMB = None

#def main():
#    import cProfile
#    cProfile.runctx("main2()", globals(), locals())

def main():
    import sys

    from mudblood.main import Mudblood

    config = {
            "script": None
            }

    if len(sys.argv) > 1:
        config['script'] = sys.argv[1]

    global mainMB
    mainMB = Mudblood("tty")
    mainMB.run(config)

def MB():
    return mainMB

import sys
import os

import time

from mudblood import event
from mudblood import session
from mudblood import linebuffer
from mudblood import window

class Mudblood(object):
    def __init__(self, screenType):
        self.session = None
        self.drain = event.Drain()
        self.console = linebuffer.Linebuffer()
        self.windows = [window.LinebufferWindow(self.console)]
        self.screenType = screenType
        self.path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def run(self, config):
        if self.screenType == "termbox":
            import mudblood.screen.tbscreen
            self.screen = mudblood.screen.tbscreen.TermboxScreen()
        elif self.screenType == "serial":
            import mudblood.screen.serial
            self.screen = mudblood.screen.serial.SerialScreen()
        elif self.screenType == "pygame":
            import mudblood.screen.pgscreen
            self.screen = mudblood.screen.pgscreen.PygameScreen()
        elif self.screenType == "tty":
            import mudblood.screen.ttyscreen
            self.screen = mudblood.screen.ttyscreen.TtyScreen()

        self.screen.start()

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
        self.session.bind(self.drain)
        self.session.start()

        self.screen.updateScreen()

        doQuit = False
        while not doQuit:
            # Process all pending events, then update screen

            ev = self.drain.get(True, 1)
            if ev:
                if isinstance(ev, event.QuitEvent):
                    doQuit = True
                else:
                    self.event(ev)
            while True:
                ev = self.drain.get(False)
                if ev is None:
                    break
                if isinstance(ev, event.QuitEvent):
                    doQuit = True
                else:
                    self.event(ev)

            self.session.lua.triggerTime()
            self.screen.updateScreen()

            self.screen.tick()

            # TODO: multiple sessions
            
        self.screen.destroy()
        self.screen.join()

    def event(self, ev):
        #if not isinstance(ev, event.RawEvent):
        #    self.log(str(ev), "debug3")

        if isinstance(ev, event.LogEvent):
            self.log(ev.msg, ev.level)
        elif isinstance(ev, event.KeyEvent):
            self.screen.key(ev.key)
        elif isinstance(ev, event.KeystringEvent):
            self.screen.keystring(ev.keystring)
        elif isinstance(ev, event.ResizeEvent):
            self.screen.updateSize(ev.w, ev.h)
        elif isinstance(ev, event.ModeEvent):
            self.screen.setMode(ev.mode, **ev.args)
        elif isinstance(ev, event.CallableEvent):
            try:
                ev.call(*ev.args)
            except Exception as e:
                self.log(str(e), "err")
        else:
            self.session.event(ev)

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
