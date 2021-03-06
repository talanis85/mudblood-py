import sys
import tty
import termios

class Terminal(object):
    def __init__(self, name):
        self.name = name
        self.terminfo = Terminfo(name)
        self.oldsettings = None

    def setup(self):
        self.oldsettings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    def reset(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.oldsettings)

    def write(self, data):
        sys.stdout.write(data)

    def read(self, count):
        return sys.stdin.read(count)

    def flush(self):
        sys.stdout.flush()

    def _dofunc(self, func):
        sys.stdout.write(self.terminfo.function(func))
        sys.stdout.flush()

    def enter_keypad(self):
        self._dofunc('ENTER_KEYPAD')

    def exit_keypad(self):
        self._dofunc('EXIT_KEYPAD')

    def erase_line(self):
        self._dofunc('ERASE_LINE')

    def cursor_up(self):
        self._dofunc('CURSOR_UP')

class Terminfo(object):
    def __init__(self, name):
        self.name = name

    def function(self, name):
        return self.terminfo[self.name]['functions'][name]

    def keys(self):
        return self.terminfo[self.name]['keys']

    terminfo = {
        'Eterm': (
            ["\033[11~","\033[12~","\033[13~","\033[14~","\033[15~","\033[17~","\033[18~","\033[19~","\033[20~","\033[21~","\033[23~","\033[24~","\033[2~","\033[3~","\033[7~","\033[8~","\033[5~","\033[6~","\033[A","\033[B","\033[D","\033[C", 0],
            {
                'ENTER_CA': "\0337\033[?47h",
                'EXIT_CA': "\033[2J\033[?47l\0338",
                'SHOW_CURSOR': "\033[?25h",
                'HIDE_CURSOR': "\033[?25l",
                'CLEAR_SCREEN': "\033[H\033[2J",
                'SGR0': "\033[m",
                'UNDERLINE': "\033[4m",
                'BOLD': "\033[1m",
                'BLINK': "\033[5m",
                'ENTER_KEYPAD': "",
                'EXIT_KEYPAD': "",
            }),
        'screen': (
            ["\033OP","\033OQ","\033OR","\033OS","\033[15~","\033[17~","\033[18~","\033[19~","\033[20~","\033[21~","\033[23~","\033[24~","\033[2~","\033[3~","\033[1~","\033[4~","\033[5~","\033[6~","\033OA","\033OB","\033OD","\033OC", 0],
            {
                'ENTER_CA': "\033[?1049h",
                'EXIT_CA': "\033[?1049l",
                'SHOW_CURSOR': "\033[34h\033[?25h",
                'HIDE_CURSOR': "\033[?25l",
                'CLEAR_SCREEN': "\033[H\033[J",
                'SGR0': "\033[m",
                'UNDERLINE': "\033[4m",
                'BOLD': "\033[1m",
                'BLINK': "\033[5m",
                'ENTER_KEYPAD': "\033[?1h\033=",
                'EXIT_KEYPAD': "\033[?1l\033>",
            }),
        'xterm': {
            'keys': {
                'F1': "\033OP",
                'F2': "\033OQ",
                'F3': "\033OR",
                'F4': "\033OS",
                'F5': "\033[15~",
                'F6': "\033[17~",
                'F7': "\033[18~",
                'F8': "\033[19~",
                'F9': "\033[20~",
                'F10': "\033[21~",
                'F11': "\033[23~",
                'F12': "\033[24~",
                'INSERT': "\033[2~",
                'DELETE': "\033[3~",
                'HOME': "\033OH",
                'END': "\033OF",
                'PGUP': "\033[5~",
                'PGDN': "\033[6~",
                'ARROW_UP': "\033OA",
                'ARROW_DOWN': "\033OB",
                'ARROW_LEFT': "\033OD",
                'ARROW_RIGHT': "\033OC",
            },
            'functions': {
                'ENTER_CA': "\033[?1049h",
                'EXIT_CA': "\033[?1049l",
                'SHOW_CURSOR': "\033[?12l\033[?25h",
                'HIDE_CURSOR': "\033[?25l",
                'CLEAR_SCREEN': "\033[H\033[2J",
                'SGR0': "\033(B\033[m",
                'UNDERLINE': "\033[4m",
                'BOLD': "\033[1m",
                'BLINK': "\033[5m",
                'ENTER_KEYPAD': "\033[?1h\033=",
                'EXIT_KEYPAD': "\033[?1l\033>",
                'ERASE_LINE': "\033[2K",
                'CURSOR_UP': "\033[1A",
            }},
        'rxvt-unicode': (
            ["\033[11~","\033[12~","\033[13~","\033[14~","\033[15~","\033[17~","\033[18~","\033[19~","\033[20~","\033[21~","\033[23~","\033[24~","\033[2~","\033[3~","\033[7~","\033[8~","\033[5~","\033[6~","\033[A","\033[B","\033[D","\033[C", 0],
            {
                'ENTER_CA': "\033[?1049h",
                'EXIT_CA': "\033[r\033[?1049l",
                'SHOW_CURSOR': "\033[?25h",
                'HIDE_CURSOR': "\033[?25l",
                'CLEAR_SCREEN': "\033[H\033[2J",
                'SGR0': "\033[m\033(B",
                'UNDERLINE': "\033[4m",
                'BOLD': "\033[1m",
                'BLINK': "\033[5m",
                'ENTER_KEYPAD': "\033=",
                'EXIT_KEYPAD': "\033>",
            }),
        'linux': (
            ["\033[[A","\033[[B","\033[[C","\033[[D","\033[[E","\033[17~","\033[18~","\033[19~","\033[20~","\033[21~","\033[23~","\033[24~","\033[2~","\033[3~","\033[1~","\033[4~","\033[5~","\033[6~","\033[A","\033[B","\033[D","\033[C", 0],
            {
                'ENTER_CA': "",
                'EXIT_CA': "",
                'SHOW_CURSOR': "\033[?25h\033[?0c",
                'HIDE_CURSOR': "\033[?25l\033[?1c",
                'CLEAR_SCREEN': "\033[H\033[J",
                'SGR0': "\033[0;10m",
                'UNDERLINE': "\033[4m",
                'BOLD': "\033[1m",
                'BLINK': "\033[5m",
                'ENTER_KEYPAD': "",
                'EXIT_KEYPAD': "",
            }),
        'rxvt-256color': (
            ["\033[11~","\033[12~","\033[13~","\033[14~","\033[15~","\033[17~","\033[18~","\033[19~","\033[20~","\033[21~","\033[23~","\033[24~","\033[2~","\033[3~","\033[7~","\033[8~","\033[5~","\033[6~","\033[A","\033[B","\033[D","\033[C", 0],
            {
                'ENTER_CA': "\0337\033[?47h",
                'EXIT_CA': "\033[2J\033[?47l\0338",
                'SHOW_CURSOR': "\033[?25h",
                'HIDE_CURSOR': "\033[?25l",
                'CLEAR_SCREEN': "\033[H\033[2J",
                'SGR0': "\033[m",
                'UNDERLINE': "\033[4m",
                'BOLD': "\033[1m",
                'BLINK': "\033[5m",
                'ENTER_KEYPAD': "\033=",
                'EXIT_KEYPAD': "\033>",
            }),
        }
