import threading
import subprocess
import tempfile
import os

import pygame
import pygame.locals
import pygame.gfxdraw

from mudblood import event
from mudblood import screen
from mudblood import keys
from mudblood import modes
from mudblood import lua
from mudblood import colors
from mudblood import package
from mudblood.screen import modalscreen

keymap = {
        ord('\r'):              ord('\n'),

        pygame.K_F1:            keys.KEY_F1,
        pygame.K_F2:            keys.KEY_F2,
        pygame.K_F3:            keys.KEY_F3,
        pygame.K_F4:            keys.KEY_F4,
        pygame.K_F5:            keys.KEY_F5,
        pygame.K_F6:            keys.KEY_F6,
        pygame.K_F7:            keys.KEY_F7,
        pygame.K_F8:            keys.KEY_F8,
        pygame.K_F9:            keys.KEY_F9,
        pygame.K_F10:           keys.KEY_F10,
        pygame.K_F11:           keys.KEY_F11,
        pygame.K_F12:           keys.KEY_F12,

        pygame.K_KP0:           keys.KEY_NUMPAD0,
        pygame.K_KP1:           keys.KEY_NUMPAD1,
        pygame.K_KP2:           keys.KEY_NUMPAD2,
        pygame.K_KP3:           keys.KEY_NUMPAD3,
        pygame.K_KP4:           keys.KEY_NUMPAD4,
        pygame.K_KP5:           keys.KEY_NUMPAD5,
        pygame.K_KP6:           keys.KEY_NUMPAD6,
        pygame.K_KP7:           keys.KEY_NUMPAD7,
        pygame.K_KP8:           keys.KEY_NUMPAD8,
        pygame.K_KP9:           keys.KEY_NUMPAD9,

        pygame.K_UP:            keys.KEY_ARROW_UP,
        pygame.K_DOWN:          keys.KEY_ARROW_DOWN,
        pygame.K_RIGHT:         keys.KEY_ARROW_RIGHT,
        pygame.K_LEFT:          keys.KEY_ARROW_LEFT,
        pygame.K_INSERT:        keys.KEY_INSERT,
        pygame.K_DELETE:        keys.KEY_DELETE,
        pygame.K_HOME:          keys.KEY_HOME,
        pygame.K_END:           keys.KEY_END,
        pygame.K_PAGEUP:        keys.KEY_PGUP,
        pygame.K_PAGEDOWN:      keys.KEY_PGDN,
}

def createScreen(master):
    return PygameScreen(master)

class Lua_Screen(lua.LuaExposedObject):
    def __init__(self, luaob, screen):
        super(Lua_Screen, self).__init__(luaob)
        self._screen = screen

    def windowVisible(self, name, value=None):
        if value is None:
            return self._screen.windowManager.hasWindow()
        else:
            if value == False and name in self._screen.windows:
                self._screen.windowManager.removeWindow(name)

            if value == True:
                self._screen.windowManager.addWindow(name)

    def windowSize(self, name, value=None):
        if value == None:
            return self._screen.windowManager.getWindow(name).size
        else:
            self._screen.windowManager.getWindow(name).size = value

    def setColumns(self, num):
        self._screen.windowManager.columns = num
    
    def configFgColor(self, colornum, rgb):
        self._screen.colormap_fg[colornum] = (rgb[1], rgb[2], rgb[3])

    def configBgColor(self, colornum, rgb):
        self._screen.colormap_bg[colornum] = (rgb[1], rgb[2], rgb[3])

    def scroll(self, value, name='main'):
        self._screen.moveScroll(name, value)

class WindowManager(object):
    def __init__(self, screen):
        self.screen = screen
        self.layout = []
        self.columns = 1
        self.windows = []
        self.windowObjects = {}

    def addWindow(self, name):
        if name not in self.windows:
            self.windows.append(name)

    def removeWindow(self, name):
        if name in self.windows:
            self.windows.remove(name)

    def hasWindow(self, name):
        return name == 'main' or (name in self.windows)

    def arrange(self, gh):
        gx = 0
        cc = self.columns - 1
        cr = 0

        self.layout = []
        for c in range(self.columns):
            self.layout.append([])

        for w in self.windows + ['main']:
            wh = 0
            if w == 'main':
                if cc > 0:
                    if cr > 0:
                        self.layout[cc][cr-1] = (self.layout[cc][cr-1][0], self.layout[cc][cr-1][1], gh - self.layout[cc][cr-1][1])
                    cc = 0
                    cr = 0
                    gx = 0
                wh = gh - gx
            else:
                wh = self.getWindow(w).size

            if gx + wh > gh and cc > 0:
                if cr > 0:
                    self.layout[cc][cr-1] = (self.layout[cc][cr-1][0], self.layout[cc][cr-1][1], gh - self.layout[cc][cr-1][1])
                cc -= 1
                cr = 0
                gx = 0

            if gx + wh > gh:
                wh = gh - gx

            self.layout[cc].append((w, gx, wh))
            cr += 1
            gx += wh

    def __iter__(self):
        return iter(self.layout)
    
    def getWindow(self, name):
        if name not in self.windowObjects:
            self.windowObjects[name] = Window.create(self.screen, name)

        return self.windowObjects[name]

class Window(object):
    @classmethod
    def create(cls, screen, name):
        if name == 'map':
            return MapWindow(screen, name)
        elif name == 'main':
            return MainWindow(screen, name)
        else:
            return LinebufferWindow(screen, name)

    def __init__(self, screen, name):
        self.screen = screen
        self.name = name
        self.size = 10
        self.refw = 0
        self.refh = 0

    def setSize(self, size):
        self.size = size

class LinebufferWindow(Window):
    def __init__(self, screen, name):
        super(LinebufferWindow, self).__init__(screen, name)

        self.ref = None
        self.fixh = 5
        self.surface = None
        self.scroll = 0

    def draw(self, w, h):
        if self.name not in self.screen.master.session.linebuffers:
            if self.surface is None:
                self.surface = pygame.Surface((w, h))
                self.surface.fill(self.screen.colormap_bg[colors.DEFAULT])
            return self.surface
            
        lb = self.screen.master.session.linebuffers[self.name]

        if lb.head() is not self.ref or self.refw != w or self.refh != h:
            self.surface = None
            self.ref = lb.head()
            self.refw = w
            self.refh = h

        if self.surface is not None:
            return self.surface

        background = self.screen.colormap_bg[colors.DEFAULT]

        surf = pygame.Surface((w, h))
        surf.fill(background)

        y = 0
        x = 0

        gw = w / self.screen.fontwidth
        gh = h / self.screen.fontheight

        lines = None
        fixlines = None

        if self.scroll > 0:
            pygame.gfxdraw.hline(surf, 0, w, h - self.fixh * self.screen.fontheight - self.screen.fontheight / 2,
                                 self.screen.colormap_fg[colors.WHITE])

            lines = lb.render(gw, self.scroll, gh - self.fixh - 1) \
                  + [[]] + lb.render(gw, 0, self.fixh)
        else:
            lines = lb.render(gw, self.scroll, gh)

        if len(lines) < gh:
            y += (gh - len(lines)) * self.screen.fontheight

        for l in lines:
            x = 0
            for ch in l:
                char = self.screen.font.render(ch[1], self.screen.antialias,
                                               self.screen.colormap_fg[ch[0][0]],
                                               (ch[0][1] == colors.DEFAULT and background or self.colormap_bg[ch[0][1]]))
                surf.blit(char, (x, y))
                x += self.screen.fontwidth
            y += self.screen.fontheight

        self.surface = surf

        return self.surface

class MainWindow(LinebufferWindow):
    def __init__(self, screen, name):
        super(MainWindow, self).__init__(screen, name)

        self.promptRef = ""
        self.cursorRef = 0
        self.surface2 = None

    def draw(self, w, h):
        surf = super(MainWindow, self).draw(w, h - self.screen.fontheight)

        line = self.screen.master.session.getPromptLine() + colors.AString(self.screen.normalMode.getBuffer()).fg(colors.YELLOW)

        if self.promptRef != line or self.cursorRef != self.screen.normalMode.getCursor():
            self.surface2 = None
            self.promptRef = line 
            self.cursorRef = self.screen.normalMode.getCursor()

        if self.surface2 is None:
            self.surface2 = pygame.Surface((w, self.screen.fontheight))

            x = 0
            for ch in line:
                char = self.screen.font.render(ch[1], self.screen.antialias,
                                               self.screen.colormap_fg[ch[0][0]],
                                               self.screen.colormap_bg[ch[0][1]])
                self.surface2.blit(char, (x, 0))
                x += self.screen.fontwidth

            cursor = self.screen.font.render("_", self.screen.antialias, self.screen.colormap_fg[colors.YELLOW])
            self.surface2.blit(cursor, ((len(self.screen.master.session.getPromptLine()) + self.screen.normalMode.getCursor())*self.screen.fontwidth, 0))

        combined = pygame.Surface((w, h))
        combined.blit(self.surface, (0, 0))
        combined.blit(self.surface2, (0, h - self.screen.fontheight))

        return combined

class MapWindow(Window):
    def draw(self, w, h):
        return pygame.Surface((w, h))

class PygameScreen(modalscreen.ModalScreen):
    def __init__(self, master):
        super(PygameScreen, self).__init__(master)

        self.width = 1000
        self.height = 600

        self.windowManager = WindowManager(self)

        self.colormap_fg = {
                colors.BLACK:           (0, 0, 0),
                colors.RED:             (255, 100, 100),
                colors.GREEN:           (0, 255, 0),
                colors.YELLOW:          (255, 255, 0),
                colors.BLUE:            (0, 0, 255),
                colors.MAGENTA:         (255, 0, 255),
                colors.CYAN:            (0, 255, 255),
                colors.WHITE:           (255, 255, 255),
                colors.DEFAULT:         (255, 255, 255),
        }

        self.colormap_bg = {
                colors.BLACK:           (0, 0, 0),
                colors.RED:             (255, 100, 100),
                colors.GREEN:           (0, 255, 0),
                colors.YELLOW:          (255, 255, 0),
                colors.BLUE:            (0, 0, 255),
                colors.MAGENTA:         (255, 0, 255),
                colors.CYAN:            (0, 255, 255),
                colors.WHITE:           (255, 255, 255),
                colors.DEFAULT:         (0, 0, 0),
        }

        self.modeManager.addMode("editor", EditorMode(self))

    def tick(self):
        pass

    def destroy(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def updateScreen(self):
        pygame.event.post(pygame.event.Event(pygame.VIDEOEXPOSE))

    def setMode(self, mode, **kwargs):
        pygame.event.post(pygame.event.Event(pygame.USEREVENT, code="mode", mode=mode, args=kwargs))

    def join(self):
        return

    def getLuaScreen(self, lua):
        return Lua_Screen(lua, self)
        
    def run(self):
        self.haveSound = True

        # Init pygame
        pygame.init()

        # Init pygame screen
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption('Mudblood')

        self.fontsize = 15
        self.font = pygame.font.Font(package.getResourceFilename("fonts", "DejaVuSansMono.ttf"), self.fontsize)
        self.fontwidth, self.fontheight = self.font.size("a")
        self.antialias = False

        pygame.key.set_repeat(500, 50)

        while True:
            ev = pygame.event.wait()

            if ev is None:
                continue

            if ev.type == pygame.VIDEOEXPOSE:
                pass
            elif ev.type == pygame.VIDEORESIZE:
                self.width, self.height = ev.w, ev.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            elif ev.type == pygame.QUIT:
                self.put(event.QuitEvent())
                pygame.quit()
                break
            elif ev.type == pygame.USEREVENT:
                if ev.code == "mode":
                    try:
                        self.modeManager.setMode(ev.mode, **ev.args)
                    except modes.UnsupportedModeException:
                        self.put(event.LogEvent("Unsupported mode: {}".format(ev.mode), "err"))
            elif ev.type == pygame.KEYDOWN:
                if ev.key in keymap:
                    k = keymap[ev.key]
                    self.modeManager.key(k)
                elif ev.unicode != "":
                    k = ord(ev.unicode)
                    self.modeManager.key(k)

            self.doUpdate()

    def doUpdate(self):
        background = self.colormap_bg[colors.DEFAULT]
        self.screen.fill(background)

        border = self.fontheight / 2

        status = [x for x in self.master.session.userStatus.splitLines()]

        gw = self.width / self.fontwidth
        gh = self.height / self.fontheight - 2 - len(status)

        gww = gw / self.windowManager.columns
        ww = self.width / self.windowManager.columns

        # Draw column separators
        for i in range(self.windowManager.columns-1):
            pygame.gfxdraw.vline(self.screen, ww * (i+1), 0, gh * self.fontheight, self.colormap_fg[colors.WHITE])

        self.windowManager.arrange(gh)
        layout = self.windowManager.layout

        # Draw windows
        for c in range(len(layout)-1, -1, -1):
            y = border 

            for r in range(len(layout[c])):
                wn, wx, wh = layout[c][r]

                s = self.windowManager.getWindow(wn).draw(gww * self.fontwidth - border*2, wh * self.fontheight - border*2)
                self.screen.blit(s, (c * ww + border, y))
                y += wh * self.fontheight
                
                if r < len(layout[c])-1:
                    pygame.gfxdraw.hline(self.screen, c * ww, (c+1) * ww,
                                         y - self.fontheight / 2, self.colormap_fg[colors.WHITE])

        pygame.gfxdraw.hline(self.screen, 0, self.width,
                             self.height - self.fontheight * (1 + len(status)) - border*2, self.colormap_fg[colors.WHITE])

        if self.modeManager.getMode() == "prompt":
            x = border
            y = self.height - self.fontheight * (1 + len(status)) - border

            curline = self.font.render(self.promptMode.getText() + self.promptMode.getBuffer(), self.antialias, self.colormap_fg[colors.RED], background)
            self.screen.blit(curline, (x, y))

            cursor = self.font.render("_", self.antialias, self.colormap_fg[colors.RED])
            self.screen.blit(cursor, (x + (self.promptMode.getCursor() + len(self.promptMode.getText()))*self.fontwidth, y))

        # Draw status lines
        y = self.height - len(status) * self.fontheight - border
        for l in status:
            x = max([((gw - len(l)) / 2) * self.fontwidth, 0])
            for ch in l:
                char = self.font.render(ch[1], self.antialias,
                                        self.colormap_fg[ch[0][0]],
                                        (ch[0][1] == colors.DEFAULT and background or self.colormap_bg[ch[0][1]]))
                self.screen.blit(char, (x, y))
                x += self.fontwidth
            y += self.fontheight
        pygame.display.flip()

class EditorMode(modes.Mode):
    def __init__(self, screen):
        self.screen = screen

    def onEnter(self, content, callback):
        tname = None
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(content)
            tname = tf.name

        subprocess.call(["/usr/bin/gvim", "--nofork", tname])

        with open(tname, "r") as tf:
            self.screen.put(event.ModeEvent("normal"))
            self.screen.put(event.CallableEvent(callback, tf.read()))

        os.unlink(tname)

