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

    def convertToPython(self, ob):
        if not hasattr(ob, "items"):
            return ob

        ret = []
        for k,v in ob.items():
            if isinstance(k, int):
                ret.append(self.convertToPython(v))

        return ret

    def convertFromPython(self, ob):
        if isinstance(ob, list):
            return self.lua.table(*[self.convertFromPython(x) for x in ob])
        elif isinstance(ob, dict):
            self.error("Dictionaries are not supported in userdata")
        else:
            return ob

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
        elif isinstance(ob, lupa._lupa._LuaTable):
            self.session.echo("{" + ", ".join(["{}:{}".format(str(k),str(v)) for k,v in ob.items()]) + "}", buf)
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

    def editor(self, content, callback):
        self.session.put(event.ModeEvent("editor", content=content, callback=callback))

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
    
    #
    # Save and load
    #

    def load(self, filename, mode="r"):
        oldCurrentRoom = self._lua.session.map.currentRoom
        oldDirections = self._lua.session.map.dirConfig

        if mode == "w":
            if self._flock:
                self._flock.release()

            try:
                self._flock = flock.Lock(filename)
            except flock.LockedException:
                self._lua.error("Map file is already locked.")

        with open(filename, "r") as f:
            self._lua.session.map = map.Map.load(f)

        self._filename = filename
        self._lua.session.map.goto(oldCurrentRoom)
        self._lua.session.map.dirConfig = oldDirections

    def lock(self):
        if self._flock is not None:
            try:
                self._flock = flock.Lock(filename)
            except flock.LockedException:
                self._lua.error("Map file is already locked.")

    def close(self):
        self._lua.session.map = map.Map()
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

    #
    # Configuration
    #

    def getDirections(self):
        return self._lua.lua.table(**self._lua.session.map.dirConfig)
    def setDirections(self, v):
        self._lua.session.map.dirConfig = dict(v)

    directions = property(getDirections, setDirections)

    def getRenderOverlay(self):
        return self._lua.lua.table(*self._lua.session.map.renderOverlay)
    def setRenderOverlay(self, v):
        self._lua.session.map.renderOverlay = list(v.values())

    renderOverlay = property(getRenderOverlay, setRenderOverlay)

    #
    # Management
    #

    def addRoom(self):
        """
        Create a new room.
        @return A new Lua_Map_Room.
        """
        return Lua_Map_Room(self._lua, self._lua.session.map.addRoom())

    def room(self, id=None, index=None):
        """
        Find a room by id or custom index.
        @return A Lua_Map_Room or nil
        """
        if id is None:
            return Lua_Map_Room(self._lua, self._lua.session.map.findRoom(self._lua.session.map.currentRoom))
        else:
            if index is not None:
                r = self._lua.session.map.findRoom((index, id))
            else:
                r = self._lua.session.map.findRoom(id)

            if r is None:
                return None
            else:
                return Lua_Map_Room(self._lua, r)

class Lua_Map_Room(LuaExposedObject):
    def __init__(self, lua, room):
        super(Lua_Map_Room, self).__init__(lua)
        self._room = room

    def __str__(self):
        return "Room #{}".format(self._room.id)

    #
    # Attributes
    #

    def getId(self):
        return self._room.id

    id = property(getId)

    def overlay(self, overlay):
        """
        Return a table of edges for a given overlay.
        """
        edges = []
        for direction,edge in self._room.getOverlay(overlay.values()).items():
            edges.append((str(direction), Lua_Map_Edge(self._lua, self._room, direction, edge)))

        return self._lua.lua.table(**dict(edges))

    def edges(self):
        """
        Return all edges as a two-dimensional mapping of layers and edges.
        """
        ret = []
        for layer,edges in self._room.getLayers().items():
            cur = []
            for direction,edge in edges.items():
                cur.append((str(direction), Lua_Map_Edge(self._lua, self._room, direction, edge)))
            ret.append((str(layer), self._lua.lua.table(**dict(cur))))

        return self._lua.lua.table(**dict(ret))

    def getUserdata(self, key):
        return self._lua.convertFromPython(self._room.getUserdata(key))

    def setUserdata(self, key, value):
        self._room.setUserdata(key, self._lua.convertToPython(value))

    #
    # Connect and delete
    #

    def connect(self, layer, other, name, opposite=None):
        try:
            self._room.connect(layer, name, other._room)

            if opposite is not None:
                other._room.connect(layer, opposite, self._room)
        except map.DuplicateEdgeException:
            self._lua.error("Cannot create edge: Already present")

    def disconnect(self, layer, name, opposite=False):
        try:
            self._room.disconnect(layer, name)
        except map.DuplicateEdgeException:
            self._lua.error("Cannot delete edge: Not found")

        if opposite:
            for layer,direction,edge in self._room.getFlatLayers():
                for layer2,direction2,edge2 in edge.follow().getFlatLayers():
                    if edge2.follow() == self._room:
                        edge.follow().disconnect(layer2, direction2)

    def opposites(self, overlay, name):
        ret = []
        l = self._room.getOverlay(list(overlay.values()))
        if name in l:
            for layer,direction,edge in l[name].follow().getFlatLayers():
                if edge.follow() == self._room:
                    ret.append(self._lua.lua.table(Lua_Map_Room(self._lua, l[name].follow()), Lua_Map_Edge(self._lua, l[name].follow(), direction, edge)))
        return self._lua.lua.table(*ret)

    def findNeighbor(self, overlay, d):
        self.neighbor = None

        if d not in self._lua.session.map.dirConfig:
            return None

        dx, dy = map.getDirectionDelta(self._lua.session.map.dirConfig[d])

        def dfs_callback(r):
            if self._room.x + dx == r.x and self._room.y + dy == r.y:
                self.neighbor = r

        self._lua.session.map.dfsVisual(self._room, dfs_callback, overlay)
        if self.neighbor:
            return Lua_Map_Room(self._lua, self.neighbor.id)
        else:
            return None

    #
    # Movement
    #

    def goto(self):
        self._lua.session.map.goto(self._room.id)
        self._lua.hook("room")

    def shortestPath(self, to, layers, weightFunction=None):
        p = None
        if weightFunction:
            def wf(r, d, e):
                return weightFunction(Lua_Map_Room(self._lua, r), Lua_Map_Edge(self._lua, r, d, e))
            p = self._lua.session.map.shortestPath(self._room.id,
                                                   to._room.id,
                                                   list(layers.values()),
                                                   weightFunction=wf)
        else:
            p = self._lua.session.map.shortestPath(self._room.id,
                                                   to._room.id,
                                                   list(layers.values()))

        if p is None:
            return None
        else:
            return self._lua.lua.table(*list(p))

class Lua_Map_Edge(LuaExposedObject):
    def __init__(self, lua, room, direction, edge):
        super(Lua_Map_Edge, self).__init__(lua)
        self._room = room
        self._direction = direction
        self._edge = edge

    def __str__(self):
        return "Edge '{}' from Room #{} to Room #{}".format(self._direction,
                                                            self._room.id,
                                                            self._edge.follow().id)

    #
    # Attributes
    #

    def getName(self):
        return self._direction

    name = property(getName)

    def getLayer(self):
        return self._edge.layer

    layer = property(getLayer)

    def getSplit(self):
        return self._edge.split

    def setSplit(self, split):
        self._edge.split = split

    split = property(getSplit, setSplit)

    def getWeight(self):
        return self._edge.weight

    def setWeight(self, weight):
        self._edge.weight = weight

    weight = property(getWeight, setWeight)

    def getUserdata(self, key):
        return self._edge.getUserdata(key)

    def setUserdata(self, key, value):
        self._edge.setUserdata(key, value)

    #
    # Movement
    #

    def follow(self):
        return Lua_Map_Room(self._lua, self._edge.follow())

