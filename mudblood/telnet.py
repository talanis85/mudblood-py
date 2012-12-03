import socket
from mudblood import event
from mudblood import lua

IAC = 255
WILL = 251
WONT = 252
DO = 253
DONT = 254
NOP = 241
SB = 250
SE = 240

CMD_EOR = 239

OPT_EOR = 25

class TelnetEvent(event.Event):
    def __init__(self, cmd, option, data=None):
        super().__init__()
        self.cmd = cmd
        self.option = option
        self.data = data

    def __str__(self):
        return "TelnetEvent: cmd={} option={} data={}".format(self.cmd, self.option, self.data)

class Telnet(event.AsyncSource):
    def __init__(self, host, port):
        super().__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def poll(self):
        ret = self.socket.recv(1024)
        if ret == b'':
            self.running = False
            return event.DisconnectEvent()
        else:
            parsed = bytearray()
            state = 0
            command = 0
            option = 0
            data = bytearray()

            for c in ret:
                if state == 1:
                    if c >= 240:
                        command = c
                        state = 2
                    else:
                        command = c
                        self.put(TelnetEvent(command, option, data))
                        state = 0
                elif state == 2:
                    option = c
                    if command == SB:
                        state = 3
                    else:
                        self.put(TelnetEvent(command, option, data))
                        state = 0
                elif state == 3:
                    if c == IAC:
                        state = 4
                    else:
                        data.append(c)
                elif state == 4:
                    if c == SE:
                        self.put(TelnetEvent(command, option, data))
                        state = 0
                    else:
                        data.append(IAC)
                        data.append(c)
                elif c == IAC:
                    self.put(event.RawEvent(bytes(parsed)))

                    parsed = bytearray()
                    command = 0
                    option = 0
                    data = bytearray()

                    state = 1
                elif c == ord("\r"):
                    pass
                elif c == 0x1b or c == ord("\n") or (c >= ord(" ") and c <= ord("~")):
                    parsed.append(c)

            return event.RawEvent(bytes(parsed))

    def write(self, buf):
        self.socket.send(buf)

    def sendIAC(self, command, option):
        b = bytes([IAC, command, option])
        self.put(event.LogEvent("Telnet: Sending {}".format(b), "debug"))
        self.socket.send(b)

    def sendSubneg(self, option, data):
        b = bytes([IAC, SB, option]) + bytes(data) + bytes([IAC, SE])
        self.put(event.LogEvent("Telnet: Sending {}".format(b), "debug"))
        self.socket.send(b)
