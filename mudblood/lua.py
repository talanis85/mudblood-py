import os
import lupa
import codecs
import traceback

from mudblood import linebuffer
from mudblood import window
from mudblood import event
from mudblood import map
from mudblood import colors
from mudblood import ansi
from mudblood import flock
from mudblood import telnet

class Lua(object):
    def __init__(self, session, packagePath):
        self.packagePath = packagePath
        self.session = session

        self.currentProfile = None
        self.profilePath = "."
        self.loadPath = self.profilePath

        self.lua = None

        self.luaInit()

    def luaInit(self):
        if self.lua is not None:
            self.lua.globals().map.close()

        self.lua = lupa.LuaRuntime()

        g = self.lua.globals()

        g.package.path = self.packagePath

        self.tryExecute("colors = require 'colors'")
        self.tryExecute("events = require 'events'")
        self.tryExecute("triggers = require 'triggers'")
        self.tryExecute("mapper = require 'mapper'")
        self.tryExecute("require 'help'")

        self.tryExecute("require 'common'")

        g.ctxGlobal = Lua_Context(self)
        g.ctxRoom = Lua_Context(self)
        g.ctxPrompt = Lua_Context(self)

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
        g.profile = self.profile
        g.listProfiles = self.listProfiles

        g.telnet = Lua_Telnet(self)
        g.map = Lua_Map(self)

        g.markPrompt = self.markPrompt

        g.screen = self.session.master.screen.getLuaScreen(self)

    def destroy(self):
        try:
            self.lua.globals().map.close()
        except:
            pass

    def loadFile(self, filename):
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
        g.triggers.queryListsAndSend.coroutine(
                self.lua.table(g.ctxPrompt.sendTriggers, g.ctxRoom.sendTriggers, g.ctxGlobal.sendTriggers),
                line).send(None)
    
    def triggerRecv(self, line):
        g = self.lua.globals()
        g.triggers.queryListsAndEcho.coroutine(
                self.lua.table(g.ctxPrompt.recvTriggers, g.ctxRoom.recvTriggers, g.ctxGlobal.recvTriggers),
                line).send(None)

    def triggerBlock(self, line):
        g = self.lua.globals()
        g.triggers.queryLists.coroutine(
                self.lua.table(g.ctxPrompt.blockTriggers, g.ctxRoom.blockTriggers, g.ctxGlobal.blockTriggers),
                line).send(None)

    def triggerTime(self):
        g = self.lua.globals()

        cr = g.ctxRoom.timers.query.coroutine(g.ctxRoom.timers)
        cr.send(None)

        cr = g.ctxGlobal.timers.query.coroutine(g.ctxGlobal.timers)
        cr.send(None)

    # Lua functions

    def connect(self, host, port):
        self.session.connect(host, port)

    def mode(self, m):
        self.session.put(event.ModeEvent(m))

    def send(self, data, args={}):
        self.session.processInput(data)

    def directSend(self, data):
        self.session.send(data)

    def echo(self, ob, buf='main'):
        if isinstance(ob, colors.AString):
            self.session.echo(ob, buf)
        elif isinstance(ob, basestring):
            self.session.echo(ansi.Ansi().parseToAString(ob), buf)
        else:
            self.session.echo(colors.AString(str(ob)), buf)

    def stripColors(self, string):
        if not isinstance(string, basestring):
            self.error("String expected")

        return str(ansi.Ansi().parseToAString(string))

    def load(self, filename):
        path = os.path.abspath(os.path.join(self.loadPath, filename))

        oldLoadPath = self.loadPath
        self.loadPath = os.path.dirname(path)
        ret = self.lua.globals().dofile(path)
        self.loadPath = oldLoadPath

        return ret

    def prompt(self, text, call, completion=None):
        if completion is not None:
            completion = [v for v in completion.values()]

        self.session.put(event.ModeEvent("prompt", text=text, call=call, completion=completion))

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

    def markPrompt(self):
        self.session.markPrompt()
        self.lua.globals().ctxPrompt.reset()

    def profile(self, name=None):
        if name is None:
            name = self.currentProfile

        if not os.path.exists(os.path.join(name, "profile.lua")):
            return None

        return Lua_Profile(self, name)

    def listProfiles(self):
        ret = []
        for r, ds, _ in os.walk("."):
            for d in ds:
                if os.path.exists(os.path.join(r, d, "profile.lua")):
                    ret.append(os.path.normpath(os.path.join(r, d)))

        return self.lua.table(*ret)

class LuaExposedObject(object):
    def __init__(self, lua):
        self._lua = lua

    def __str__(self):
        return "MudbloodObject"

    def __repr__(self):
        return self.__str__()

class Lua_Profile(LuaExposedObject):
    def __init__(self, lua, path):
        super(Lua_Profile, self).__init__(lua)
        self._path = path

    def load(self):
        self._lua.luaInit()
        self._lua.currentProfile = self._path
        self._lua.profilePath = os.path.abspath(self._path)
        self._lua.loadPath = self._lua.profilePath
        self._lua.loadFile(os.path.join(self._path, "profile.lua"))

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
        self.waitBlock = lua.eval("function (self, trigs) return triggers.yield(trigs, self.blockTriggers) end")
        self.waitSend = lua.eval("function (self, trigs) return triggers.yield(trigs, self.sendTriggers) end")
        self.waitTime = lua.eval("function (self, trigs) return triggers.yield(trigs, self.timers) end")

        self.reset()

    def reset(self):
        self.sendTriggers = self._lua.lua.globals().triggers.TriggerList.create()
        self.recvTriggers = self._lua.lua.globals().triggers.TriggerList.create()
        self.blockTriggers = self._lua.lua.globals().triggers.TriggerList.create()
        self.timers = self._lua.lua.globals().triggers.TriggerList.create()

class Lua_Telnet(LuaExposedObject):
    # Constants

    IAC = 255

    EOR = 239
    SE = 240
    NOP = 241
    DM = 242
    BRK = 243
    IP = 244
    AO = 245
    AYT = 246
    EC = 247
    EL = 248
    GA = 249

    SB = 250
    WILL = 251
    WONT = 252
    DO = 253
    DONT = 254


    OPT_ECHO = 1
    OPT_SUPPRESS_GA = 3
    OPT_TIMING_MARK = 6
    OPT_TTYPE = 24
    OPT_EOR = 25
    OPT_NAWS = 31
    OPT_LINEMODE = 34

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

    def gmcpObject(self, module, ob):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendGMCP(telnet.GMCPEvent(module=module, obj=dict(ob)))
    def gmcpArray(self, module, ob):
        if not self._lua.session.telnet: raise Exception("Not connected")
        arr = []
        for i in ob.values():
            arr.append(i)
        self._lua.session.telnet.sendGMCP(telnet.GMCPEvent(module=module, obj=arr))
    def gmcpValue(self, module, ob):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendGMCP(telnet.GMCPEvent(module=module, obj=ob))

    def gmcpFlag(self, module):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendGMCP(telnet.GMCPEvent(module=module))

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

    def visible(self, v):
        self._lua.session.put(event.ScreenConfigEvent("map.visible", v))

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

    def invalidateWeightCache(self):
        self._lua.session.map.invalidateWeightCache()

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
