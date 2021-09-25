import bisect
import json
from collections import deque
from pathlib import Path

from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    QueuedConnectionManager,
    QueuedConnectionListener,
    QueuedConnectionReader,
    ConnectionWriter,
    PointerToConnection,
    NetAddress,
    NetDatagram
)
from direct.task.Task import Task

SCORES_FILE = Path("scores.json")
if not SCORES_FILE.exists():
    with open(SCORES_FILE, "w") as f:
        json.dump([], f)

PORT_ADDRESS = 9099
BACKLOG = 1000

POST_SCORE = 1
GET_LEADERBOARD = 2


def datagram_from_list(list_):
    string = json.dumps(list_)
    datagram = PyDatagram()
    datagram.addString(string)
    return datagram


class Server(ShowBase):
    def __init__(self):
        super().__init__()
        with open(SCORES_FILE) as file:
            self.scores = deque(json.load(file))

        self.c_manager = QueuedConnectionManager()
        self.c_listener = QueuedConnectionListener(self.c_manager, 0)
        self.c_reader = QueuedConnectionReader(self.c_manager, 0)
        self.c_writer = ConnectionWriter(self.c_manager, 0)

        self.active_connections = []

        tcp_socket = self.c_manager.openTCPServerRendezvous(PORT_ADDRESS, BACKLOG)

        self.c_listener.addConnection(tcp_socket)
        self.taskMgr.add(self.tsk_listener_polling, "Poll the connection listener", -39)
        self.taskMgr.add(self.tsk_reader_polling, "Poll the connection reader", -40)
        self.taskMgr.doMethodLater(5, self.save_to_file_task, "SaveToFile")

    def tsk_listener_polling(self, _task):
        if self.c_listener.newConnectionAvailable():
            rendezvous = PointerToConnection()
            net_address = NetAddress()
            new_connection = PointerToConnection()

            if self.c_listener.getNewConnection(rendezvous, net_address, new_connection):
                print("connecting")
                new_connection = new_connection.p()
                self.active_connections.append(new_connection)
                self.c_reader.addConnection(new_connection)
        return Task.cont

    def tsk_reader_polling(self, _task):
        if self.c_reader.dataAvailable():
            datagram = NetDatagram()
            if self.c_reader.getData(datagram):
                datagram_iterator = PyDatagramIterator(datagram)
                message_category = datagram_iterator.getUint8()
                if message_category == POST_SCORE:
                    username, score = datagram_iterator.getString(), datagram_iterator.getUint64()
                    print("received", username, score)
                    bisect.insort(self.scores, [score, username])
                    if len(self.scores) > 10:
                        self.scores.popleft()
                elif message_category == GET_LEADERBOARD:
                    print("rcvd")
                    self.c_writer.send(datagram_from_list(list(self.scores)), datagram.getConnection())
        return Task.cont

    def save_to_file_task(self, _task):
        with open(SCORES_FILE, "w") as file:
            json.dump(list(self.scores), file)
        return Task.again


if __name__ == "__main__":
    server = Server()
    server.run()
