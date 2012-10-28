import json

directions = {
        'n': ('s', 0, -1, 0),
        'ne': ('sw', 1, -1, 0),
        'e': ('w', 1, 0, 0),
        'se': ('nw', 1, 1, 0),
        's': ('n', 0, -1, 0),
        'sw': ('ne', -1, 1, 0),
        'w': ('e', -1, 0, 0),
        'nw': ('se', -1, -1, 0),
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

    def save(self, f):
        j = {"rooms": []}

        for r in self.rooms:
            j['rooms'].append(self.rooms[r].toJsonObj())

        json.dump(j, f)

    def addRoom(self):
        self.rooms[self._nextRid] = Room(self._nextRid)
        self._nextRid += 1


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

        if x >= 0 and x < w and y >= 0 and y < w:
            if r.id == self.map.currentRoom:
                self.out[y*w+x] = ord('X')
            else:
                self.out[y*w+x] = ord('#')

        for d,e in r.edges.items():
            if d in directions:
                newx = x
                newy = y
                for i in range(2):
                    newx += directions[d][1]
                    newy += directions[d][2]
                    if newx >= 0 and newx < w and newy >= 0 and newy < w:
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
