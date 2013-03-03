import wx
import wx.lib.newevent

from mudblood import event
from mudblood import screen
from mudblood import keys
from mudblood import modes
from mudblood import ansi

from mudblood.screen import modalscreen

DestroyEvent, EVT_DESTROY_EVENT = wx.lib.newevent.NewEvent()
UpdateEvent, EVT_UPDATE_EVENT = wx.lib.newevent.NewEvent()
ModeEvent, EVT_MODE_EVENT = wx.lib.newevent.NewEvent()

keymap = {
        ord('\r'):              ord('\n'),
        wx.WXK_F1:              keys.KEY_F1,
        wx.WXK_F2:              keys.KEY_F2,
        wx.WXK_F3:              keys.KEY_F3,
        wx.WXK_F4:              keys.KEY_F4,
        wx.WXK_F5:              keys.KEY_F5,
        wx.WXK_F6:              keys.KEY_F6,
        wx.WXK_F7:              keys.KEY_F7,
        wx.WXK_F8:              keys.KEY_F8,
        wx.WXK_F9:              keys.KEY_F9,
        wx.WXK_F10:             keys.KEY_F10,
        wx.WXK_F11:             keys.KEY_F11,
        wx.WXK_F12:             keys.KEY_F12,

        wx.WXK_NUMPAD0:         keys.KEY_NUMPAD0,
        wx.WXK_NUMPAD1:         keys.KEY_NUMPAD1,
        wx.WXK_NUMPAD2:         keys.KEY_NUMPAD2,
        wx.WXK_NUMPAD3:         keys.KEY_NUMPAD3,
        wx.WXK_NUMPAD4:         keys.KEY_NUMPAD4,
        wx.WXK_NUMPAD5:         keys.KEY_NUMPAD5,
        wx.WXK_NUMPAD6:         keys.KEY_NUMPAD6,
        wx.WXK_NUMPAD7:         keys.KEY_NUMPAD7,
        wx.WXK_NUMPAD8:         keys.KEY_NUMPAD8,
        wx.WXK_NUMPAD9:         keys.KEY_NUMPAD9,
}

def createScreen(master):
    return WxScreen(master)

class WxScreen(modalscreen.ModalScreen):
    def __init__(self, master):
        super(WxScreen, self).__init__(master)

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
        self.text.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTWEIGHT_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text.SetForegroundColour(wx.WHITE)
        self.text.SetBackgroundColour(wx.BLACK)

        self.text.Bind(wx.EVT_CHAR, self.doKey)
        self.text.SetFocus()

        self.win.Show(True)

        self.ready = True

        self.updateScreen()

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
        try:
            self.modeManager.setMode(ev.mode, **ev.args)
        except modes.UnsupportedModeException:
            self.put(event.LogEvent("Unsupported mode: {}".format(ev.mode), "err"))

    def doKey(self, ev):
        key = ev.GetKeyCode()

        if key in keymap:
            key = keymap[key]

        self.modeManager.key(key)
        self.updateScreen()

    def doUpdate(self, ev):
        if self.master.session is None:
            return

        lines = self.master.session.linebuffers['main'].lines

        pos = self.text.XYToPosition(0, self.text.GetNumberOfLines()-1)
        self.text.Remove(pos, pos+100)
        
        text = ""
        for l in lines[self.nlines:]:
            text += str(l) + "\n"

        text += str(self.master.session.getPromptLine())
        if self.modeManager.getMode() == "normal":
            text += self.normalMode.getBuffer()
        elif self.modeManager.getMode() == "lua":
            text += "lua: " + self.luaMode.getBuffer()
        elif self.modeManager.getMode() == "prompt":
            text += self.promptMode.getText() + self.promptMode.getBuffer()

        self.text.write(text)
        #self.text.SendTextUpdatedEvent()

        self.nlines = len(lines)
