import os
import lupa
import codecs
import traceback

from mudblood import linebuffer
from mudblood import event
from mudblood import map
from mudblood import rpc

from mudblood.main import MB

class Lua(object):
    def __init__(self, session, packagePath):
        self.packagePath = packagePath
        self.session = session
        self.profilePath = "."
        self.filename = None

        self.luaInit()

    def luaInit(self):
        self.lua = lupa.LuaRuntime()

        self.lua.execute("package.path = '{}'".format(self.packagePath))

        self.lua.execute("colors = require 'colors'")
        self.lua.execute("events = require 'events'")
        self.lua.execute("triggers = require 'triggers'")
        self.lua.execute("mapper = require 'mapper'")

        self.lua.execute("require 'aux'")

        g = self.lua.globals()

        g.ctxGlobal = Lua_Context(self)
        g.ctxRoom = Lua_Context(self)

        g.reload = self.reload
        g.quit = self.session.quit
        g.mode = self.mode
        g.connect = self.connect
        g.print = self.print
        g.status = self.session.status
        g.send = self.send
        g.directSend = self.directSend
        g.nmap = self.nmap
        g.prompt = self.prompt
        g.load = self.load
        g.config = self.config
        g.editor = self.editor
        g.path = Lua_Path(self)
        g.rpcClient = self.rpcClient
        g.rpcServer = self.rpcServer

        g.telnet = Lua_Telnet(self)
        g.map = Lua_Map(self)

        g.markPrompt = self.markPrompt

    def loadFile(self, filename):
        self.profilePath = os.path.abspath(os.path.dirname(filename))
        self.filename = filename
        with open(filename, "r") as f:
            self.lua.execute(f.read())
    
    def toString(self, ob):
        if isinstance(ob, lupa._lupa._LuaTable):
            return "{" + ", ".join([str(e) for e in ob]) + "}"
        else:
            return str(ob)

    def error(self, msg):
        raise lupa.LuaError(msg)

    def execute(self, command):
        return self.lua.execute(command)

    def eval(self, command):
        return self.lua.eval(command)

    def call(self, function, *args):
        if getattr(self.lua.globals(), function):
            return getattr(self.lua.globals(), function)(*args)
        else:
            raise KeyError()

    def hook(self, hook, *args):
        return self.lua.globals().events.call(hook, *args)

    def triggerSend(self, line):
        g = self.lua.globals()
        g.triggers.queryListsAndSend.coroutine(self.lua.table(g.ctxRoom.sendTriggers, g.ctxGlobal.sendTriggers), line).send(None)
    
    def triggerRecv(self, line):
        g = self.lua.globals()
        gret = None

        crRet = g.ctxRoom.recvTriggers.query.coroutine(g.ctxRoom.recvTriggers, line).send(None)
        if crRet is None:
            return False

        ret, _, _ = crRet
        if ret is not None:
            line = ret
            gret = ret

        crRet = g.ctxGlobal.recvTriggers.query.coroutine(g.ctxGlobal.recvTriggers, line).send(None)
        if crRet is None:
            return False

        ret, _, _ = crRet
        if ret is not None:
            line = ret
            gret = ret

        return gret

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
            self.luaInit()
            self.loadFile(self.filename)
    
    def connect(self, host, port):
        self.session.connect(host, port)

    def mode(self, m):
        self.session.put(event.ModeEvent(m))

    def send(self, data, args={}):
        def cont():
            try:
                # This has to be executed as a coroutine, otherwise the continuation
                # function would be ran not in the main thread but in the lua thread
                # where send() was called. No idea why.
                args['continuation'].coroutine().send(None)
            except StopIteration:
                pass
            except Exception as e:
                self.session.log("Lua error in event continuation: {}\n{}".format(str(e), traceback.format_exc()), "err")

        ev = event.InputEvent(data)

        if "continuation" in args:
            ev.continuation = cont
        if "display" in args:
            ev.display = args['display']

        self.session.put(ev)

    def directSend(self, data):
        self.session.put(event.DirectInputEvent(data))

    def print(self, ob):
        self.session.put(event.EchoEvent(self.toString(ob)))

    def load(self, filename):
        with open(os.path.join(self.profilePath, filename), "r") as f:
            #return self.lua.execute(f.read())
            return self.lua.globals().loadstring(f.read())()

    def prompt(self, text, call):
        self.session.put(event.ModeEvent("prompt", text=text, call=call))

    def nmap(self, key, value=None):
        if value is None:
            self.session.bindings.delete(self.session.bindings.parse(key))
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
        return MB().screen.editor(content)

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

class Lua_Context(LuaExposedObject):
    def __init__(self, lua):
        super().__init__(lua)

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
        if hasattr(super(), key):
            return getattr(super(), key)
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

    DO_EOR = 25
    EOR = 239

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

    def load(self, filename):
        oldCurrentRoom = self._lua.session.map.currentRoom

        with open(filename, "r") as f:
            self._lua.session.map.load(f)

        self._lua.session.map.goto(oldCurrentRoom)

    def load_old(self, filename):
        oldCurrentRoom = self._lua.session.map.currentRoom

        with open(filename, "r") as f:
            self._lua.session.map.load_old(f)

        self._lua.session.map.goto(oldCurrentRoom)

    def save(self, filename):
        with open(filename, "w") as f:
            self._lua.session.map.save(f)

class Lua_Map_Room(LuaExposedObject):
    def __init__(self, lua, rid):
        super().__init__(lua)
        self._roomId = self._lua.session.map.findRoom(rid)

    def __str__(self):
        r = self._lua.session.map.rooms[self._roomId]
        return "Room #{} ({})".format(r.id, (r.tag or "no tag"))

    def getEdges(self):
        return self._lua.lua.table(**dict([(e, Lua_Map_Edge(self._lua, self._roomId, e))
                     for e in self._lua.session.map.rooms[self._roomId].getEdges()]))

    edges = property(getEdges)

    def getUserdata(self, key):
        return self._lua.session.map.rooms[self._roomId].userdata.get(key)
    def setUserdata(self, key, value):
        self._lua.session.map.rooms[self._roomId].userdata[key] = value

    def getTag(self):
        return self._lua.session.map.rooms[self._roomId].tag
    def setTag(self, tag):
        self._lua.session.map.rooms[self._roomId].tag = tag
    tag = property(getTag, setTag)

    def connect(self, other, name, opposite=None):
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
        neighbor = None
        dx, dy = map.getDirectionDelta(self._lua.session.map.dirConfig[d])

        def dfs_callback(r):
            if self._lua.session.map.rooms[self._roomId].x + dx == r.x and self._lua.session.map.rooms[self._roomId].y + dy == r.y:
                neighbor = r

        self._lua.session.map.dfs(self._lua.session.map.rooms[self._roomId], dfs_callback)
        if neighbor:
            return Lua_Map_Room(self._lua, neighbor.id)
        else:
            return None

    def fly(self):
        self._lua.session.map.goto(self._roomId)
        self._lua.hook("room")

    def getPath(self, to, weightFunction=None):
        if weightFunction:
            def wf(r, d):
                return weightFunction(Lua_Map_Room(self._lua, r), Lua_Map_Edge(self._lua, r, d))
            return self._lua.lua.table(*self._lua.session.map.shortestPath(self._roomId, to._roomId, wf))
        else:
            return self._lua.lua.table(*self._lua.session.map.shortestPath(self._roomId, to._roomId))

class Lua_Map_Edge(LuaExposedObject):
    def __init__(self, lua, rid, edge):
        super().__init__(lua)
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
