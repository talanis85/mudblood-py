BLACK		= 0x00
RED		    = 0x01
GREEN		= 0x02
YELLOW		= 0x03
BLUE		= 0x04
MAGENTA		= 0x05
CYAN		= 0x06
WHITE		= 0x07
DEFAULT     = 0x09

BOLD		= 0x10
UNDERLINE	= 0x20

class AString(object):
    defaultAttributes = (DEFAULT, DEFAULT, 0)

    def __init__(self, string=""):
        self.string = []

        if isinstance(string, str):
            for c in string:
                self.string.append((self.defaultAttributes, c))
        elif isinstance(string, AString):
            self.string = list(string.string)
        elif isinstance(string, list):
            self.string = list(string)
        else:
            raise TypeError()

    def __getitem__(self, i):
        if isinstance(i, slice):
            return AString(self.string[i.start:i.stop])
        else:
            return self.string[i]

    def __setitem__(self, i, val):
        self.string[i] = val

    def __add__(self, other):
        ret = AString(self)
        ret += other
        return ret
    
    def __radd__(self, other):
        ret = AString(other)
        ret += self
        return ret
    
    def __iadd__(self, other):
        if isinstance(other, AString):
            self.string.extend(other.string)
        elif isinstance(other, tuple):
            self.string.append(other)
        elif isinstance(other, str):
            for c in other:
                self.string.append((self.defaultAttributes, c))
        else:
            raise TypeError()

        return self

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self).__lt__(str(other))

    def __str__(self):
        return "".join([x[1] for x in self.string])
    
    def __repr__(self):
        return self.__str__()

    def attribute(self, att):
        new = []
        for c in self.string:
            new.append((att, c[1]))
        self.string = new
        return self

    def fg(self, fg):
        new = []
        for c in self.string:
            new.append(((fg, c[0][1], c[0][2]), c[1]))
        self.string = new
        return self
    
    def splitLines(self):
        cur = AString()
        for c in self.string:
            if c[1] == "\n":
                yield cur
                cur = AString()
            else:
                cur += c
        yield cur
