class Window(object):
    def __init__(self):
        self.ratio = 1
        self.visible = True

class LinebufferWindow(Window):
    def __init__(self, linebuffer):
        super(LinebufferWindow, self).__init__()
        self.type = "linebuffer"
        self.linebuffer = linebuffer
        self.scroll = 0

class MapWindow(Window):
    def __init__(self, map):
        super(MapWindow, self).__init__()
        self.type = "map"
        self.map = map
