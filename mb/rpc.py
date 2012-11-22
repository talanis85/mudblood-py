import event
import socketserver
import asynchat
import socket
import os
import json

class RPCEvent(event.Event):
    def __init__(self, literal=None, func="", args=[]):
        super().__init__()
        self.literal = literal
        self.func = func
        self.args = args

class RPCServerHandler(socketserver.StreamRequestHandler):
    def handle(self):
        data = self.rfile.read().decode('utf8')
        ob = json.loads(data)
        if "literal" in ob:
            self.server.rpc_source.put(RPCEvent(literal=ob['literal']))
        else:
            self.server.rpc_source.put(RPCEvent(func=ob['func'], args=ob['args']))
        self.server.rpc_source.put(event.LogEvent("Got RPC:\n{}\nEOF".format(data), "debug"))

class RPCServerSocket(event.AsyncSource):
    def __init__(self, path):
        self.path = path

        if os.path.exists(path):
            os.unlink(path)

        self.server = socketserver.UnixStreamServer(path, RPCServerHandler)
        self.server.rpc_source = self
        super().__init__()

    def run(self):
        self.put(event.LogEvent("Started RPC Server on {}".format(self.path), "info"))
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()
        self.thread.join()

def call(path, func, args):
    data = json.dumps({'func': func, 'args': args})

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(path)
    sock.sendall(data.encode('utf8'))
    sock.close()

def callLiteral(path, data):
    data = json.dumps({'literal': data})

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(path)
    sock.sendall(data.encode('utf8'))
    sock.close()
