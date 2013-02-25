import unittest
import collections
import time

from mudblood.telnet import *
from mudblood import event

class DummyFile(object):
    def __init__(self):
        self.buffer = b''
    def read(self, size):
        ret = self.buffer[:size]
        self.buffer = self.buffer[size:]
        return ret
    def write(self, string):
        self.buffer = self.buffer + bytes(string)

class TestTelnegs(unittest.TestCase):
    def assertEventsEqual(self, ev1, ev2):
        self.assertIsInstance(ev1, ev2.__class__)
        self.assertDictEqual(ev1.__dict__, ev2.__dict__)

    def assertDrainContents(self, events):
        i = 0
        for e in events:
            e2 = self.drain.get(False)
            e.source = e2.source
            if not (isinstance(e2, e.__class__)):
                self.fail("Event {}: Classes dont match. {} expected, but found {}".format(i, e, e2))
            if not e2.__dict__ == e.__dict__:
                self.fail("Event {}: Contents dont match. {} expected, but found {}.\nexpected:{}\nfound:{}".format(i, e, e2, e.__dict__, e2.__dict__))
            i += 1

    def setUp(self):
        self.file = DummyFile()
        self.telnet = Telnet(self.file)
        self.drain = event.Drain()
        self.telnet.bind(self.drain)

    def test_1arg(self):
        self.file.write(bytearray([IAC, EOR]))
        self.telnet.poll()
        self.assertDrainContents([TelnetEvent(EOR, None, None)])

    def test_2arg(self):
        self.file.write(bytearray([IAC, DO, OPT_EOR]))
        self.telnet.poll()
        self.assertDrainContents([TelnetEvent(DO, OPT_EOR, None)])

    def test_3arg(self):
        self.file.write(bytearray([IAC, SB, 1, 2, 3, IAC, SE]))
        self.telnet.poll()
        self.assertDrainContents([TelnetEvent(SB, 1, bytearray([2,3]))])

    def tearDown(self):
        pass

class TestReal(unittest.TestCase):
    def setUp(self):
        self.drain = event.Drain()

    def test_connect(self):
        self.sock = TCPSocket()
        self.telnet = Telnet(self.sock)
        self.telnet.bind(self.drain)
        self.sock.connect("openfish", 9999)
        self.telnet.start()
        time.sleep(1)
        print("First events:")
        while True:
            e = self.drain.get(False)
            if e is None:
                break
            print(e)

suite = unittest.TestSuite([unittest.TestLoader().loadTestsFromTestCase(x) for x in
    [TestTelnegs, TestReal]
    ])
