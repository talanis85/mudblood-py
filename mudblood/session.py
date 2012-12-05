import os
import traceback

from pkg_resources import Requirement, resource_filename

from mudblood import lua
from mudblood import event
from mudblood import linebuffer
from mudblood import colors
from mudblood import window
from mudblood import ansi
from mudblood import telnet
from mudblood import keys
from mudblood import map
from mudblood import rpc

from mudblood.main import MB

class Session(event.Source):
    """
    A session is one single connection to a server. Every session has its own socket,
    linebuffer, map and lua-runtime.
    """
    def __init__(self, script=None):
        super().__init__()

        self.lua = lua.Lua(self, os.path.join(resource_filename(Requirement.parse("mudblood"), "mudblood/lua"), "?.lua"))

        self.lb = linebuffer.Linebuffer()
        self.bindings = keys.Bindings()
        self.telnet = None
        self.lastLine = ""
        self.promptLine = ""
        self.ansi = ansi.Ansi()
        self.userStatus = ""
        self.encoding = "utf8"
        self.map = map.Map()
        self.mapWindow = window.MapWindow(self.map)
        self.windows = [window.LinebufferWindow(self.lb), self.mapWindow]
        self.rpc = None

        if script:
            self.log("Loading {}".format(script), "info")
            try:
                self.lua.loadFile(script + "/profile.lua")
            except Exception as e:
                self.log("Lua error: {}\n{}".format(str(e), traceback.format_exc()), "err")

        self.log("Session started.", "info")

    def event(self, ev):
        """
        This function handles incoming events (see event.py)
        User input and data received from the socket are somewhat special, as they are
        processed as chains of events:
          RawEvent -> StringEvent -> EchoEvent
        and
          InputEvent -> DirectInputEvent -> SendEvent
        """
        if isinstance(ev, event.RawEvent):
            if self.encoding != "":
                try:
                    text = ev.data.decode(self.encoding)
                    self.push(event.StringEvent(text))
                except UnicodeDecodeError as e:
                    self.encoding = "utf8"
                    self.put(LogEvent("Error decoding data. Switching to 'utf8'"))
                    try:
                        text = ev.data.decode(self.encoding)
                        self.push(event.StringEvent(text))
                    except UnicodeDecodeError as e:
                        self.encoding = ""
                        self.push(event.LogEvent("Still no luck. Giving up, sorry. Maybe try a different encoding?"))
        elif isinstance(ev, event.StringEvent):
            tempqueue = []
            lines = ev.text.split("\n")
            firstLine = self.lastLine + lines[0]
            if len(lines) > 1:
                parsedLines = []
                for line in [firstLine] + lines[1:-1]:
                    parsedLines.append(self.ansi.parseToAString(line))
                for parsedLine in parsedLines:
                    ret = None
                    try:
                        ret = self.lua.triggerRecv(str(parsedLine))
                    except Exception as e:
                        self.log("Lua error in send trigger: {}\n{}".format(str(e), traceback.format_exc()), "err")

                    if ret is None:
                        tempqueue.append(event.EchoEvent(parsedLine))
                    elif ret is False:
                        pass
                    else:
                        tempqueue.append(event.EchoEvent(ansi.Ansi().parseToAString(ret)))
                self.lastLine = lines[-1]
            else:
                self.lastLine = firstLine
            for e in reversed(tempqueue):
                self.push(e)
        elif isinstance(ev, event.EchoEvent):
            self.print(ev.text)

        elif isinstance(ev, event.DisconnectEvent):
            self.log("Connection closed.", "info")
            self.luaHook("disconnect")
            self.telnet = None

        elif isinstance(ev, event.InputEvent):
            for l in ev.text.split("\n"):
                if ev.display:
                    self.print(self.getPromptLine() + colors.AString(l).fg(colors.YELLOW))
                    self.lastLine = ""

                ret = None
                try:
                    ret = self.lua.triggerSend(l)
                except Exception as e:
                    self.log("Lua error in send trigger: {}\n{}".format(str(e), traceback.format_exc()), "err")
        elif isinstance(ev, event.DirectInputEvent):
            self.push(event.SendEvent(ev.text + "\n"))
        elif isinstance(ev, event.SendEvent):
            if self.telnet:
                self.telnet.write((ev.data).encode(self.encoding))

        elif isinstance(ev, telnet.TelnetEvent):
            self.luaHook("telneg", ev.cmd, ev.option, ev.data)

        elif isinstance(ev, rpc.RPCEvent):
            try:
                if ev.literal:
                    self.lua.execute(ev.literal)
                else:
                    f = self.lua.lua.globals()
                    for s in ev.func:
                        f = getattr(f, s)
                    f(*ev.args)
            except Exception as e:
                self.log("Lua error in RPC: {}\n{}".format(str(e), traceback.format_exc()), "err")

        if ev.continuation:
            try:
                ev.continuation()
            except Exception as e:
                self.log("Lua error: {}\n{}".format(str(e), traceback.format_exc()), "err")
    
    def getLastLine(self):
        return ansi.Ansi().parseToAString(self.lastLine)
    def getPromptLine(self):
        if self.promptLine == "":
            return self.getLastLine()
        else:
            return ansi.Ansi().parseToAString(self.promptLine)

    def getStatusLine(self):
        return (self.lua.eval("mapper.walking()") and "WALKING" or "NOT WALKING")
    
    def print(self, string):
        self.lb.echo(string)

    def luaHook(self, hook, *args):
        ret = None
        try:
            ret = self.lua.hook(hook, *args)
        except Exception as e:
            self.log("Lua error in hook {}: {}\n{}".format(hook, str(e), traceback.format_exc()), "err")
            return None
        return ret

    def luaEval(self, command):
        try:
            if command[0] == "?":
                ret = self.lua.eval(command[1:])
            else:
                ret = self.lua.execute(command)
        except Exception as e:
            self.log("Lua error: {}\n{}".format(str(e), traceback.format_exc()), "err")
            return

        if ret:
            self.print(colors.AString("-> {}".format(ret)).fg(colors.MAGENTA))

    def setRPCSocket(self, sock):
        if self.rpc:
            self.rpc.stop()

        self.rpc = sock
        self.rpc.bind(self)
        self.rpc.start()

    def log(self, msg, level="info"):
        self.print("-- {}".format(msg))

    # LUA FUNCTIONS

    def quit(self):
        self.put(event.QuitEvent())

    def connect(self, host, port):
        if self.telnet:
            self.log("Already connected")
            return

        self.log("Connecting to {}:{} ...".format(host, port), "info")

        try:
            self.telnet = telnet.Telnet(host, port)
        except Exception as e:
            self.telnet = None
            self.log("Could not connect: {}".format(str(e)))
            return

        self.telnet.bind(self)
        self.log("Connection established.", "info")
        self.luaHook("connect", host, port)
        self.telnet.start()

    def status(self, string=None):
        if string is None:
            pass
        else:
            self.userStatus = string
        return self.userStatus

