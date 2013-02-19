import threading

import pygame
import pygame.locals

from mudblood import event
from mudblood import screen
from mudblood import keys
from mudblood import modes
from mudblood import lua
from mudblood import colors
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

colormap = {
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

def createScreen(master):
    return PygameScreen(master)

class Lua_Screen(lua.LuaExposedObject):
    def __init__(self, luaob, screen):
        super(Lua_Screen, self).__init__(luaob)
        self._screen = screen

    def scroll(self, value, name='main'):
        self._screen.moveScroll(name, value)

    def playMusic(self, filename):
        pygame.mixer.Sound(filename).play(-1)

class PygameScreen(modalscreen.ModalScreen):
    def __init__(self, master):
        super(PygameScreen, self).__init__(master)

        self.width = 1000
        self.height = 600

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
        # Init pygame
        pygame.init()

        self.background = (0, 0, 0)

        # Init pygame screen
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption('Mudblood')

        # Init pygame mixer
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)

        self.fontsize = 15
        self.fontname = "Monaco,Lucida Typewriter,Andale Mono"
        self.font = pygame.font.SysFont(self.fontname, self.fontsize)
        self.fontwidth, self.fontheight = self.font.size("a")
        self.antialias = False

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
                    self.modeManager.setMode(ev.mode, **ev.args)
            elif ev.type == pygame.KEYDOWN:
                if ev.key in keymap:
                    k = keymap[ev.key]
                    self.modeManager.key(k)
                elif ev.unicode != "":
                    k = ord(ev.unicode)
                    self.modeManager.key(k)

            self.doUpdate()

    def doUpdate(self):
        self.screen.fill(self.background)

        border = 10

        wh = (self.height - 2*border) / self.fontheight
        ww = (self.width - 2*border) / self.fontwidth

        lines = self.master.session.linebuffers['main'].render(ww, self.getScroll('main'), wh-2) \
              + [self.master.session.getPromptLine()]

        x = border
        y = border
        for l in lines:
            x = border
            for c in l:
                char = self.font.render(c[1], self.antialias, colormap[c[0][0]], (c[0][1] == colors.DEFAULT and self.background or colormap[c[0][1]]))
                self.screen.blit(char, (x, y))
                x += self.fontwidth
            y += self.fontheight

        y -= self.fontheight

        # Prompt line
        if self.modeManager.getMode() == "normal":
            curline = self.font.render(self.normalMode.getBuffer(), self.antialias, colormap[colors.YELLOW], self.background)
            self.screen.blit(curline, (x, y))

            cursor = self.font.render("_", self.antialias, colormap[colors.YELLOW])
            self.screen.blit(cursor, (x + self.normalMode.getCursor()*self.fontwidth, y))
        elif self.modeManager.getMode() == "lua":
            x = border
            y += 2 * self.fontheight

            curline = self.font.render("\\" + self.luaMode.getBuffer(), self.antialias, colormap[colors.RED], self.background)
            self.screen.blit(curline, (x, y))

            cursor = self.font.render("_", self.antialias, colormap[colors.RED])
            self.screen.blit(cursor, (x + (self.luaMode.getCursor()+1)*self.fontwidth, y))

        pygame.display.flip()

