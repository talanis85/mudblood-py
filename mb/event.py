import threading
from collections import deque

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
        self.eventQueue = deque()
        self.condition = threading.Condition()

    def get(self, block=True, timeout=None):
        """
        Pop a single event from the drain. Blocks if no events are
        pending.
        """
        ev = None

        self.condition.acquire()
        try:
            ev = self.eventQueue.pop()
            self.condition.release()
            return ev
        except IndexError:
            if not block:
                self.condition.release()
                return None
            while True:
                self.condition.wait(timeout)
                try:
                    ev = self.eventQueue.pop()
                    self.condition.release()
                    return ev
                except IndexError:
                    if timeout is not None:
                        self.condition.release()
                        return None

    def put(self, event):
        """
        Inject something into the drain.
        """
        self.condition.acquire()

        self.eventQueue.appendleft(event)

        self.condition.notify()
        self.condition.release()

    def push(self, event):
        """
        Push an event (i.e. append on the right side of the queue)
        """
        self.condition.acquire()

        self.eventQueue.append(event)

        self.condition.notify()
        self.condition.release()

# EVENT TYPES

class Event(object):
    def __init__(self):
        # The source of the event
        self.source = None
        # A function that is called after the event was processed
        self.continuation = None

class DisconnectEvent(Event):
    pass

class QuitEvent(Event):
    pass

class LogEvent(Event):
    def __init__(self, msg, level):
        super().__init__()
        self.msg = msg
        self.level = level

# Window Events

class KeyEvent(Event):
    def __init__(self, key):
        super().__init__()
        self.key = key

class ResizeEvent(Event):
    def __init__(self, w, h):
        super().__init__()
        self.w = w
        self.h = h

class ModeEvent(Event):
    def __init__(self, mode, **kwargs):
        super().__init__()
        self.mode = mode
        self.args = kwargs

# Output Chain

class RawEvent(Event):
    def __init__(self, data):
        super().__init__()
        self.data = data

class StringEvent(Event):
    def __init__(self, text):
        super().__init__()
        self.text = text

class EchoEvent(Event):
    def __init__(self, text):
        super().__init__()
        self.text = text


# Input Chain

class InputEvent(Event):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.display = True

class DirectInputEvent(Event):
    def __init__(self, text):
        super().__init__()
        self.text = text

class SendEvent(Event):
    def __init__(self, data):
        super().__init__()
        self.data = data

class CallableEvent(Event):
    def __init__(self, call, *args):
        super().__init__()
        self.call = call
        self.args = args

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

    def push(self, event):
        event.source = self
        if self.drain:
            self.drain.push(event)

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
