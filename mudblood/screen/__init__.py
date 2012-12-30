import threading
import Queue

from mudblood import event

class ScreenEvent(object):
    pass

class UpdateScreenEvent(ScreenEvent):
    pass

class SizeScreenEvent(ScreenEvent):
    def __init__(self, w, h):
        self.w, self.h = w, h

class ModeScreenEvent(ScreenEvent):
    def __init__(self, mode, args):
        self.mode, self.args = mode, args

class KeyScreenEvent(ScreenEvent):
    def __init__(self, key):
        self.key = key

class KeystringScreenEvent(ScreenEvent):
    def __init__(self, keystring):
        self.keystring = keystring

class DestroyScreenEvent(ScreenEvent):
    pass

class Screen(event.Source):
    def __init__(self):
        self.thread = threading.Thread(target=self.run)
        self.queue = Queue.Queue()

    def start(self):
        self.thread.start()

    def run(self):
        pass

    def tick(self):
        pass

    def nextEvent(self, timeout=0):
        try:
            return self.queue.get()
        except Queue.Empty:
            return None

    def doneEvent(self):
        self.queue.task_done()

    def join(self):
        self.queue.join()

    def destroy(self):
        self.queue.put(DestroyScreenEvent())

    def updateScreen(self):
        self.queue.put(UpdateScreenEvent())

    def updateSize(self, w, h):
        self.queue.put(SizeScreenEvent(w, h))

    def setMode(self, mode, **kwargs):
        self.queue.put(ModeScreenEvent(mode, kwargs))

    def key(self, key):
        self.queue.put(KeyScreenEvent(key))

    def keystring(self, keystring):
        self.queue.put(KeystringScreenEvent(keystring))
