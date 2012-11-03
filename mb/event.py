import threading
import queue

import sys
import termios

import socket
import telnetlib

# MANAGER

class Drain(object):
    """
    A Drain aggregates data from multiple sources.
    """
    def __init__(self):
        self.eventQueue = queue.Queue()

    def get(self, timeout=0):
        """
        Pop a single event from the drain. Blocks if no events are
        pending.
        """
        try:
            return self.eventQueue.get(True, timeout)
        except queue.Empty as e:
            return None

    def put(self, event):
        """
        Inject something into the drain.
        """
        self.eventQueue.put(event)

# EVENT TYPES

class Event(object):
    def __init__(self):
        self.source = None

class DisconnectEvent(Event):
    pass

class LogEvent(Event):
    def __init__(self, msg, level):
        super().__init__()
        self.msg = msg
        self.level = level

class RawEvent(Event):
    def __init__(self, data):
        super().__init__()
        self.data = data

class KeyEvent(Event):
    def __init__(self, key):
        super().__init__()
        self.key = key

class ResizeEvent(Event):
    def __init__(self, w, h):
        super().__init__()
        self.w = w
        self.h = h

class InputEvent(Event):
    def __init__(self, text, display=True):
        super().__init__()
        self.text = text
        self.display = display

class ModeEvent(Event):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode

class FunctionEvent(Event):
    def __init__(self, func):
        super().__init__()
        self.func = func

class QuitEvent(Event):
    pass

# SOURCE TYPES

class Source(object):
    def __init__(self):
        self.drain = None

    def bind(self, drain):
        if self.drain:
            raise Exception("Source is already bound.")

        self.drain = drain

    def put(self, event):
        """
        Inject an event into the source.
        """
        event.source = self
        if self.drain:
            self.drain.put(event)

class AsyncSource(Source):
    def __init__(self):
        super().__init__()
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True

    def start(self):
        self.running = True
        self.thread.start()

    def run(self):
        while self.running:
            ev = self.poll()
            if ev:
                self.put(ev)

    def poll(self):
        pass

class FileSource(AsyncSource):
    def __init__(self, file, chunksize):
        self.file = file
        self.chunksize = chunksize
        super().__init__()
        self.start()

    def poll(self):
        return RawEvent(self.file.read(self.chunksize))

class SocketSource(AsyncSource):
    def __init__(self, socket):
        super().__init__()
        self.socket = socket

    def poll(self):
        try:
            return RawEvent(self.socket.recv(1024))
        except:
            # TODO: Specify, which exception(s) should be caught
            self.running = False
            return DisconnectEvent()

class GtkInputSource(Source):
    pass

# UNIT TEST

if __name__ == "__main__":
    drain = Drain()

    ttysource = FileSource(sys.stdin, 1)
    drain.addSource(ttysource)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", 4711))
    socksource = SocketSource(sock)
    drain.addSource(socksource)

    gtksource = GtkInputSource()
    drain.addSource(gtksource)

    gtksource.put(RawEvent("hallo"))

    print("Type something:")

    for i in range(3):
        src, ev = drain.get()
        print("Got: {} ({}) from {}".format(ev.data, ev.__class__, src.__class__))
