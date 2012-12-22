from mudblood import keys

class ModeManager(object):
    def __init__(self, initMode, modes):
        self._modes = modes
        self._currentMode = initMode

    def setMode(self, modename, **kwargs):
        self._modes[self._currentMode].onExit()
        self._currentMode = modename
        self._modes[self._currentMode].onEnter(**kwargs)

    def getMode(self):
        return self._currentMode

    def key(self, key):
        self._modes[self._currentMode].onKey(key)

class Mode(object):
    def onEnter(self):
        pass

    def onExit(self):
        pass

    def onKey(self, key):
        pass

class BufferMode(Mode):
    def __init__(self):
        self._buffer = ""
        self._saved_buffer = ""
        self._cursor = 0
        self._history = []
        self._curHistory = 0

    def onKey(self, key):
        if key == keys.KEY_BACKSPACE or key == keys.KEY_BACKSPACE2:
            if self._cursor > 0:
                self._cursor -= 1
                self._buffer = self._buffer[:self._cursor] + self._buffer[self._cursor+1:]
        elif key == keys.KEY_ARROW_LEFT:
            if self._cursor > 0:
                self._cursor -= 1
        elif key == keys.KEY_ARROW_RIGHT:
            if self._cursor < len(self._buffer):
                self._cursor += 1
        elif key == keys.KEY_ARROW_UP:
            self.history(-1)
        elif key == keys.KEY_ARROW_DOWN:
            self.history(1)
        elif key <= 127:
            self._buffer = self._buffer[:self._cursor] + chr(key) + self._buffer[self._cursor:]
            self._cursor += 1

    def addHistory(self):
        if self._buffer == "":
            return

        self._history.append(self._buffer)
        self._curHistory = 0

    def history(self, move):
        if len(self._history) == 0:
            return

        if self._curHistory == 0 and move <= 0:
            self._saved_buffer = self._buffer

        self._curHistory += move

        if self._curHistory > 0:
            self._curHistory = 0

        if self._curHistory == 0:
            self._buffer = self._saved_buffer
            self._cursor = 0
        else:
            if self._curHistory < -len(self._history):
                self._curHistory = -len(self._history)
            self._buffer = self._history[self._curHistory]
            self._cursor = 0

    def clearBuffer(self):
        self._buffer = ""
        self._cursor = 0

    def getBuffer(self):
        return self._buffer

    def getCursor(self):
        return self._cursor
