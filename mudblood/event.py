# ----------------------------------------------------------------------------
#
# -- mudblood - a flexible mud client --
#
# event.py
#
# This module implements a thread-safe multiple-producer-single-consumer
# pattern. The Drain class is the consumer - it can consume Event objects
# from a number of Source objects that are bound to that Drain.
#
# ----------------------------------------------------------------------------

import threading
from collections import deque

import sys

import socket

class Drain(object):
    """
    This is the consumer object. Sources can bind themselves to a Drain
    which can consume the events from the sources.
    """
    def __init__(self):
        self.eventQueue = deque()
        self.condition = threading.Condition()

    def get(self, block=True, timeout=None):
        """
        Consume a single event from the end of the queue.
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
        Called by sources to append something to the front of the queue.
        """
        self.condition.acquire()

        self.eventQueue.appendleft(event)

        self.condition.notify()
        self.condition.release()

    def push(self, event):
        """
        Called by sources to append something to the end of the queue.
        I.e.: The pushed event will be the next consumed event.
        """
        self.condition.acquire()

        self.eventQueue.append(event)

        self.condition.notify()
        self.condition.release()

# ----------------------------------------------------------------------------
#   EVENT TYPES
# 
# Instances of these classes are meant to be emitted by sources.
# ----------------------------------------------------------------------------

class Event(object):
    """
    Base class for all events.
    """
    def __init__(self):
        # The source of the event
        self.source = None
        # A function that is called after the event was processed
        self.continuation = None

class DisconnectEvent(Event):
    """
    Signals that a session has closed its connection.
    Emitted by: Session
    """
    pass

class QuitEvent(Event):
    """
    Requests mudblood to quit.
    Emitted by: Session
    """
    pass

class LogEvent(Event):
    """
    Adds a message to the log console.
    Emitted by: *
    """
    def __init__(self, msg, level):
        super().__init__()
        self.msg = msg
        self.level = level

class KeyEvent(Event):
    """
    Signals that a key has been pressed.
    Emitted by: Screen
    """
    def __init__(self, key):
        super().__init__()
        self.key = key

class ResizeEvent(Event):
    """
    Signals that the screen size has changed.
    Emitted by: Screen
    """
    def __init__(self, w, h):
        super().__init__()
        self.w = w
        self.h = h

class ModeEvent(Event):
    """
    Requests to change screen mode.
    Emitted by: Session
    """
    def __init__(self, mode, **kwargs):
        super().__init__()
        self.mode = mode
        self.args = kwargs

class RawEvent(Event):
    """
    Incoming data from a telnet socket, already stripped of Telnegs.
    Emitted by: Telnet
    """
    def __init__(self, data):
        super().__init__()
        self.data = data

class StringEvent(Event):
    """
    Decoded data from a telnet socket.
    Emitted by: Session
    """
    def __init__(self, text):
        super().__init__()
        self.text = text

class EchoEvent(Event):
    """
    Requests a session to add text to its linebuffer.
    Emitted by: Session
    """
    def __init__(self, text):
        super().__init__()
        self.text = text


class InputEvent(Event):
    """
    A line of input was made or the lua function send() was called.
    Emitted by: Session, Screen
    """
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.display = True

class DirectInputEvent(Event):
    """
    A single line of data should be sent to the socket.
    Emitted by: Session
    """
    def __init__(self, text):
        super().__init__()
        self.text = text

class SendEvent(Event):
    """
    Somewhat redundant. Encode a single line and send it to the socket.
    Emitted by: Session
    """
    def __init__(self, data):
        super().__init__()
        self.data = data

class CallableEvent(Event):
    """
    A callable should be called with the given arguments.
    Emitted by: *
    """
    def __init__(self, call, *args):
        super().__init__()
        self.call = call
        self.args = args

# ----------------------------------------------------------------------------
#   SOURCE TYPES
# 
# These are the producer classes. Every Source must be bound to a single
# drain. However, a source can act as a drain by itself so sources can be
# stacked.
# ----------------------------------------------------------------------------

class Source(object):
    """
    Base class for all sources.
    """
    def __init__(self):
        self.drain = None

    def bind(self, drain):
        """
        Bind this source to a drain. Raise an error if this source is already
        bound.
        """
        if self.drain:
            raise Exception("Source is already bound.")

        self.drain = drain

    def put(self, event):
        """
        Append to the end of the drain.
        """
        if not event.source:
            event.source = self
        if self.drain:
            self.drain.put(event)

    def push(self, event):
        """
        Append to the front of the drain.
        """
        if not event.source:
            event.source = self
        if self.drain:
            self.drain.push(event)

class AsyncSource(Source):
    """
    Base class for asynchronous sources, i.e. sources that run in their own
    thread.
    """
    def __init__(self):
        super().__init__()
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True

    def start(self):
        """
        Start the source's thread routine.
        """
        self.running = True
        self.thread.start()

    def stop(self):
        """
        Stop the source's thread routine.
        """
        self.running = False
        self.thread.join()

    def run(self):
        while self.running:
            ev = self.poll()
            if ev:
                self.put(ev)

    def poll(self):
        """
        To be defined by concrete subclasses. Called periodically in the thread
        routine. Should return the next event object (may block before that).
        """
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
