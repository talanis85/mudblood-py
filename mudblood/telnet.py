import socket
import struct
import json
from mudblood import event

IAC = 255

EOR = 239
SE = 240
NOP = 241
DM = 242
BRK = 243
IP = 244
AO = 245
AYT = 246
EC = 247
EL = 248
GA = 249

SB = 250
WILL = 251
WONT = 252
DO = 253
DONT = 254


OPT_ECHO = 1
OPT_SUPPRESS_GA = 3
OPT_TIMING_MARK = 6
OPT_TTYPE = 24
OPT_EOR = 25
OPT_NAWS = 31
OPT_LINEMODE = 34

class TelnetEvent(event.Event):
    def __init__(self, cmd, option=None, data=None):
        super(TelnetEvent, self).__init__()
        self.cmd = cmd
        self.option = option
        self.data = data

    def __str__(self):
        return "TelnetEvent: cmd={} option={} data={}".format(self.cmd, self.option, self.data)

    def __eq__(self, other):
        return (isinstance(other, TelnetEvent) and self.cmd == other.cmd and self.option == other.option and self.data == other.data)

class GMCPEvent(event.Event):
    def __init__(self, data=None, module=None, obj=None):
        super(GMCPEvent, self).__init__()

        self.module = None
        self.data = None

        if data is not None:
            self.module, _, d = data.partition(" ")
            if d == "":
                self.data = None
            else:
                self.data = json.loads(d)

        if module is not None:
            self.module = module
            self.data = obj

    def dump(self):
        if self.module is None:
            return ""

        if self.data is None:
            return self.module
        else:
            return "{} {}".format(self.module, json.dumps(self.data))

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

        self.telnet_parsed = bytearray()
        self.telnet_state = 0
        self.telnet_command = 0
        self.telnet_option = 0
        self.telnet_data = bytearray()

    def poll(self):
        ret = self.file.read(1024)
        if ret == None:
            self.running = False
            self.put(event.DisconnectEvent())
        else:
            #parsed = bytearray()
            #state = 0
            #command = 0
            #option = 0
            #data = bytearray()

            for d in ret:
                # Remove in Python 3
                c = ord(d)

                if self.telnet_state == 1:
                    if c >= 240:
                        self.telnet_command = c
                        self.telnet_state = 2
                    else:
                        self.telnet_command = c
                        self.put(TelnetEvent(self.telnet_command, None, None))
                        self.telnet_state = 0
                elif self.telnet_state == 2:
                    self.telnet_option = c
                    if self.telnet_command == SB:
                        self.telnet_state = 3
                    else:
                        self.put(TelnetEvent(self.telnet_command, self.telnet_option, None))
                        self.telnet_state = 0
                elif self.telnet_state == 3:
                    if c == IAC:
                        self.telnet_state = 4
                    else:
                        self.telnet_data.append(c)
                elif self.telnet_state == 4:
                    if c == SE:
                        if self.telnet_option == 201:
                            # TODO: Which encoding?
                            self.put(TelnetEvent(self.telnet_command, self.telnet_option, self.telnet_data))
                            self.put(GMCPEvent(data=self.telnet_data.decode('utf8')))
                        else:
                            self.put(TelnetEvent(self.telnet_command, self.telnet_option, self.telnet_data))
                        self.telnet_state = 0
                    else:
                        self.telnet_data.append(IAC)
                        self.telnet_data.append(c)
                elif c == IAC:
                    if len(self.telnet_parsed) > 0:
                        self.put(event.RawEvent(bytes(self.telnet_parsed)))

                    self.telnet_parsed = bytearray()
                    self.telnet_command = 0
                    self.telnet_option = 0
                    self.telnet_data = bytearray()

                    self.telnet_state = 1
                elif c == ord("\r"):
                    pass
                elif c == ord("\b"):
                    self.telnet_parsed = self.telnet_parsed[:-1]
                elif c == 0x1b or c == ord("\n") or (c >= ord(" ") and c <= ord("~")):
                    self.telnet_parsed.append(c)

            if len(self.telnet_parsed) > 0:
                self.put(event.RawEvent(bytes(self.telnet_parsed)))

            self.telnet_parsed = bytearray()

    def write(self, buf):
        self.file.write(buf)

    def sendIAC(self, command, option):
        b = bytearray([IAC, command, option])
        self.put(event.LogEvent("Telnet: Sending {}".format(list(b)), "debug"))
        self.file.write(b)

    def sendSubneg(self, option, data):
        b = bytearray([IAC, SB, option]) + bytearray(data) + bytearray([IAC, SE])
        self.put(event.LogEvent("Telnet: Sending {}".format(list(b)), "debug"))
        self.file.write(b)

    def sendGMCP(self, gmcp):
        self.sendSubneg(201, gmcp.dump().encode('utf8'))

    def sendNaws(self, w, h):
        self.sendSubneg(OPT_NAWS, struct.pack('!HH', w, h))

