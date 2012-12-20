import socket
from mudblood import event

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
    def __init__(self, cmd, option=None, data=None):
        super(TelnetEvent, self).__init__()
        self.cmd = cmd
        self.option = option
        self.data = data

    def __str__(self):
        return "TelnetEvent: cmd={} option={} data={}".format(self.cmd, self.option, self.data)

class TCPSocket(object):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect(self, host, port):
        self.socket.connect((host, port))

    def read(self, size):
        ret = self.socket.recv(size)
        if ret == b'':
            return None
        return ret

    def write(self, string):
        self.socket.send(string)

class Telnet(event.AsyncSource):
    def __init__(self, file):
        super(Telnet, self).__init__()
        self.file = file

    def poll(self):
        ret = self.file.read(1024)
        if ret == None:
            self.running = False
            self.put(event.DisconnectEvent())
        else:
            parsed = bytearray()
            state = 0
            command = 0
            option = 0
            data = bytearray()

            for d in ret:
                # Remove in Python 3
                c = ord(d)

                if state == 1:
                    if c >= 240:
                        command = c
                        state = 2
                    else:
                        command = c
                        self.put(TelnetEvent(command, None, None))
                        state = 0
                elif state == 2:
                    option = c
                    if command == SB:
                        state = 3
                    else:
                        self.put(TelnetEvent(command, option, None))
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
                    if len(parsed) > 0:
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

            if len(parsed) > 0:
                self.put(event.RawEvent(bytes(parsed)))

    def write(self, buf):
        self.file.write(buf)

    def sendIAC(self, command, option):
        b = bytearray([IAC, command, option])
        self.put(event.LogEvent("Telnet: Sending {}".format(b), "debug"))
        self.file.write(b)

    def sendSubneg(self, option, data):
        b = bytes([IAC, SB, option]) + bytes(data) + bytes([IAC, SE])
        self.put(event.LogEvent("Telnet: Sending {}".format(b), "debug"))
        self.file.write(b)
