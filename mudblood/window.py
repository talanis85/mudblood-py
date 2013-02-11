class Window(object):
    def __init__(self):
        self.ratio = 1
        self.visible = True

    def echo(self, string):
        pass

class LinebufferWindow(Window):
    def __init__(self, linebuffer):
        super(LinebufferWindow, self).__init__()
        self.type = "linebuffer"
        self.linebuffer = linebuffer
        self.scroll = 0

    def echo(self, string):
        self.linebuffer.echo(string)

class MapWindow(Window):
    def __init__(self, map):
        super(MapWindow, self).__init__()
        self.type = "map"
        self.map = map
