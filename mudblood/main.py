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
    mainMB = Mudblood("termbox")
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

#class Singleton(type):
#    def __init__(cls, name, bases, dict):
#        super(Singleton, cls).__init__(name, bases, dict)
#        cls.instance = None 
#
#    def __call__(cls,*args,**kw):
#        if cls.instance is None:
#            cls.instance = super(Singleton, cls).__call__(*args, **kw)
#        return cls.instance

class Mudblood(object):
    #__metaclass__ = Singleton

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
        elif self.screenType == "debug":
            import mudblood.screen.debug
            self.screen = mudblood.screen.debug.DebugScreen()

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

        self.screen.update()

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
            self.screen.update()

            # TODO: multiple sessions
            
        self.screen.destroy()

    def event(self, ev):
        #if not isinstance(ev, event.RawEvent):
        #    self.log(str(ev), "debug3")

        if isinstance(ev, event.LogEvent):
            self.log(ev.msg, ev.level)
        elif isinstance(ev, event.KeyEvent):
            self.screen.keyEvent(ev.key)
        elif isinstance(ev, event.ResizeEvent):
            #self.log("Window Resize ({}x{})".format(ev.w, ev.h), "debug")
            #self.screen.updateSize()
            self.screen.updateSize(ev.w, ev.h)
            #self.screen.updateSize(10, 10)
        elif isinstance(ev, event.ModeEvent):
            #self.log("Changed mode to {} ({})".format(ev.mode, ev.args), "debug")
            self.screen.modeManager.setMode(ev.mode, **ev.args)
        elif isinstance(ev, event.CallableEvent):
            try:
                ev.call(*ev.args)
            except Exception as e:
                self.log(str(e), "err")
        else:
            #t = time.clock()
            self.session.event(ev)
            #self.log("{} took time {}".format(str(ev), time.clock() - t))

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
