import unittest
import sys
from StringIO import StringIO

from mudblood import map

testmap = """
{"__type__": "map", "rooms": [{"virtualEdges": [], "edges": {"main": {"n": {"dest": 1, "userdata": {}, "__type__": "edge", "split": false, "weight": 1}}}, "__type__": "room", "id": 0, "userdata": {}}, {"virtualEdges": [], "edges": {"main2": {"w": {"dest": 2, "userdata": {}, "__type__": "edge", "split": false, "weight": 1}}, "main": {"s": {"dest": 0, "userdata": {}, "__type__": "edge", "split": false, "weight": 1}}}, "__type__": "room", "id": 1, "userdata": {}}, {"virtualEdges": [], "edges": {}, "__type__": "room", "id": 2, "userdata": {}}]}
"""

class TestMap(unittest.TestCase):
    def setUp(self):
        self.m = map.Map()

    def makeSimpleMap(self):
        r0 = self.m.rooms[0]
        r1 = self.m.addRoom()
        r2 = self.m.addRoom()

        # MAP:  2 <- 1
        #            |
        #            0

        r0.connect('main', 'n', r1)
        r1.connect('main', 's', r0)
        r1.connect('main2', 'w', r2)

    def test_addRoom(self):
        r1 = self.m.addRoom()
        r2 = self.m.addRoom()
        # Check room ids
        self.assertEquals(r1.id, 1)
        self.assertEquals(r2.id, 2)
        # Check initial values
        self.assertEquals(r1.edges, {})
        self.assertEquals(r1.virtualEdges, [])
        self.assertEquals(r1.userdata, {})
        self.assertEquals(r1.refcount, 0)

    def test_connect(self):
        r0 = self.m.rooms[0]
        r1 = self.m.addRoom()
        r2 = self.m.addRoom()

        # Disconnect raises exception
        self.assertRaises(map.InvalidEdgeException, r0.disconnect, 'main', 'testexit')

        # Connect an edge. Connecting again raises exception
        r0.connect('main', 'testexit', r1)
        self.assertRaises(map.DuplicateEdgeException, r0.connect, 'main', 'testexit', r2)

        # Check refcounts
        self.assertEquals(r0.refcount, 0)
        self.assertEquals(r1.refcount, 1)

        # Check new edge
        self.assertIn(('main', 'testexit'), r0.getEdges())
        e = r0.getEdges()[('main', 'testexit')]
        self.assertEquals(e.dest, r1)
        self.assertEquals(e.weight, 1)
        self.assertEquals(e.split, False)
        self.assertEquals(e.userdata, {})

        self.assertEquals(r1.getEdges(), {})

        # Disconnect the new edge again
        r0.disconnect('main', 'testexit')

        self.assertEquals(r0.refcount, 0)
        self.assertEquals(r1.refcount, 0)
        self.assertEquals(r0.getEdges(), {})
        self.assertEquals(r1.getEdges(), {})

    def test_connectVirtual(self):
        r0 = self.m.rooms[0]
        r1 = self.m.addRoom()
        r2 = self.m.addRoom()

        # Disconnect raises exception
        self.assertRaises(map.InvalidEdgeException, r0.disconnectVirtual, r1)

        # Connect an edge. Connecting again raises exception
        r0.connectVirtual(r1)
        self.assertRaises(map.DuplicateEdgeException, r0.connectVirtual, r1)

        # Check refcounts and edge lists
        self.assertEquals(r0.refcount, 0)
        self.assertEquals(r1.refcount, 1)
        self.assertEquals(r0.getVirtualEdges(), [r1])
        self.assertEquals(r1.getVirtualEdges(), [])

        # Disconnect again
        r0.disconnectVirtual(r1)

        self.assertEquals(r0.refcount, 0)
        self.assertEquals(r1.refcount, 0)
        self.assertEquals(r0.getVirtualEdges(), [])
        self.assertEquals(r1.getVirtualEdges(), [])

    def test_findRoom(self):
        self.assertRaises(TypeError, self.m.findRoom, "hallo")

        self.m.addRoom().setUserdata("name", "test")
        self.assertEquals(self.m.findRoom(1), self.m.findRoom(("name", "test")))

    def test_overlay(self):
        r0 = self.m.rooms[0]
        r1 = self.m.addRoom()
        r2 = self.m.addRoom()

        self.assertEquals(r0.getOverlay([]), {})
        self.assertEquals(r0.getOverlay(['main']), {})

        r0.connect('main', 'testexit', r1)

        self.assertEquals(r0.getOverlay([]), {})
        self.assertEquals(r0.getOverlay(['error']), {})

        l = r0.getOverlay(['main', 'main2'])
        self.assertEquals(len(l), 1)
        self.assertIn('testexit', l)
        self.assertEquals(l['testexit'].dest, r1)

        r0.connect('main2', 'testexit', r2)

        l = r0.getOverlay(['main', 'main2'])
        self.assertEquals(len(l), 1)
        self.assertIn('testexit', l)
        self.assertEquals(l['testexit'].dest, r2)

    def test_dfs(self):
        self.makeSimpleMap()
        r0 = self.m.rooms[0]

        class Namespace: pass
        shared = Namespace()

        def cb(r):
            shared.dfscount += 1

        shared.dfscount = 0
        self.m.dfsVisual(r0, cb, ['main'])
        self.assertEquals(shared.dfscount, 2)

        shared.dfscount = 0
        self.m.dfsVisual(r0, cb, ['main', 'main2'])
        self.assertEquals(shared.dfscount, 3)

    def test_asciiRender(self):
        self.makeSimpleMap()

        renderer = map.AsciiMapRenderer(self.m)

        print("Render with layers = ['main']")
        r = renderer.render(10, 10)
        for i in range(len(r)):
            if i % 10 == 0:
                sys.stdout.write("\n")
            sys.stdout.write(chr(r[i]))

        renderer.layers = ['main', 'main2']
        print("Render with layers = ['main', 'main2']")
        r = renderer.render(10, 10)
        for i in range(len(r)):
            if i % 10 == 0:
                sys.stdout.write("\n")
            sys.stdout.write(chr(r[i]))

    def test_shortestPath(self):
        self.makeSimpleMap()
        self.assertEquals(self.m.shortestPath(0, 2, ['main', 'main2']), ('n', 'w'))

    def test_json(self):
        self.makeSimpleMap()

        o = StringIO()
        self.m.save(o)
        print(o.getvalue())

        o = StringIO()
        i = StringIO(testmap)

        jsonmap = map.Map.load(StringIO(testmap))
        jsonmap.save(o)
        print(o.getvalue())

        jsonmap = map.Map.load_old(open("/home/philip/.config/mudblood/mg/map", "r"))
        jsonmap.save(open("newmap", "w"))

suite = unittest.TestSuite([unittest.TestLoader().loadTestsFromTestCase(x) for x in
    [TestMap]
    ])
