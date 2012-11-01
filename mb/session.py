import os
import traceback

import lua
import event
import linebuffer
import colors
import window
import ansi
import telnet
import keys
import errors
import map

from mudblood import MB

class Session(object):
    def __init__(self, script=None):
        self.lua = lua.Lua(self, os.path.join(MB().path, "lua/?.lua"))

        self.lb = linebuffer.Linebuffer()
        self.bindings = keys.Bindings()
        self.telnet = None
        self.ansi = ansi.Ansi()
        self.status = ""
        self.encoding = "utf8"
        self.map = map.Map()
        self.mapWindow = window.MapWindow(self.map)
        self.windows = [window.LinebufferWindow(self.lb), self.mapWindow]

        if script:
            self.lb.echo("-- Loading {}".format(script))
            try:
                self.lua.loadFile(script + "/profile.lua")
            except Exception as e:
                self.lb.echo("-- LUA ERROR: {}".format(str(e)))

        self.lb.echo("-- Session started.")

    def event(self, ev):
        if isinstance(ev, event.RawEvent):
            if self.encoding != "":
                try:
                    self.lb.append(self.ansi.parseToAString(ev.data.decode(self.encoding)))
                except UnicodeDecodeError as e:
                    self.encoding = "utf8"
                    self.log("Error decoding data. Switching to 'utf8'")
                    try:
                        self.lb.append(self.ansi.parseToAString(ev.data.decode(self.encoding)))
                    except UnicodeDecodeError as e:
                        self.encoding = ""
                        self.log("Still no luck. Giving up, sorry. Maybe try a different encoding?")

        elif isinstance(ev, event.DisconnectEvent):
            self.log("Connection closed.", "info")
            self.luaHook("disconnect")
            self.telnet = None
        elif isinstance(ev, event.InputEvent):
            for l in ev.text.splitlines():
                ret = self.luaHook("input", l)
                if ret is not None:
                    l = ret
                if l:
                    self.lb.echoInto(colors.AString(l).fg(colors.YELLOW))
                    if self.telnet:
                        self.telnet.write((l + "\n").encode(self.encoding))
        elif isinstance(ev, telnet.TelnetEvent):
            self.luaHook("telneg", ev.cmd, ev.option, ev.data)

        def lineCallback(line):
            a = ansi.Ansi()
            ret = self.luaHook("line", str(line))
            if ret:
                ret = a.parseToAString(ret)
            return ret

        self.lb.update(lineCallback)

    def luaHook(self, hook, *args):
        ret = None
        try:
            ret = self.lua.hook(hook, *args)
        except Exception as e:
            self.lb.echo("-- ERROR in {}: {}".format(hook, str(e)))
            return None
        return ret

    def luaEval(self, command):
        try:
            if command[0] == "?":
                ret = self.lua.eval(command[1:])
            else:
                ret = self.lua.execute(command)
        except Exception as e:
            self.lb.echo("-- LUA ERROR: {}\n{}".format(str(e), traceback.format_exc()))
            return

        if ret:
            self.lb.echo(colors.AString("-> {}".format(ret)).fg(colors.MAGENTA))

    def log(self, msg, level="info"):
        self.lb.echo("-- {}".format(msg))

    # LUA FUNCTIONS

    def quit(self):
        MB().drain.put(event.QuitEvent())

    def print(self, string):
        self.lb.echo(str(string))
    
    def connect(self, host, port):
        self.log("Connecting to {}:{} ...".format(host, port), "info")

        try:
            self.telnet = telnet.Telnet(host, port)
        except Exception as e:
            self.telnet = None
            self.log("Could not connect: {}".format(str(e)))
            return

        self.telnet.bind(MB().drain)
        self.log("Connection established.", "info")
        self.luaHook("connect", host, port)
        self.telnet.start()

    def status(self, string=None):
        if string is None:
            pass
        else:
            self.status = string
        return self.status

    def send(self, data):
        MB().drain.put(event.InputEvent(data))

    def directSend(self, data):
        self.telnet.write(data.encode(self.encoding))
