import json

from panda3d.core import (
    QueuedConnectionManager,
    QueuedConnectionReader,
    ConnectionWriter,
    NetDatagram
)

from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator


class Client:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

        self.manager = QueuedConnectionManager()
        self.reader = QueuedConnectionReader(self.manager, 0)
        self.writer = ConnectionWriter(self.manager, 0)

        self.timeout = 8000 # 8 seconds
        self.conn = self.manager.openTCPClientConnection(self.addr, self.port, self.timeout)
        if self.conn:
            self.reader.addConnection(self.conn)
        else:
            print("Could not connect to server")

    def upload_score(self, name, score):
        data = PyDatagram()
        data.addUint8(1)
        data.addString(name)
        data.addUint64(score)
        self.writer.send(data, self.conn)

    def get_leaderboard(self):
        netdata = NetDatagram()
        data_cat = PyDatagram()
        data_cat.addUint8(2)
        self.writer.send(data_cat, self.conn)

        scores = []
        while not self.reader.dataAvailable():
            pass
        if self.reader.dataAvailable():
            self.reader.getData(netdata)
            data_iter = PyDatagramIterator(netdata)
            score_str = data_iter.getString()
            scores = json.loads(score_str)
        print(scores)
        return scores

    def close(self):
        self.manager.closeConnection(self.conn)
