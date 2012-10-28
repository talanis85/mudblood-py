from colors import AString
import colors

class InvalidStateException(Exception):
    pass

class FSM(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.current = "start"
        self.debug = []

    def step(self, inp):
        self.debug.append(inp)

        if not hasattr(self, "state_" + self.current):
            raise Exception("Missing state {}".format(self.current))

        self.current = getattr(self, "state_" + self.current)(inp)
        if self.current is None:
            raise InvalidStateException(self.debug)
        elif self.current == "start":
            self.debug = []
            return False
        elif self.current == "end":
            self.current = "start"
            self.debug = []
            return True
        else:
            return True

class Ansi(FSM):
    def __init__(self):
        super().__init__()
        self.reset()

    def parseToAString(self, string):
        ret = AString()
        for c in string:
            try:
                if not self.step(c):
                    ret += AString(c).attribute(self.attr)
            except InvalidStateException as e:
                ret += "<ESC>" + str(e)
                super().reset()
        return ret

    def reset(self):
        super().reset()
        self.attr = (9, 9, 0)

    def state_start(self, c):
        if c == "\x1b":
            return "esc"
        else:
            return "start"

    def state_esc(self, c):
        if c == "[":
            self.args = [0]
            return "csi"

    def state_csi(self, c):
        if c >= "0" and c <= "9":
            self.args[-1] = self.args[-1] * 10 + int(c)
            return "csi"
        elif c == ";":
            self.args.append(0)
            return "csi"
        elif c == "m":
            for d in self.args:
                if d == 0:
                    self.attr = (9, 9, 0)
                elif d == 1:
                    self.attr = (self.attr[0], self.attr[1], self.attr[2] | colors.BOLD)
                elif d == 4:
                    self.attr = (self.attr[0], self.attr[1], self.attr[2] | colors.UNDERLINE)
                elif d >= 30 and d <= 37:
                    self.attr = (d - 30, self.attr[1], self.attr[2])
                elif d >= 40 and d <= 47:
                    self.attr = (self.attr[0], d - 40, self.attr[2])
            return "end"
