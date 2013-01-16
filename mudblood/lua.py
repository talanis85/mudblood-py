import os
import lupa
import codecs
import traceback

from mudblood import linebuffer
from mudblood import event
from mudblood import map
from mudblood import rpc
from mudblood import colors
from mudblood import ansi
from mudblood import flock

class Lua(object):
    def __init__(self, session, packagePath):
        self.packagePath = packagePath
        self.session = session
        self.profilePath = "."
        self.filename = None

        self.luaInit()

    def luaInit(self):
        self.lua = lupa.LuaRuntime()

        g = self.lua.globals()

        g.package.path = self.packagePath

        self.tryExecute("colors = require 'colors'")
        self.tryExecute("events = require 'events'")
        self.tryExecute("triggers = require 'triggers'")
        self.tryExecute("mapper = require 'mapper'")
        self.tryExecute("profile = require 'profile'")
        self.tryExecute("help = require 'help'")

        self.tryExecute("require 'common'")

        g.ctxGlobal = Lua_Context(self)
        g.ctxRoom = Lua_Context(self)

        g.reload = self.reload
        g.quit = self.session.quit
        g.mode = self.mode
        g.connect = self.connect
        setattr(g, "print", self.echo)
        g.status = self.session.status
        g.send = self.send
        g.directSend = self.directSend
        g.nmap = self.nmap
        g.prompt = self.prompt
        g.stripColors = self.stripColors
        g.load = self.load
        g.config = self.config
        g.editor = self.editor
        g.path = Lua_Path(self)
        g.rpcClient = self.rpcClient
        g.rpcServer = self.rpcServer

        g.telnet = Lua_Telnet(self)
        g.map = Lua_Map(self)

        g.markPrompt = self.markPrompt

    def destroy(self):
        try:
            self.lua.globals().map.close()
        except:
            pass

    def loadFile(self, filename):
        self.profilePath = os.path.abspath(os.path.dirname(filename))
        self.loadPath = self.profilePath
        self.filename = filename

        self.lua.globals().dofile(filename)
    
    def toString(self, ob):
        if isinstance(ob, lupa._lupa._LuaTable):
            return "{" + ", ".join([str(e) for e in ob]) + "}"
        else:
            return str(ob)

    def error(self, msg):
        raise lupa.LuaError(msg)

    def execute(self, command):
        return self.lua.execute(command)

    def tryExecute(self, command):
        try:
            return self.lua.execute(command)
        except lupa.LuaError as e:
            self.session.log(str(e), "err")

    def eval(self, command):
        return self.lua.eval(command)

    def call(self, function, *args):
        if getattr(self.lua.globals(), function):
            return getattr(self.lua.globals(), function)(*args)
        else:
            raise KeyError()

    def hook(self, hook, *args):
        return self.lua.globals().events.call(hook, self.lua.table(*args))

    def triggerSend(self, line):
        g = self.lua.globals()
        g.triggers.queryListsAndSend.coroutine(self.lua.table(g.ctxRoom.sendTriggers, g.ctxGlobal.sendTriggers), line).send(None)
    
    def triggerRecv(self, line):
        g = self.lua.globals()
        g.triggers.queryListsAndEcho.coroutine(self.lua.table(g.ctxRoom.recvTriggers, g.ctxGlobal.recvTriggers), line).send(None)

    def triggerTime(self):
        g = self.lua.globals()

        cr = g.ctxRoom.timers.query.coroutine(g.ctxRoom.timers)
        cr.send(None)

        cr = g.ctxGlobal.timers.query.coroutine(g.ctxGlobal.timers)
        cr.send(None)

    # Lua functions

    def reload(self):
        if self.filename is None:
            self.error("No file loaded")
        else:
            self.lua.globals().map.close()
            self.luaInit()
            self.loadFile(self.filename)
    
    def connect(self, host, port):
        self.session.connect(host, port)

    def mode(self, m):
        self.session.put(event.ModeEvent(m))

    def send(self, data, args={}):
        self.session.processInput(data)

    def directSend(self, data):
        self.session.send(data)

    def echo(self, ob):
        if isinstance(ob, colors.AString):
            self.session.echo(ob)
        elif isinstance(ob, basestring):
            self.session.echo(ansi.Ansi().parseToAString(ob))
        else:
            self.session.echo(colors.AString(str(ob)))

    def stripColors(self, string):
        if not isinstance(string, basestring):
            self._error("String expected")

        return str(ansi.Ansi().parseToAString(string))

    def load(self, filename):
        path = os.path.abspath(os.path.join(self.loadPath, filename))

        oldLoadPath = self.loadPath
        self.loadPath = os.path.dirname(path)
        ret = self.lua.globals().dofile(path)
        self.loadPath = oldLoadPath

        return ret

    def prompt(self, text, call):
        self.session.put(event.ModeEvent("prompt", text=text, call=call))

    def nmap(self, key, value=None):
        if value is None:
            try:
                self.session.bindings.delete(self.session.bindings.parse(key))
            except:
                self.error("No binding for " + key + " found.")
        else:
            self.session.bindings.add(self.session.bindings.parse(key), value)

    def config(self, key, value):
        if key == "encoding":
            try:
                codecs.lookup(value)
                self.session.encoding = value
            except:
                self.error("Encoding {} not supported".format(value))

    def editor(self, content):
        self.error("Editor not supported for now.")
        #return MB().screen.editor(content)

    def rpcClient(self, type, path):
        if type == "unix":
            return Lua_RPCObject(self, path)
        else:
            self.error("Supported socket types: unix")

    def rpcServer(self, type, addr):
        if type == "unix":
            self.session.setRPCSocket(rpc.RPCServerSocket(addr))
        else:
            self.error("Supported socket types: unix")

    def markPrompt(self):
        self.session.promptLine = self.session.lastLine
        self.session.lastLine = ""

class LuaExposedObject(object):
    def __init__(self, lua):
        self._lua = lua

    def __str__(self):
        return "MudbloodObject"

    def __repr__(self):
        return self.__str__()

class Lua_Path(LuaExposedObject):
    def profile(self):
        return self._lua.profilePath

    def library(self):
        return os.path.dirname(self._lua.packagePath)

    def profileBase(self):
        return os.path.join(os.environ['HOME'], ".config", "mudblood-py")

class Lua_Context(LuaExposedObject):
    def __init__(self, lua):
        super(Lua_Context, self).__init__(lua)

        # Must be a pure lua function as we cannot yield across the Lua-Python boundary.
        self.wait = lua.eval("function (self, trigs) return triggers.yield(trigs, self.recvTriggers) end")
        self.waitSend = lua.eval("function (self, trigs) return triggers.yield(trigs, self.sendTriggers) end")
        self.waitTime = lua.eval("function (self, trigs) return triggers.yield(trigs, self.timers) end")

        self.reset()

    def reset(self):
        self.sendTriggers = self._lua.lua.globals().triggers.TriggerList.create()
        self.recvTriggers = self._lua.lua.globals().triggers.TriggerList.create()
        self.timers = self._lua.lua.globals().triggers.TriggerList.create()

class Lua_RPCObject(LuaExposedObject):
    def __init__(self, lua, port, stack=[]):
        self._lua = lua
        self._port = port
        self._stack = stack

    def call(self, string):
        if self._stack != []:
            self._lua.error("Only the top RPC object supports literal calls.")
        else:
            rpc.callLiteral(self._port, string)

    def __call__(self, *args):
        if self._stack == []:
            self._lua.error("Base RPCObject not callable.")
        else:
            rpc.call(self._port, self._stack, args)
        return None

    def __getattr__(self, key):
        if hasattr(super(Lua_RPCObject, self), key):
            return getattr(super(Lua_RPCObject, self), key)
        else:
            return Lua_RPCObject(self._lua, self._port, self._stack + [key])

    def __getitem__(self, key):
        return self.__getattr__(key)

class Lua_Telnet(LuaExposedObject):
    # Constants

    IAC = 255

    WILL = 251
    WONT = 252
    DO = 253
    DONT = 254

    NOP = 241

    SB = 250
    SE = 240

    SUPPRESS_GA = 3
    DO_EOR = 25

    EOR = 239
    GA = 249

    def negWill(self, option):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendIAC(self.WILL, option)
    def negWont(self, option):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendIAC(self.WONT, option)
    def negDo(self, option):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendIAC(self.DO, option)
    def negDont(self, option):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendIAC(self.DONT, option)
    def negSubneg(self, option, data):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendSubneg(option, data)

class Lua_Map(LuaExposedObject):
    NORTH       = map.NORTH
    NORTHEAST   = map.NORTHEAST
    EAST        = map.EAST
    SOUTHEAST   = map.SOUTHEAST
    SOUTH       = map.SOUTH
    SOUTHWEST   = map.SOUTHWEST
    WEST        = map.WEST
    NORTHWEST   = map.NORTHWEST

    def __init__(self, lua):
        super(Lua_Map, self).__init__(lua)
        self._filename = None
        self._flock = None

    def room(self, id=None):
        if id is None:
            return Lua_Map_Room(self._lua, self._lua.session.map.currentRoom)
        else:
            return Lua_Map_Room(self._lua, self._lua.session.map.findRoom(id))

    def addRoom(self):
        return Lua_Map_Room(self._lua, self._lua.session.map.addRoom().id)

    def getVisible(self):
        return self._lua.session.mapWindow.visible
    def setVisible(self, v):
        self._lua.session.mapWindow.visible = v

    visible = property(getVisible, setVisible)

    def getDirections(self):
        return self._lua.lua.table(**self._lua.session.map.dirConfig)
    def setDirections(self, v):
        self._lua.session.map.dirConfig = dict(v)

    directions = property(getDirections, setDirections)

    def load(self, filename, mode="r"):
        oldCurrentRoom = self._lua.session.map.currentRoom

        if mode == "w":
            if self._flock:
                self._flock.release()

            try:
                self._flock = flock.Lock(filename)
            except flock.LockedException:
                self._lua.error("Map file is already locked.")

        with open(filename, "r") as f:
            self._lua.session.map.load(f)

        self._filename = filename

        self._lua.session.map.goto(oldCurrentRoom)

    def close(self):
        if self._filename is None:
            return
        if self._flock is not None:
            self._flock.release()
            self._flock = None
            self._filename = None

    def save(self, filename=None):
        if filename is None:
            filename = self._filename

        if filename == self._filename:
            if self._flock is None:
                self._lua.error("To save, the map must be opened with mode 'w'")
        else:
            try:
                templock = flock.Lock(filename)
                templock.release()
            except flock.LockedException:
                self._lua.error("Map file {} is locked.".format(filename))

        with open(filename, "w") as f:
            self._lua.session.map.save(f)

class Lua_Map_Room(LuaExposedObject):
    def __init__(self, lua, rid):
        super(Lua_Map_Room, self).__init__(lua)
        self._roomId = self._lua.session.map.findRoom(rid)
        self._valid = True

    def __str__(self):
        self._checkValid()
        r = self._lua.session.map.rooms[self._roomId]
        return "Room #{} ({})".format(r.id, (r.tag or "no tag"))

    def _checkValid(self):
        if not self._valid:
            self._lua.error("Room '{}' is no longer valid.".format(self._roomId))

    def getId(self):
        return self._roomId

    id = property(getId)

    def getEdges(self):
        self._checkValid()
        return self._lua.lua.table(**dict([(str(e), Lua_Map_Edge(self._lua, self._roomId, e))
                     for e in self._lua.session.map.rooms[self._roomId].getEdges()]))

    edges = property(getEdges)

    def delete(self):
        self._checkValid()
        for e in self._lua.session.map.rooms[self._roomId].edges:
            Lua_Map_Edge(self._lua, self._roomId, e).delete(True)

        del self._lua.session.map.rooms[self._roomId]
        self._valid = False

    def getUserdata(self, key):
        self._checkValid()
        return self._lua.session.map.rooms[self._roomId].userdata.get(key)
    def setUserdata(self, key, value):
        self._checkValid()
        self._lua.session.map.rooms[self._roomId].userdata[key] = value

    def getTag(self):
        self._checkValid()
        return self._lua.session.map.rooms[self._roomId].tag
    def setTag(self, tag):
        self._checkValid()
        self._lua.session.map.rooms[self._roomId].tag = tag
    tag = property(getTag, setTag)

    def connect(self, other, name, opposite=None):
        self._checkValid()
        if name in self._lua.session.map.rooms[self._roomId].edges:
            self._lua.error("Edge '{}' already present in {}".format(name, str(self)))
        if opposite and opposite in self._lua.session.map.rooms[other._roomId].edges:
            self._lua.error("Edge '{}' already present in {}".format(opposite, str(other)))

        e1 = map.Edge(self._lua.session.map.rooms[other._roomId])
        self._lua.session.map.rooms[self._roomId].edges[name] = e1
        if opposite:
            e2 = map.Edge(self._lua.session.map.rooms[self._roomId])
            self._lua.session.map.rooms[other._roomId].edges[opposite] = e2

    def findNeighbor(self, d):
        self._checkValid()
        self.neighbor = None

        if d not in self._lua.session.map.dirConfig:
            return None

        dx, dy = map.getDirectionDelta(self._lua.session.map.dirConfig[d])

        def dfs_callback(r):
            if self._lua.session.map.rooms[self._roomId].x + dx == r.x and self._lua.session.map.rooms[self._roomId].y + dy == r.y:
                self.neighbor = r

        self._lua.session.map.dfs(self._lua.session.map.rooms[self._roomId], dfs_callback)
        if self.neighbor:
            return Lua_Map_Room(self._lua, self.neighbor.id)
        else:
            return None

    def fly(self):
        self._checkValid()
        self._lua.session.map.goto(self._roomId)
        self._lua.hook("room")

    def getPath(self, to, weightFunction=None):
        self._checkValid()
        if weightFunction:
            def wf(r, d):
                return weightFunction(Lua_Map_Room(self._lua, r), Lua_Map_Edge(self._lua, r, d))
            return self._lua.lua.table(*self._lua.session.map.shortestPath(self._roomId, to._roomId, wf))
        else:
            return self._lua.lua.table(*self._lua.session.map.shortestPath(self._roomId, to._roomId))

class Lua_Map_Edge(LuaExposedObject):
    def __init__(self, lua, rid, edge):
        super(Lua_Map_Edge, self).__init__(lua)
        self._roomId = rid
        self._edge = edge
        self._valid = True

    def __str__(self):
        self._checkValid()
        return "Edge '{}' from Room #{} to Room #{}".format(self._edge,
                                                            self._roomId,
                                                            self._lua.session.map.rooms[self._roomId].getEdges()[self._edge].dest.id)

    def _checkValid(self):
        if not self._valid:
            self._lua.error("Edge '{}' is no longer valid.".format(self._edge))

    def getName(self):
        return self._edge

    name = property(getName)

    def delete(self, twoway=False):
        self._checkValid()

        if twoway:
            for k in self._lua.session.map.rooms[self._roomId].edges[self._edge].dest.edges.keys():
                if self._lua.session.map.rooms[self._roomId].edges[self._edge].dest.edges[k].dest == self._lua.session.map.rooms[self._roomId]:
                    del self._lua.session.map.rooms[self._roomId].edges[self._edge].dest.edges[k]
                    break

        del self._lua.session.map.rooms[self._roomId].edges[self._edge]
        self._valid = False

    def getTo(self):
        self._checkValid()
        return Lua_Map_Room(self._lua,
                            self._lua.session.map.rooms[self._roomId].getEdges()[self._edge].dest.id)

    def setTo(self, room):
        self._checkValid()

        rid = 0
        if isinstance(room, int):
            rid = room
        elif isinstance(room, Lua_Map_Room):
            rid = room._roomId
        else:
            raise Exception("Room object or Room ID required")

        if rid in self._lua.session.map.rooms:
            self._lua.session.map.rooms[self._roomId].edges[self._edge].dest = self._lua.session.map.rooms[rid]
        else:
            raise Exception("Destination room not found")

    to = property(getTo, setTo)

    def getSplit(self):
        self._checkValid()
        return self._lua.session.map.rooms[self._roomId].edges[self._edge].split

    def setSplit(self, split):
        self._checkValid()
        self._lua.session.map.rooms[self._roomId].getEdges()[self._edge].split = split

    split = property(getSplit, setSplit)

    def getWeight(self):
        self._checkValid()
        return self._lua.session.map.rooms[self._roomId].getEdges()[self._edge].weight

    def setWeight(self, weight):
        self._checkValid()
        self._lua.session.map.rooms[self._roomId].getEdges()[self._edge].weight = weight

    weight = property(getWeight, setWeight)

    def getUserdata(self, key):
        self._checkValid()
        return self._lua.session.map.rooms[self._roomId].getEdges()[self._edge].userdata.get(key)
    def setUserdata(self, key, value):
        self._checkValid()
        self._lua.session.map.rooms[self._roomId].getEdges()[self._edge].userdata[key] = value
