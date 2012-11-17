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
import map

from mudblood import MB

class Session(event.Source):
    def __init__(self, script=None):
        super().__init__()

        self.lua = lua.Lua(self, os.path.join(MB().path, "lua/?.lua"))

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

        if script:
            self.log("Loading {}".format(script), "info")
            try:
                self.lua.loadFile(script + "/profile.lua")
            except Exception as e:
                self.log("Lua error: {}\n{}".format(str(e), traceback.format_exc()), "err")

        self.log("Session started.", "info")

    def event(self, ev):

        # EVENT DISPATCHER

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
            for l in reversed(ev.text.split("\n")):
                if ev.display:
                    self.print(self.getPromptLine() + colors.AString(l).fg(colors.YELLOW))
                    self.lastLine = ""

                ret = None
                try:
                    ret = self.lua.triggerSend(l)
                except Exception as e:
                    self.log("Lua error in send trigger: {}\n{}".format(str(e), traceback.format_exc()), "err")

                if ret is None:
                    self.push(event.DirectInputEvent(l))
                elif ret is False:
                    pass
                else:
                    self.push(event.DirectInputEvent(ret))
        elif isinstance(ev, event.DirectInputEvent):
            self.push(event.SendEvent(ev.text + "\n"))
        elif isinstance(ev, event.SendEvent):
            self.telnet.write((ev.data).encode(self.encoding))

        elif isinstance(ev, telnet.TelnetEvent):
            self.luaHook("telneg", ev.cmd, ev.option, ev.data)

        if ev.continuation:
            ev.continuation()
    
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

    def log(self, msg, level="info"):
        self.print("-- {}".format(msg))

    # LUA FUNCTIONS

    def quit(self):
        MB().drain.put(event.QuitEvent())

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

        self.telnet.bind(MB().drain)
        self.log("Connection established.", "info")
        self.luaHook("connect", host, port)
        self.telnet.start()

    def status(self, string=None):
        if string is None:
            pass
        else:
            self.userStatus = string
        return self.userStatus

