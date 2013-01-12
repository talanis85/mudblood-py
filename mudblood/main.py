import sys
import os
import time
import argparse

def main():
    from mudblood.main import Mudblood

    parser = argparse.ArgumentParser(description="Mudblood MUD client")
    parser.add_argument("-i", metavar="interface", action='store',
            choices=['tbscreen', 'pgscreen', 'serial', 'ttyscreen', 'tkscreen', 'wxscreen'],
            default='tbscreen', help="The interface to use (default: termbox)")
    parser.add_argument("script", action='store', nargs='?',
            help="The main script")
    options = parser.parse_args()

    config = {
            "script": options.script
            }

    Mudblood(options.i).run(config)

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
        screenModule = getattr(__import__('mudblood.screen.'+self.screenType, globals(), locals(), [], -1).screen, self.screenType)
        self.screen = screenModule.createScreen(self)

        self.screen.bind(self.drain)
        self.screen.start()

        # Initialize session
        try:
            os.chdir(os.path.join(os.environ['HOME'], ".config", "mudblood-py"))
        except:
            self.log("Creating ~/.config/mudblood-py", "info")
            try:
                try:
                    os.mkdir(os.path.join(os.environ['HOME'], ".config"))
                except OSError:
                    pass
                os.mkdir(os.path.join(os.environ['HOME'], ".config", "mudblood-py"))
                os.chdir(os.path.join(os.environ['HOME'], ".config", "mudblood-py"))
            except:
                raise Exception("Could not create configuration directory.")

        self.session = session.Session(config['script'])
        self.session.bind(self.drain)
        self.session.start()

        self.screen.updateScreen()

        doQuit = False
        while not doQuit:
            needUpdate = False

            # Process all pending events, then update screen
            ev = self.drain.get(True, 1)
            if ev:
                if isinstance(ev, event.QuitEvent):
                    doQuit = True
                else:
                    self.event(ev)
                    needUpdate = True
            while True:
                ev = self.drain.get(False)
                if ev is None:
                    break
                if isinstance(ev, event.QuitEvent):
                    doQuit = True
                else:
                    self.event(ev)
                    needUpdate = True

            self.session.lua.triggerTime()

            if needUpdate:
                self.screen.updateScreen()

            self.screen.tick()

            # TODO: multiple sessions
        self.log("Goodbye", "info")
            
        self.screen.destroy()
        self.screen.join()

        self.session.destroy()

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
            self.screen.log("-- DEBUG: " + msg)
        elif level == "debug2":
            self.screen.log("-- DEBUG: " + msg)
        elif level == "debug":
            self.screen.log("-- DEBUG: " + msg)
        elif level == "info":
            self.screen.log("-- INFO: " + msg)
        elif level == "warn":
            self.screen.log("-- WARNING: " + msg)
        elif level == "err":
            self.screen.log("-- ERROR: " + msg)
        else:
            self.screen.log("-- CRITICAL: " + msg)

if __name__ == "__main__":
    main()

