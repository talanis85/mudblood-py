import os
import lupa
import linebuffer
import codecs
import event

from mudblood import MB

#def expose(f):
#    f._lua_expose = True
#    return f
#
#class LuaExposedObject(object):
#    def __init__(self, ob, attrName):
#        self.ob = ob
#        self.attrName = attrName
#
#    def __getitem__(self, key):
#        attr = getattr(self.ob, self.attrName)
#        if attr:
#            if hasattr(attr, "_luaVars"):
#                luaVars = attr._luaVars
#                if key in luaVars:
#                    return luaVars[key]
#            attr2 = getattr(attr, key)
#            if hasattr(attr2, "_lua_expose") and attr2._lua_expose:
#                return attr2
#            else:
#                raise KeyError("'{}' object has no attribute '{}'".format(attr.__class__.__name__, key))
#        else:
#            raise Exception("{} is not ready".format(self.attrName))

class Lua(object):
    def __init__(self, session, packagePath):
        self.lua = lupa.LuaRuntime()
        self.session = session
        self.profilePath = "."

        self.lua.execute("package.path = '{}'".format(packagePath))

        self.lua.execute("colors = require 'colors'")
        self.lua.execute("events = require 'events'")
        self.lua.execute("triggers = require 'triggers'")
        self.lua.execute("context = require 'context'")
        self.lua.execute("mapper = require 'mapper'")

        self.lua.execute("require 'aux'")

        g = self.lua.globals()

        g.quit = self.session.quit
        g.mode = MB().screen.mode
        g.connect = self.session.connect
        g.print = self.print
        g.status = self.session.status
        g.send = self.session.send
        g.directSend = self.session.directSend
        g.nmap = self.nmap
        g.dofile = self.dofile
        g.config = self.config
        g.path = Lua_Path(self)

        g.astring = linebuffer.AString

        g.telnet = Lua_Telnet(self)
        g.map = Lua_Map(self)

    def exposeObject(self, ob):
        ret = {}
        for att in ob.__dict__:
            att_ob = getattr(ob, att)
            if hasattr(att_ob, "_lua_expose") and att_ob._lua_expose:
                ret[att] = att_ob
        return ret

    def loadFile(self, filename):
        self.profilePath = os.path.abspath(os.path.dirname(filename))
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
    
    def contextSwitch(self, ctx):
        self.lua.execute("context.switch('{}')".format(ctx))

    # Lua functions

    def print(self, ob):
        self.session.lb.echo(self.toString(ob))

    def dofile(self, filename):
        with open(os.path.join(self.profilePath, filename), "r") as f:
            self.lua.execute(f.read())

    def nmap(self, key, value):
        self.session.bindings.parseAndAdd(key, value)

    def config(self, key, value):
        if key == "encoding":
            try:
                codecs.lookup(value)
                self.session.encoding = value
            except:
                self.error("Encoding {} not supported".format(value))

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
        self._lua.session.telnet.sendIAC(WILL, option)
    def negWont(self, option):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendIAC(WONT, option)
    def negDo(self, option):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendIAC(DO, option)
    def negDont(self, option):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendIAC(DONT, option)
    def negSubneg(self, option, data):
        if not self._lua.session.telnet: raise Exception("Not connected")
        self._lua.session.telnet.sendSubneg(option, data)

class Lua_Map(LuaExposedObject):
    def room(self, id=None):
        if id is None:
            return Lua_Map_Room(self._lua, self._lua.session.map.currentRoom)
        else:
            return Lua_Map_Room(self._lua, self._lua.session.map.findRoom(id))

    def getVisible(self):
        return self._lua.session.mapWindow.visible
    def setVisible(self, v):
        self._lua.session.mapWindow.visible = v

    visible = property(getVisible, setVisible)

    def load(self, filename):
        with open(filename, "r") as f:
            self._lua.session.map.load(f)

    def load_old(self, filename):
        with open(filename, "r") as f:
            self._lua.session.map.load_old(f)

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
                     for e in self._lua.session.map.rooms[self._roomId].edges]))

    edges = property(getEdges)

    def getUserdata(self):
        return self._lua.session.map.rooms[self._roomId].userdata

    userdata = property(getUserdata)

    def fly(self):
        self._lua.session.map.goto(self._roomId)

    def getPath(self, to):
        return self._lua.lua.table(*self._lua.session.map.shortestPath(self._roomId, to._roomId))

class Lua_Map_Edge(LuaExposedObject):
    def __init__(self, lua, rid, edge):
        super().__init__(lua)
        self._roomId = rid
        self._edge = edge

    def __str__(self):
        return "Edge '{}' from Room #{} to Room #{}".format(self._edge,
                                                            self._roomId,
                                                            self._lua.session.map.rooms[self._roomId].edges[self._edge].dest.id)

    def getTo(self):
        return Lua_Map_Room(self._lua,
                            self._lua.session.map.rooms[self._roomId].edges[self._edge].dest.id)

    def setTo(self, room):
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
