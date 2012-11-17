import json
import re

# EXCEPTIONS

class InvalidMapFile(Exception):
    pass

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

class Room(object):
    def __init__(self, id):
        self.id = id
        self.tag = None
        self.edges = {}
        self.virtualEdges = []
        self.x = 0
        self.y = 0
        self.userdata = {}

    @classmethod
    def fromJsonObj(cls, ob):
        r = cls(ob['id'])
        r.tag = ob.get('tag', None)
        r.edges = {}
        for e in ob.get('edges', []):
            r.edges[e] = Edge.fromJsonObj(ob['edges'][e])
        return r

    def toJsonObj(self):
        ob = {}
        ob['id'] = self.id
        ob['tag'] = self.tag

        ob['edges'] = {}
        for e in self.edges:
            ob['edges'][e] = self.edges[e].toJsonObj()

        return ob
    
    def getEdges(self):
        ret = dict(self.edges)
        for v in self.virtualEdges:
            for d,e in v.edges.items():
                ret[d] = e
        return ret

    def updateCoords(self, map, x, y, visited):
        visited.add(self.id)
        self.x = x
        self.y = y
        for d,e in self.edges.items():
            if e.dest.id not in visited and d in directions:
                e.dest.updateCoords(x + directions[d][1], y + directions[d][2], visited)

class Edge(object):
    def __init__(self, dest):
        self.dest = dest
        self.weight = 1
        self.split = False
        self.userdata = {}

    @classmethod
    def fromJsonObj(cls, ob):
        e = cls(ob['dest'])
        return e
    
    def toJsonObj(self):
        ob = {}
        ob['dest'] = self.dest.id

        return ob

    def follow(self):
        if isinstance(self.dest, int):
            raise Exception("Unfixated Edge cannot be followed")

        return self.dest

class Map(object):
    def __init__(self):
        self.rooms = {0: Room(0)}
        self.tags = {}
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

        self._nextRid = 1

    def load(self, f):
        j = json.load(f)

        self.rooms = {}
        self.tage = {}
        self._nextRid = 0
        self.currentRoom = 0

        # 1st pass
        for r in j['rooms']:
            newRoom = Room.fromJsonObj(r)
            self.rooms[newRoom.id] = newRoom
            if newRoom.tag:
                self.tags[newRoom.tag] = newRoom
            if self._nextRid <= newRoom.id:
                self._nextRid = newRoom.id + 1

        # 2nd pass
        for r in self.rooms:
            for e in self.rooms[r].edges:
                self.rooms[r].edges[e].dest = self.rooms[self.rooms[r].edges[e].dest]

    def load_old(self, f):
        state = 0
        line = 0
        r = None
        for l in f:
            line += 1
            l = l.rstrip()
            if state == 0:
                if l == "mudblood v1.0":
                    state = 1
                else:
                    raise InvalidMapFile("Expected 'mudblood v1.0' in line {}".format(line))
            elif state == 1:
                nrooms = int(l)
                for i in range(nrooms):
                    self.rooms[i] = Room(i)
                state = 2
            elif state == 2:
                if l == "":
                    state = 3
                else:
                    m = re.match(r"^(\d+) (.+)$", l)
                    if m is None:
                        raise InvalidMapFile("Expected Room tag in line {}".format(line))
                    self.rooms[int(m.group(1))].tag = m.group(2)
            elif state == 3:
                if l == "":
                    state = 4
                else:
                    m = re.match(r"^(\d+)\|([^\|]*)\|(\d+)\|([^\|]*)\|(\d)(\d)(\d)$", l)
                    if m is None:
                        raise InvalidMapFile("Expected edge in line {}".format(line))
                    if m.group(2) != "":
                        e = Edge(self.rooms[int(m.group(3))])
                        e.split = (m.group(5) == "1")
                        e.weight = (m.group(6) == "1" and -1 or 1)
                        e.userdata['level'] = int(m.group(7))
                        self.rooms[int(m.group(1))].edges[m.group(2)] = e
                    if m.group(4) != "":
                        e = Edge(self.rooms[int(m.group(1))])
                        e.split = (m.group(5) == "1")
                        e.weight = (m.group(6) == "1" and -1 or 1)
                        e.userdata['level'] = int(m.group(7))
                        self.rooms[int(m.group(3))].edges[m.group(4)] = e
            elif state == 4:
                if l == "":
                    state = 5
                else:
                    m = re.match(r"^(\d+) (\d+) (\d)$", l)
                    if m is None:
                        raise InvalidMapFile("Expected virtual edge in line {}".format(line))
                    self.rooms[int(m.group(1))].virtualEdges.append(self.rooms[int(m.group(2))])
            elif state == 5:
                r = self.rooms[int(l)]
                r.userdata['script'] = ""
                state = 6
            elif state == 6:
                if l == "###":
                    state = 5
                else:
                    r.userdata['script'] += l + "\n"


    def save(self, f):
        j = {"rooms": []}

        for r in self.rooms:
            j['rooms'].append(self.rooms[r].toJsonObj())

        json.dump(j, f)

    def addRoom(self):
        self.rooms[self._nextRid] = Room(self._nextRid)
        self._nextRid += 1

    def findRoom(self, id):
        if isinstance(id, str):
            for r in self.rooms.values():
                if r.tag == id:
                    id = r.id
        if isinstance(id, int):
            return id
        else:
            raise KeyError("Room {} not found".format(id))

    def shortestPath(self, fr, to, weightFunction=None):
        import heapq

        visited = set()
        queue = [(0, fr, ())]

        while queue != []:
            length, roomid, path = heapq.heappop(queue)
            visited.add(roomid)

            if roomid == to:
                return path

            for d,e in self.rooms[roomid].getEdges().items():
                if e.dest.id not in visited:
                    if weightFunction:
                        weight = weightFunction(roomid, d)
                    else:
                        weight = e.weight

                    if weight >= 0:
                        heapq.heappush(queue, (length + e.weight, e.dest.id, path + (d,)))

        return None

    def goto(self, id):
        self.currentRoom = id

class MapRenderer(object):
    def __init__(self, map):
        self.map = map

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

        self.renderRoom(self.map.rooms[self.map.currentRoom], int(w/2), int(h/2), w, h)

        return self.out

    def renderRoom(self, r, x, y, w, h):
        if r.id in self.visited:
            return

        self.visited.add(r.id)

        if x >= 0 and x < w and y >= 0 and y < h:
            if r.id == self.map.currentRoom:
                self.out[y*w+x] = ord('X')
            else:
                self.out[y*w+x] = ord('#')

        for d,e in r.edges.items():
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

                    self.renderRoom(e.dest, newx, newy, w, h)

if __name__ == "__main__":
    m = Map()
    with open("testmap.json", "r") as f:
        m.load(f)
    with open("testmap.json.out", "w") as f:
        m.save(f)
