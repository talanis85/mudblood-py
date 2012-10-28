from colors import AString

class Linebuffer(object):
    def __init__(self):
        self.lines = []
        self.newLines = [AString()]

    def render(self, width, start, length):
        ret = []

        cur = start
        i = 0

        lines = self.lines + self.newLines

        while i < length and cur < len(lines):
            curstr = lines[-(cur+1)]
            if curstr == "":
                ret.append(curstr)
                i += 1
                cur += 1
            else:
                tempret = []
                while curstr != "" and i < length:
                    tempret.append(curstr[0:width])
                    curstr = curstr[width:]
                    i += 1
                cur += 1
                tempret.reverse()
                ret.extend(tempret)

        ret.reverse()
        return ret

    def append(self, astring):
        i = 0
        for l in AString(astring).splitLines():
            if i > 0:
                self.newLines.append(AString())
            self.newLines[-1] += l
            i += 1

    def echo(self, astring):
        self.lines.extend(AString(astring).splitLines())

    def echoInto(self, astring):
        self.lines.append(self.newLines[-1] + astring)
        self.newLines = self.newLines[:-1] + [AString()]

    def update(self, callback=None):
        for l in self.newLines[:-1]:
            index = len(self.lines)
            if callback:
                ret = callback(l)
                if ret != None:
                    l = ret
            self.lines.insert(index, l)
        self.newLines = [self.newLines[-1]]
