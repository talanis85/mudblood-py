KEY_F1			= (0xFFFF-0)
KEY_F2			= (0xFFFF-1)
KEY_F3			= (0xFFFF-2)
KEY_F4			= (0xFFFF-3)
KEY_F5			= (0xFFFF-4)
KEY_F6			= (0xFFFF-5)
KEY_F7			= (0xFFFF-6)
KEY_F8			= (0xFFFF-7)
KEY_F9			= (0xFFFF-8)
KEY_F10			= (0xFFFF-9)
KEY_F11			= (0xFFFF-10)
KEY_F12			= (0xFFFF-11)
KEY_INSERT		= (0xFFFF-12)
KEY_DELETE		= (0xFFFF-13)
KEY_HOME		= (0xFFFF-14)
KEY_END			= (0xFFFF-15)
KEY_PGUP		= (0xFFFF-16)
KEY_PGDN		= (0xFFFF-17)
KEY_ARROW_UP		= (0xFFFF-18)
KEY_ARROW_DOWN		= (0xFFFF-19)
KEY_ARROW_LEFT		= (0xFFFF-20)
KEY_ARROW_RIGHT		= (0xFFFF-21)

KEY_CTRL_TILDE		= 0x00
KEY_CTRL_2		= 0x00
KEY_CTRL_A		= 0x01
KEY_CTRL_B		= 0x02
KEY_CTRL_C		= 0x03
KEY_CTRL_D		= 0x04
KEY_CTRL_E		= 0x05
KEY_CTRL_F		= 0x06
KEY_CTRL_G		= 0x07
KEY_BACKSPACE		= 0x08
KEY_CTRL_H		= 0x08
KEY_TAB			= 0x09
KEY_CTRL_I		= 0x09
KEY_CTRL_J		= 0x0A
KEY_CTRL_K		= 0x0B
KEY_CTRL_L		= 0x0C
KEY_ENTER		= 0x0D
KEY_CTRL_M		= 0x0D
KEY_CTRL_N		= 0x0E
KEY_CTRL_O		= 0x0F
KEY_CTRL_P		= 0x10
KEY_CTRL_Q		= 0x11
KEY_CTRL_R		= 0x12
KEY_CTRL_S		= 0x13
KEY_CTRL_T		= 0x14
KEY_CTRL_U		= 0x15
KEY_CTRL_V		= 0x16
KEY_CTRL_W		= 0x17
KEY_CTRL_X		= 0x18
KEY_CTRL_Y		= 0x19
KEY_CTRL_Z		= 0x1A
KEY_ESC			= 0x1B
KEY_CTRL_LSQ_BRACKET	= 0x1B
KEY_CTRL_3		= 0x1B
KEY_CTRL_4		= 0x1C
KEY_CTRL_BACKSLASH	= 0x1C
KEY_CTRL_5		= 0x1D
KEY_CTRL_RSQ_BRACKET	= 0x1D
KEY_CTRL_6		= 0x1E
KEY_CTRL_7		= 0x1F
KEY_CTRL_SLASH		= 0x1F
KEY_CTRL_UNDERSCORE	= 0x1F
KEY_SPACE		= 0x20
KEY_BACKSPACE2		= 0x7F
KEY_CTRL_8		= 0x7F

class Bindings(object):
    specialKeys = {
            "E": ord("\\"),
            "TAB": ord("\t"),

            "F1": KEY_F1,
            "F2": KEY_F2,
            "F3": KEY_F3,
            "F4": KEY_F4,
            "F5": KEY_F5,
            "F6": KEY_F6,
            "F7": KEY_F7,
            "F8": KEY_F8,
            "F9": KEY_F9,
            "F10": KEY_F10,
            "F11": KEY_F11,
            "F12": KEY_F12,
            }

    def __init__(self):
        self.bindings = dict()
        self.keybuffer = []

    def add(self, keys, value):
        self.bindings[keys] = value

    def reset(self):
        self.keybuffer = []

    def key(self, key):
        """
        Returns:
            True:       incomplete key sequence
            Function:   complete key sequence
            False:      no key sequence
        """
        self.keybuffer.append(key)

        pref = False
        for k in self.bindings:
            if k == tuple(self.keybuffer):
                return self.bindings[k]
            for i in range(min([len(self.keybuffer), len(k)])):
                pref = True
                if self.keybuffer[i] != k[i]:
                    pref = False
                if not pref:
                    continue
            if pref:
                break

        return pref

    def parseAndAdd(self, keystr, value):
        keys = []
        specialKey = None

        for c in keystr:
            if c == "<":
                specialKey = ""
            elif c == ">":
                keys.append(self.specialKeys[specialKey])
                specialKey = None
            elif specialKey == None:
                keys.append(ord(c))
            else:
                specialKey += c

        self.add(tuple(keys), value)
