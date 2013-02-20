import threading

import pygame
import pygame.locals
import pygame.gfxdraw

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

def createScreen(master):
    return PygameScreen(master)

class Lua_Screen(lua.LuaExposedObject):
    def __init__(self, luaob, screen):
        super(Lua_Screen, self).__init__(luaob)
        self._screen = screen

    def windowVisible(self, name, value=None):
        if value is None:
            if name == 'main':
                return True
            return (name in self._screen.windows)
        else:
            if name == 'main':
                return

            if value == False and name in self._screen.windows:
                self._screen.windows.remove(name)

            if value == True:
                if name not in self._screen.windows:
                    self._screen.windows.append(name)
                if name not in self._screen.window_sizes:
                    self._screen.window_sizes[name] = 10

    def windowSize(self, name, value=None):
        if value == None:
            if name in self._screen.window_sizes:
                return self._screen.window_sizes[name]
            else:
                return None
        else:
            self._screen.window_sizes[name] = value

    def setColumns(self, num):
        self._screen.columns = num
    
    def configFgColor(self, colornum, rgb):
        self._screen.colormap_fg[colornum] = (rgb[1], rgb[2], rgb[3])

    def configBgColor(self, colornum, rgb):
        self._screen.colormap_bg[colornum] = (rgb[1], rgb[2], rgb[3])

    def scroll(self, value, name='main'):
        self._screen.moveScroll(name, value)

    def playMusic(self, filename):
        if self._screen.haveSound:
            pygame.mixer.Sound(filename).play(-1)

class PygameScreen(modalscreen.ModalScreen):
    def __init__(self, master):
        super(PygameScreen, self).__init__(master)

        self.width = 1000
        self.height = 600

        self.windows = []
        self.window_sizes = {}
        self.columns = 1

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
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=4096)
        except:
            haveSound = False
        pygame.init()

        # Init pygame screen
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption('Mudblood')

        self.fontsize = 15
        self.fontname = "Monaco,Lucida Typewriter,Andale Mono"
        self.font = pygame.font.SysFont(self.fontname, self.fontsize)
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
                    self.modeManager.setMode(ev.mode, **ev.args)
            elif ev.type == pygame.KEYDOWN:
                if ev.key in keymap:
                    k = keymap[ev.key]
                    self.modeManager.key(k)
                elif ev.unicode != "":
                    k = ord(ev.unicode)
                    self.modeManager.key(k)

            self.doUpdate()

    def drawWindow(self, wn, w, h, fixh=5):
        surf = pygame.Surface((w, h))
        surf.fill(self.colormap_bg[colors.DEFAULT])

        background = self.colormap_bg[colors.DEFAULT]

        y = 0
        x = 0

        gw = w / self.fontwidth
        gh = h / self.fontheight

        if wn == 'map':
            # TODO
            pass
        else:
            if wn in self.master.session.linebuffers:
                lines = None
                fixlines = None
                scroll = self.getScroll(wn)
                lb = self.master.session.linebuffers[wn]

                if scroll > 0:
                    pygame.gfxdraw.hline(surf, 0, w, h - fixh * self.fontheight - self.fontheight / 2,
                                         self.colormap_fg[colors.WHITE])

                    if wn == 'main':
                        lines = lb.render(gw, scroll, gh - fixh - 1) \
                              + [[]] + lb.render(gw, 0, fixh - 1) + [self.master.session.getPromptLine()]
                    else:
                        lines = lb.render(gw, scroll, gh - fixh - 1) \
                              + [[]] + lb.render(gw, 0, fixh)
                else:
                    if wn == 'main':
                        lines = lb.render(gw, scroll, gh - 1) \
                              + [self.master.session.getPromptLine()]
                    else:
                        lines = lb.render(gw, scroll, gh)

                if len(lines) < gh:
                    y += (gh - len(lines)) * self.fontheight

                for l in lines:
                    x = 0
                    for ch in l:
                        char = self.font.render(ch[1], self.antialias,
                                                self.colormap_fg[ch[0][0]],
                                                (ch[0][1] == colors.DEFAULT and background or self.colormap_bg[ch[0][1]]))
                        surf.blit(char, (x, y))
                        x += self.fontwidth
                    y += self.fontheight

                if wn == 'main':
                    y -= self.fontheight

                    curline = self.font.render(self.normalMode.getBuffer(), self.antialias,
                                               self.colormap_fg[colors.YELLOW], background)
                    surf.blit(curline, (x, y))

                    cursor = self.font.render("_", self.antialias, self.colormap_fg[colors.YELLOW])
                    surf.blit(cursor, (x + self.normalMode.getCursor()*self.fontwidth, y))

        return surf

    def doUpdate(self):
        background = self.colormap_bg[colors.DEFAULT]
        self.screen.fill(background)

        border = 10

        gw = self.width / self.fontwidth
        gh = self.height / self.fontheight - 3

        gww = gw / self.columns
        ww = self.width / self.columns

        # Arrange windows
        gx = 0
        cc = self.columns - 1
        cr = 0

        layout = []
        for c in range(self.columns):
            layout.append([])

        for w in self.windows + ['main']:
            if w == 'main':
                if cc > 0:
                    if cr > 0:
                        layout[cc][cr-1] = (layout[cc][cr-1][0], layout[cc][cr-1][1], gh - layout[cc][cr-1][1])
                    cc = 0
                    cr = 0
                    gx = 0
                wh = gh - gx
            else:
                wh = self.window_sizes[w]

            if gx + wh > gh and cc > 0:
                if cr > 0:
                    layout[cc][cr-1] = (layout[cc][cr-1][0], layout[cc][cr-1][1], gh - layout[cc][cr-1][1])
                cc -= 1
                cr = 0
                gx = 0

            if gx + wh > gh:
                wh = gh - gx

            layout[cc].append((w, gx, wh))
            cr += 1
            gx += wh

        # Draw column separators
        for i in range(self.columns-1):
            pygame.gfxdraw.vline(self.screen, ww * (i+1), 0, gh * self.fontheight, self.colormap_fg[colors.WHITE])

        # Draw windows
        for c in range(len(layout)-1, -1, -1):
            y = border 

            for r in range(len(layout[c])):
                wn, wx, wh = layout[c][r]

                s = self.drawWindow(wn, gww * self.fontwidth - border*2, wh * self.fontheight - border*2)
                self.screen.blit(s, (c * ww + border, y))
                y += wh * self.fontheight
                
                if r < len(layout[c])-1:
                    pygame.gfxdraw.hline(self.screen, c * ww, (c+1) * ww,
                                         y - self.fontheight / 2, self.colormap_fg[colors.WHITE])

        pygame.gfxdraw.hline(self.screen, 0, self.width,
                             self.height - self.fontheight * 2 - border*2, self.colormap_fg[colors.WHITE])

        if self.modeManager.getMode() == "prompt":
            x = border
            y = self.height - self.fontheight * 2 - border

            curline = self.font.render(self.promptMode.getText() + self.promptMode.getBuffer(), self.antialias, self.colormap_fg[colors.RED], background)
            self.screen.blit(curline, (x, y))

            cursor = self.font.render("_", self.antialias, self.colormap_fg[colors.RED])
            self.screen.blit(cursor, (x + (self.promptMode.getCursor() + len(self.promptMode.getText()))*self.fontwidth, y))

        status = self.font.render(self.master.session.userStatus, self.antialias, self.colormap_fg[colors.DEFAULT], background)
        self.screen.blit(status, ((self.width - status.get_width()) / 2, self.height - self.fontheight - border))
        pygame.display.flip()

