import os
import traceback

from mudblood import lua
from mudblood import event
from mudblood import linebuffer
from mudblood import colors
from mudblood import window
from mudblood import ansi
from mudblood import telnet
from mudblood import keys
from mudblood import map
from mudblood import package

class Session(event.Source):
    """
    A session is one single connection to a server. Every session has its own socket,
    linebuffer, map and lua-runtime.
    """
    def __init__(self, master, profile=None):
        super(Session, self).__init__()
        
        self.master = master

        self.linebuffers = {}

        self.lua = lua.Lua(self, package.getResourceFilename("lua", "?.lua"))

        self.bindings = keys.Bindings()
        self.telnet = None
        self.lastLine = ""
        self.lastBlock = ""
        self.promptLine = ""
        self.ansi = ansi.Ansi()
        self.userStatus = colors.AString("")
        self.encoding = "utf8"
        self.map = map.Map()
        self.rpc = None
        self.profile = profile

        self.local_echo = True

        self.width = 0
        self.height = 0

    def start(self):
        if self.profile:
            self.log("Loading {}".format(self.profile), "info")
            try:
                self.lua.lua.globals().profile(self.profile).load()
            except Exception as e:
                self.log("Lua error: {}\n{}".format(str(e), traceback.format_exc()), "err")
        else:
            self.lua.loadFile(package.getResourceFilename("lua", "default.lua"))

        self.log("Session started.", "info")

    def destroy(self):
        self.lua.destroy()

    def event(self, ev):
        """
        This function handles incoming events (see event.py)
        """
        if isinstance(ev, event.RawEvent):
            text = None
            if self.encoding != "":
                try:
                    text = ev.data.decode(self.encoding)
                except UnicodeDecodeError as e:
                    self.encoding = "utf8"
                    self.put(LogEvent("Error decoding data. Switching to 'utf8'"))
                    try:
                        text = ev.data.decode(self.encoding)
                    except UnicodeDecodeError as e:
                        self.encoding = ""
                        self.push(event.LogEvent("Still no luck. Giving up, sorry. Maybe try a different encoding?"))
                        return

            lines = text.split("\n")

            for l in lines:
                self.lastBlock += l.strip() + " "

            firstLine = self.lastLine + lines[0]
            if len(lines) > 1:
                parsedLines = []
                for line in [firstLine] + lines[1:-1]:
                    parsedLines.append(self.ansi.parseToAString(line))
                for parsedLine in parsedLines:
                    ret = None
                    try:
                        ret = self.lua.triggerRecv(parsedLine)
                    except Exception as e:
                        self.log("Lua error in recv trigger: {}\n{}".format(str(e), traceback.format_exc()), "err")

                self.lastLine = lines[-1]
            else:
                self.lastLine = firstLine

        elif isinstance(ev, event.DisconnectEvent):
            self.log("Connection closed.", "info")
            self.luaHook("disconnect")
            self.telnet = None

        elif isinstance(ev, event.InputEvent):
            if ev.display:
                self.echo(self.getPromptLine() + colors.AString(ev.text).fg(colors.YELLOW))
            self.lastLine = ""

            self.processInput(ev.text)

        elif isinstance(ev, event.LuaEvent):
            self.luaEval(ev.code)

        elif isinstance(ev, telnet.TelnetEvent):
            self.put(event.LogEvent("Received Telneg {}".format(ev)))

            if ev.option == telnet.OPT_ECHO:
                if ev.cmd == telnet.WILL:
                    self.local_echo = True
                elif ev.cmd == telnet.WONT:
                    self.local_echo = False
            elif ev.option == telnet.OPT_NAWS and ev.cmd == telnet.DO and self.telnet is not None:
                self.telnet.sendIAC(telnet.WILL, telnet.OPT_NAWS)
                self.telnet.sendNaws(self.width, self.height)

            self.luaHook("telneg", ev.cmd, ev.option, ev.data)

        elif isinstance(ev, telnet.GMCPEvent):
            self.luaHook("gmcp", ev.module, ev.data)

        elif isinstance(ev, event.GridResizeEvent):
            self.width = ev.w
            self.height = ev.h

            if self.telnet is not None:
                self.telnet.sendNaws(ev.w, ev.h)

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

    def processInput(self, text):
        for l in text.split("\n"):
            ret = None
            try:
                ret = self.lua.triggerSend(l)
            except Exception as e:
                self.log("Lua error in send trigger: {}\n{}".format(str(e), traceback.format_exc()), "err")

    def send(self, text):
        if self.telnet:
            self.telnet.write((text + "\n").encode(self.encoding))

    def getLastLine(self):
        return ansi.Ansi().parseToAString(self.lastLine)
    def getPromptLine(self):
        if self.promptLine == "":
            return self.getLastLine()
        else:
            return ansi.Ansi().parseToAString(self.promptLine)

    def markPrompt(self):
        self.promptLine = self.lastLine
        self.lastLine = ""

        try:
            ret = self.lua.triggerBlock(ansi.Ansi().parseToAString(self.lastBlock))
        except Exception as e:
            self.log("Lua error in block trigger: {}\n{}".format(str(e), traceback.format_exc()), "err")

        self.lastBlock = ""

    def echo(self, string, lb='main'):
        if lb not in self.linebuffers:
            self.linebuffers[lb] = linebuffer.Linebuffer()

        self.linebuffers[lb].echo(string)

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
            self.echo(colors.AString("-> {}".format(ret)).fg(colors.MAGENTA))

    def setRPCSocket(self, sock):
        if self.rpc:
            self.rpc.stop()

        self.rpc = sock
        self.rpc.bind(self)
        self.rpc.start()

    def log(self, msg, level="info"):
        self.echo("-- {}".format(msg))

    # LUA FUNCTIONS

    def quit(self):
        self.put(event.QuitEvent())

    def connect(self, host, port):
        if self.telnet:
            self.log("Already connected")
            return

        self.log("Connecting to {}:{} ...".format(host, port), "info")

        try:
            sock = telnet.TCPSocket()
            self.telnet = telnet.Telnet(sock)
            self.telnet.bind(self)
            sock.connect(host, port)
            self.telnet.start()
        except Exception as e:
            self.telnet = None
            self.log("Could not connect: {}".format(str(e)))
            return

        self.log("Connection established.", "info")
        self.luaHook("connect", host, port)

    def status(self, string=None):
        if string is None:
            pass
        else:
            self.userStatus = ansi.Ansi().parseToAString(string)
        return str(self.userStatus)

