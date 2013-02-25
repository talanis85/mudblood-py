import json

#
# EXCEPTIONS
#

class InvalidMapFileException(Exception):
    pass

class UnsettledMapException(Exception):
    def __init__(self):
        super(UnsettledMapException, self).__init__("Unsettled map")

class DuplicateEdgeException(Exception):
    def __init__(self):
        super(DuplicateEdgeException, self).__init__("Duplicate edge")

class InvalidEdgeException(Exception):
    def __init__(self):
        super(InvalidEdgeException, self).__init__("Invalid edge")

#
# DIRECTIONS
#

NORTH = 'n'
NORTHEAST = 'ne'
EAST = 'e'
SOUTHEAST = 'se'
SOUTH = 's'
SOUTHWEST = 'sw'
WEST = 'w'
NORTHWEST = 'nw'

directions = {
        NORTH:      (SOUTH, 0, -1, 0),
        NORTHEAST:  (SOUTHWEST, 1, -1, 0),
        EAST:       (WEST, 1, 0, 0),
        SOUTHEAST:  (NORTHWEST, 1, 1, 0),
        SOUTH:      (SOUTH, 0, 1, 0),
        SOUTHWEST:  (NORTHEAST, -1, 1, 0),
        WEST:       (EAST, -1, 0, 0),
        NORTHWEST:  (SOUTHEAST, -1, -1, 0),
#        'u': ('d', 0, 0, 1),
#        'd': ('u', 0, 0, -1),
        }

def getDirectionDelta(d):
    return (directions[d][1], directions[d][2])

class Room(object):
    """
    A room.
    """
    def __init__(self, id):
        self.id = id
        self.edges = {}
        self.virtualEdges = []
        self.x = 0
        self.y = 0
        self.userdata = {}
        self.refcount = 0

    # Getters and setters

    def getEdges(self):
        return self.edges

    def getVirtualEdges(self):
        return self.virtualEdges

    def getUserdata(self, key):
        return (key in self.userdata and self.userdata[key] or None)

    def setUserdata(self, key, value):
        self.userdata[key] = value

    # Layered view

    def getOverlay(self, layers):
        """
        Returns a view on the edges of this room, filtered by the given
        layer stack.
        """
        ret = {}

        for l in layers:
            for d,e in self.edges.items():
                if d[0] == l:
                    ret[d[1]] = e

            for v in self.virtualEdges:
                for d,e in v.edges.items():
                    if d[0] == l:
                        ret[d[1]] = e

        return ret

    def getLayers(self):
        """
        Return a two-dimensional mapping of layers and their associated
        edges, skipping virtual edges.
        """
        ret = {}

        for d,e in self.edges.items():
            if d[0] not in ret:
                ret[d[0]] = {}

            ret[d[0]][d[1]] = e

        return ret

    def getFlatLayers(self):
        """
        Like getLayers, but return a 3-tuple (layer, direction, edge) for
        every edge.
        """
        ret = []

        for d,e in self.edges.items():
            ret.append((d[0], d[1], e))

        return ret

    # Edge management

    def connect(self, layer, name, dest):
        """
        Create a new edge.
        """
        if (layer, name) in self.edges:
            raise DuplicateEdgeException()

        dest.refcount += 1
        self.edges[(layer, name)] = Edge(dest)

    def disconnect(self, layer, name):
        """
        Remove an edge.
        """
        if (layer, name) not in self.edges:
            raise InvalidEdgeException()

        self.edges[(layer, name)].dest.refcount -= 1
        del self.edges[(layer, name)]

    def connectVirtual(self, dest):
        """
        Create a new virtual edge.
        """
        if dest in self.virtualEdges:
            raise DuplicateEdgeException()

        dest.refcount += 1
        self.virtualEdges.append(dest)

    def disconnectVirtual(self, dest):
        """
        Remove a virtual edge.
        """
        if dest not in self.virtualEdges:
            raise InvalidEdgeException()

        dest.refcount -= 1
        self.virtualEdges.remove(dest)

    # General purpose DFS

class Edge(object):
    """
    An edge.
    """
    def __init__(self, dest):
        self.dest = dest
        self.weight = 1
        self.split = False
        self.userdata = {}

    def follow(self):
        if isinstance(self.dest, int):
            raise UnsettledMapException()

        return self.dest

class Map(object):
    """
    A map.
    """

    @classmethod
    def load(self, f):
        m = json.load(f, cls=MapJSONDecoder)
        m.settle()

        return m

    @classmethod
    def load_old(self, f):
        m = json.load(f, cls=MapJSONDecoderOld)
        m.settle()

        return m

    def __init__(self):
        self.rooms = {0: Room(0)}
        self.dirConfig = {
                'n': NORTH,
                'ne': NORTHEAST,
                'e': EAST,
                'se': SOUTHEAST,
                's': SOUTH,
                'sw': SOUTHWEST,
                'w': WEST,
                'nw': NORTHWEST
                }

        self.currentRoom = 0
        self.weightCache = {}
        self._nextRid = 1
        self._settled = True

    def save(self, f):
        json.dump(self, f, cls=MapJSONEncoder)

    def settle(self):
        if self._settled:
            return

        for r in self.rooms:
            for e in self.rooms[r].edges:
                self.rooms[r].edges[e].dest = self.rooms[self.rooms[r].edges[e].dest]
                self.rooms[r].edges[e].dest.refcount += 1
            for e in range(len(self.rooms[r].virtualEdges)):
                self.rooms[r].virtualEdges[e] = self.rooms[self.rooms[r].virtualEdges[e]]
                self.rooms[r].virtualEdges[e].refcount += 1

        self._settled = True

    # Room management

    def addRoom(self):
        """
        Create a room with a fresh room ID.
        """
        newroom = Room(self._nextRid)
        self.rooms[self._nextRid] = newroom
        self._nextRid += 1

        return newroom

    def findRoom(self, id):
        """
        Get a specific room.

        @param id       Either a numeric ID or a tuple (key, value) where key is
                        a key in the userdata field.
        """
        if isinstance(id, tuple) and len(id) == 2:
            for r in self.rooms.values():
                if id[0] in r.userdata and r.userdata[id[0]] == id[1]:
                    return r

            return None
        elif isinstance(id, int):
            if id in self.rooms:
                return self.rooms[id]
            else:
                return None
        else:
            raise TypeError("Argument must be int or 2-tuple")

    def goto(self, id):
        """
        Set current room to given room ID.
        """
        if id in self.rooms:
            self.currentRoom = id
    
    # Shortest path

    def shortestPath(self, fr, to, layers, weightFunction=None):
        import heapq

        visited = set()
        queue = [(0, fr, ())]

        while queue != []:
            length, roomid, path = heapq.heappop(queue)
            visited.add(roomid)

            if roomid == to:
                return path

            for d,e in self.rooms[roomid].getOverlay(layers).items():
                if e.follow().id not in visited:
                    if weightFunction:
                        if (roomid, d, e) in self.weightCache:
                            weight = self.weightCache[(roomid, d, e)]
                        else:
                            weight = weightFunction(roomid, d, e)
                            self.weightCache[(roomid, d, e)] = weight
                    else:
                        weight = e.weight

                    if weight >= 0:
                        heapq.heappush(queue, (length + e.weight, e.follow().id, path + (d,)))

        return None

    # General purpose DFS

    def dfsVisual(self, room, callback, layers):
        self._dfsVisual(room, 0, 0, callback, set(), layers)

    def _dfsVisual(self, room, x, y, callback, visited, layers):
        visited.add(room.id)
        room.x = x
        room.y = y
        callback(room)
        for d,e in room.getOverlay(layers).items():
            if e.follow().id not in visited and d in self.dirConfig and not e.split:
                self._dfsVisual(e.follow(),
                                x + directions[self.dirConfig[d]][1], y + directions[self.dirConfig[d]][2],
                                callback, visited, layers)

    # Weight cache

    def invalidateWeightCache(self):
        self.weightCache = {}

class MapJSONEncoder(json.JSONEncoder):
    def default(self, ob):
        if isinstance(ob, Map):
            return {'__type__': 'map',
                    'rooms': ob.rooms.values()}
        elif isinstance(ob, Room):
            return {'__type__': 'room',
                    'id': ob.id,
                    'edges': ob.getLayers(),
                    'virtualEdges': ob.getVirtualEdges(),
                    'userdata': ob.userdata,
                   }
        elif isinstance(ob, Edge):
            return {'__type__': 'edge',
                    'dest': ob.dest.id,
                    'weight': ob.weight,
                    'split': ob.split,
                    'userdata': ob.userdata,
                   }

class MapJSONDecoder(json.JSONDecoder):
    def __init__(self, **kwargs):
        super(MapJSONDecoder, self).__init__(object_hook=self.dict_to_object, **kwargs)

    def dict_to_object(self, d):
        if '__type__' not in d:
            return d

        t = d['__type__']

        if t == 'map':
            m = Map()
            m._settled = False
            for room in d['rooms']:
                m.rooms[room.id] = room
                if room.id >= m._nextRid:
                    m._nextRid = room.id + 1
            return m

        elif t == 'room':
            room = Room(d['id'])
            for layer,edges in d['edges'].items():
                for direction,edge in edges.items():
                    room.edges[(layer, direction)] = edge
            for virt in d['virtualEdges']:
                room.virtualEdges.append(virt)
            room.userdata = d['userdata']
            return room

        elif t == 'edge':
            edge = Edge(d['dest'])
            edge.weight = d['weight']
            edge.split = d['split']
            edge.userdata = d['userdata']
            return edge
        
        else:
            return d

class MapJSONDecoderOld(json.JSONDecoder):
    def __init__(self, **kwargs):
        super(MapJSONDecoderOld, self).__init__(object_hook=self.dict_to_object, **kwargs)

    def dict_to_object(self, d):
        if 'rooms' in d:
            m = Map()
            m._settled = False
            for room in d['rooms']:
                m.rooms[room.id] = room
                if room.id >= m._nextRid:
                    m._nextRid = room.id + 1
            return m

        elif 'edges' in d:
            room = Room(d['id'])
            for direction,edge in d['edges'].items():
                room.edges[('base', direction)] = edge
            for virt in d['virtualEdges']:
                room.virtualEdges.append(virt)
            room.userdata = d['userdata']
            return room

        elif 'dest' in d:
            edge = Edge(d['dest'])
            edge.weight = d['weight']
            edge.split = d['split']
            edge.userdata = d['userdata']
            return edge

        else:
            return d

class MapRenderer(object):
    """
    Base class for map renderers.
    """
    def __init__(self, map):
        self.map = map
        self.layers = ['base']

    def render(self):
        pass

class AsciiMapRenderer(MapRenderer):
    directionSymbols = {
            'n': '|',
            'ne': '/',
            'e': '-',
            'se': '\\',
            's': '|',
            'sw': '/',
            'w': '-',
            'nw': '\\'
            }

    def render(self, w, h):
        self.out = bytearray(" "*w*h, "ascii")
        self.visited = set()

        self._renderRoom(self.map.rooms[self.map.currentRoom], int(w/2), int(h/2), w, h)

        x = 1
        y = 1
        for e in self.map.rooms[self.map.currentRoom].getOverlay(self.layers):
            if y >= h:
                break
            for c in str(e):
                self.out[y*w+x] = c
                x += 1
            x = 1
            y += 1

        return self.out

    def _renderRoom(self, r, x, y, w, h):
        if r.id in self.visited:
            return

        self.visited.add(r.id)

        if x >= 0 and x < w and y >= 0 and y < h:
            if r.id == self.map.currentRoom:
                self.out[y*w+x] = ord('X')
            else:
                self.out[y*w+x] = ord('#')

        for d,e in r.getOverlay(self.layers).items():
            if d in self.map.dirConfig:
                d2 = self.map.dirConfig[d]
                newx = x
                newy = y
                if e.split:
                    newx += directions[d2][1]
                    newy += directions[d2][2]
                    if newx >= 0 and newx < w and newy >= 0 and newy < h:
                        self.out[newy*w+newx] = ord(self.directionSymbols[d2])
                else:
                    for i in range(2):
                        newx += directions[d2][1]
                        newy += directions[d2][2]
                        if newx >= 0 and newx < w and newy >= 0 and newy < h:
                            self.out[newy*w+newx] = ord(self.directionSymbols[d2])
                    newx += directions[d2][1]
                    newy += directions[d2][2]

                    self._renderRoom(e.follow(), newx, newy, w, h)

