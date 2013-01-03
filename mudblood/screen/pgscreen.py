import threading

import pygame
import pygame.locals

from mudblood import event
from mudblood import screen
from mudblood import keys
from mudblood import modes
from mudblood.screen import modalscreen

def createScreen(master):
    return PygameScreen(master)

class PygameSource(event.AsyncSource):
    def __init__(self):
        super(PygameSource, self).__init__()

    def poll(self):
        try:
            ev = pygame.event.wait()
        except:
            return None

        if ev.type == pygame.locals.QUIT:
            return event.QuitEvent()
        elif ev.type == pygame.locals.KEYDOWN:
            if ev.key <= 127:
                k = ord(ev.unicode)
                if k == ord("\r"):
                    k = ord("\n")
                return event.KeyEvent(k)
        elif ev.type == pygame.locals.VIDEORESIZE:
            return event.ResizeEvent(ev.w, ev.h)
        elif ev.type == pygame.locals.VIDEOEXPOSE:
            return None

class PygameScreen(modalscreen.ModalScreen):
    def __init__(self, master):
        super(PygameScreen, self).__init__(master)

        self.width = 1000
        self.height = 600

        pygame.init()

        self.background = (0, 0, 0)

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Mudblood')

        self.fontsize = 15
        self.fontname = "Mono"
        self.font = pygame.font.SysFont(self.fontname, self.fontsize)
        self.fontwidth, self.fontheight = self.font.size("a")
        self.antialias = False

        # Create a source for user input
        self.source = PygameSource()
        self.source.start()
        self.source.bind(self.master.drain)

    def tick(self):
        pass
        
    def run(self):
        while True:
            ev = self.nextEvent()

            if ev is None:
                continue

            if isinstance(ev, screen.UpdateScreenEvent):
                self.doUpdate()
            elif isinstance(ev, screen.SizeScreenEvent):
                self.width, self.height = ev.w, ev.h
            elif isinstance(ev, screen.DestroyScreenEvent):
                pygame.quit()
                self.doneEvent()
                break
            elif isinstance(ev, screen.ModeScreenEvent):
                self.modeManager.setMode(ev.mode, **ev.args)
            elif isinstance(ev, screen.KeyScreenEvent):
                self.modeManager.key(ev.key)

            self.doneEvent()

    def doUpdate(self):
        self.screen.fill(self.background)

        border = 10

        win = self.master.session.windows[0]
        wh = (self.height - 2*border) / self.fontheight
        ww = (self.width - 2*border) / self.fontwidth

        lines = win.linebuffer.render(ww, win.scroll, wh-2) \
              + [self.master.session.getPromptLine()]

        x = border
        y = border
        for l in lines:
            x = border
            for c in l:
                char = self.font.render(c[1], self.antialias, (c[0][0]*15,c[0][0]*15,c[0][0]*15), self.background)
                self.screen.blit(char, (x, y))
                x += self.fontwidth
            y += self.fontheight

        y -= self.fontheight

        # Prompt line
        if self.modeManager.getMode() == "normal":
            curline = self.font.render(self.normalMode.getBuffer(), self.antialias, (255,255,255), self.background)
            self.screen.blit(curline, (x, y))

            cursor = self.font.render("_", self.antialias, (255,255,255))
            self.screen.blit(cursor, (x + self.normalMode.getCursor()*self.fontwidth, y))
        elif self.modeManager.getMode() == "lua":
            x = border
            y += 2 * self.fontheight

            curline = self.font.render("\\" + self.luaMode.getBuffer(), self.antialias, (255,100,100), self.background)
            self.screen.blit(curline, (x, y))

            cursor = self.font.render("_", self.antialias, (255,255,255))
            self.screen.blit(cursor, (x + (self.luaMode.getCursor()+1)*self.fontwidth, y))

        pygame.display.flip()

