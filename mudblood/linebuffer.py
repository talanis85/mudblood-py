from mudblood.colors import AString

class Linebuffer(object):
    def __init__(self):
        self.lines = []

    def render(self, width, start, length):
        ret = []

        cur = start
        i = 1

        lines = self.lines

        while i < length and cur < len(lines):
            curstr = lines[-(cur+1)]
            if curstr == "":
                ret.append(curstr)
                i += 1
                cur += 1
            else:
                tempret = []
                while unicode(curstr) != "" and i < length:
                    tempret.append(curstr[0:width])
                    curstr = curstr[width:]
                    i += 1
                cur += 1
                tempret.reverse()
                ret.extend(tempret)

        ret.reverse()
        return ret

    def echo(self, astring):
        self.lines.extend(AString(astring).splitLines())

    def head(self):
        return self.lines[-1]
