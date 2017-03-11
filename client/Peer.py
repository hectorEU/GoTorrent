import abc
import random
from abc import ABCMeta
from datetime import datetime


class Peer(object):
    __metaclass__ = ABCMeta  # Abstract class
    _tell = ["run", "push", "add_torrent", "active_thread"]
    _ask = []
    _ref = ["push"]
    _parallel = ["push"]

    def __init__(self, delta):
        self.gossip_cycle = delta
        self.torrents = {}

    @abc.abstractmethod
    def active_thread(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def push(self, chunk_id, chunk_data, file_name="example.txt"):
        t = self.torrents[file_name]
        if t.completed:
            return

        file = None
        try:
            file = open(file_name, "w+")
            file.seek(chunk_id)
            file.write(chunk_data)
        except (IOError, IndexError) as error:
            return

        finally:
            if file is not None:
                file.close()

        t.update()

    def run(self):
        self.loop = self.host.interval(self.gossip_cycle, self.proxy, "active_thread")

    def add_torrent(self, torrent):
        self.torrents[torrent.file.fp] = torrent

    def remove_torrent(self, torrent):
        self.torrents.remove(torrent)

    @staticmethod
    def choose_random_peer(peers):
        return peers[random.randint(0, len(peers) - 1)]


class PushPeer(Peer):
    _tell = ["run", "push", "add_torrent", "active_thread"]
    _ask = []
    _ref = ["push"]
    _parallel = ["push"]

    def __init__(self, delta=1):
        Peer.__init__(self, delta)

    def active_thread(self):
        for torrent in super(PushPeer, self).torrents.values():
            if torrent.last_discovery > datetime.now() + torrent.discovery_period:
                for tracker in torrent.trackers:
                    torrent.peers += tracker.get_peers(torrent.file.id)
            p = Peer.choose_random_peer(torrent.peers)

            chunk_index = random.randint(0, torrent.file.size)
            p.push(chunk_index, torrent.file.get_chunk(chunk_index), torrent.file.fp)


class PullPeer(Peer):
    def __init__(self, delta=1):
        Peer.__init__(self, delta)


class PushPullPeer(PushPeer, PullPeer):
    def __init__(self, delta=1):
        Peer.__init__(self, delta)
