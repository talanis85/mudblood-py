import os

class LockedException(Exception):
    pass

class Lock(object):
    def __init__(self, filename):
        self.filename = filename
        self.lockfile = filename + ".lock"
        self.locked = False

        if os.path.exists(self.lockfile):
            raise LockedException()

        with open(self.lockfile, "w") as f:
            f.write("locked")

        self.locked = True

    def release(self):
        if self.locked:
            os.remove(self.lockfile)

