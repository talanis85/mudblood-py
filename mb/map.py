import json
import re

# EXCEPTIONS

class InvalidMapFile(Exception):
    pass

directions = {
        'n': ('s', 0, -1, 0),
        'no': ('sw', 1, -1, 0),
        'o': ('w', 1, 0, 0),
        'so': ('nw', 1, 1, 0),
        's': ('n', 0, 1, 0),
        'sw': ('no', -1, 1, 0),
        'w': ('o', -1, 0, 0),
        'nw': ('so', -1, -1, 0),
#        'u': ('d', 0, 0, 1),
#        'd': ('u', 0, 0, -1),
        }

class Room(object):
    def __init__(self, id):
        self.id = id
        self.tag = None
        self.edges = {}
        self.x = 0
        self.y = 0

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

    def updateCoords(self, x, y, visited):
        visited.add(self.id)
        self.x = x
        self.y = y
        for d,e in self.edges.items():
            if e.dest.id not in visited and d in directions:
                e.dest.updateCoords(x + directions[d][1], y + directions[d][2], visited)

class Edge(object):
    def __init__(self, dest):
        self.dest = dest
        self.split = False

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
        for l in f:
            line += 1
            l = l.strip()
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
                        self.rooms[int(m.group(1))].edges[m.group(2)] = e
                    if m.group(4) != "":
                        e = Edge(self.rooms[int(m.group(1))])
                        e.split = (m.group(5) == "1")
                        self.rooms[int(m.group(3))].edges[m.group(4)] = e
            else:
                pass

    def save(self, f):
        j = {"rooms": []}

        for r in self.rooms:
            j['rooms'].append(self.rooms[r].toJsonObj())

        json.dump(j, f)

    def addRoom(self):
        self.rooms[self._nextRid] = Room(self._nextRid)
        self._nextRid += 1

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
            'no': '/',
            'o': '-',
            'so': '\\',
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
            if d in directions:
                newx = x
                newy = y
                if e.split:
                    newx += directions[d][1]
                    newy += directions[d][2]
                    if newx >= 0 and newx < w and newy >= 0 and newy < h:
                        self.out[newy*w+newx] = ord(self.directionSymbols[d])
                else:
                    for i in range(2):
                        newx += directions[d][1]
                        newy += directions[d][2]
                        if newx >= 0 and newx < w and newy >= 0 and newy < h:
                            self.out[newy*w+newx] = ord(self.directionSymbols[d])
                    newx += directions[d][1]
                    newy += directions[d][2]

                    self.renderRoom(e.dest, newx, newy, w, h)

if __name__ == "__main__":
    m = Map()
    with open("testmap.json", "r") as f:
        m.load(f)
    with open("testmap.json.out", "w") as f:
        m.save(f)
