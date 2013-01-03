import wx
import wx.lib.newevent

from mudblood import event
from mudblood import screen
from mudblood import keys
from mudblood import modes
from mudblood import ansi

from mudblood.screen import modalscreen

from mudblood.main import MB

DestroyEvent, EVT_DESTROY_EVENT = wx.lib.newevent.NewEvent()
UpdateEvent, EVT_UPDATE_EVENT = wx.lib.newevent.NewEvent()
ModeEvent, EVT_MODE_EVENT = wx.lib.newevent.NewEvent()

class WxScreen(modalscreen.ModalScreen):
    def __init__(self):
        super(WxScreen, self).__init__()

        self.ready = False
        self.nlines = 0
    
    def updateScreen(self):
        pass

    def run(self):
        self.app = wx.App(False)
        self.app.Bind(EVT_DESTROY_EVENT, self.doDestroy)
        self.app.Bind(EVT_UPDATE_EVENT, self.doUpdate)
        self.app.Bind(EVT_MODE_EVENT, self.doMode)

        self.win = wx.Frame(None, wx.ID_ANY, "Mudblood")

        self.text = wx.TextCtrl(self.win, style=wx.TE_MULTILINE)
        self.text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Terminus'))
        self.text.SetForegroundColour(wx.WHITE)
        self.text.SetBackgroundColour(wx.BLACK)

        self.text.Bind(wx.EVT_CHAR, self.doKey)
        self.text.SetFocus()

        self.win.Show(True)

        self.ready = True

        self.app.MainLoop()

    def destroy(self):
        wx.PostEvent(self.app, DestroyEvent())

    def join(self):
        pass

    def setMode(self, mode, **kwargs):
        wx.PostEvent(self.app, ModeEvent(mode=mode, args=kwargs))

    def updateScreen(self):
        if self.ready:
            wx.PostEvent(self.app, UpdateEvent())

    def doDestroy(self, ev):
        self.win.Close(True)

    def doMode(self, ev):
        self.modeManager.setMode(ev.mode, **ev.args)

    def doKey(self, ev):
        key = ev.GetKeyCode()

        if key == ord('\r'):
            key = ord('\n')

        self.modeManager.key(key)
        self.updateScreen()

    def doUpdate(self, ev):
        lines = MB().session.windows[0].linebuffer.lines

        pos = self.text.XYToPosition(0, self.text.GetNumberOfLines()-1)
        self.text.Remove(pos, pos+100)
        
        text = ""
        for l in lines[self.nlines:]:
            text += str(l) + "\n"

        text += str(MB().session.getPromptLine())
        if self.modeManager.getMode() == "normal":
            text += self.normalMode.getBuffer()
        elif self.modeManager.getMode() == "lua":
            text += "lua: " + self.luaMode.getBuffer()
        elif self.modeManager.getMode() == "prompt":
            text += self.promptMode.getText() + self.promptMode.getBuffer()

        self.text.write(text)
        #self.text.SendTextUpdatedEvent()

        self.nlines = len(lines)
