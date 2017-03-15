import abc
import imp
import random
from abc import ABCMeta
from datetime import datetime, timedelta

from pyactor.context import set_context, create_host, serve_forever

from Tracker import Tracker
from client.Torrent import Torrent

try:
    imp.find_module('bitarray')
    found = True
except ImportError:
    found = False


class Peer(object):
    __metaclass__ = ABCMeta  # Abstract class
    _tell = ["active_thread", "announce", "update_peers", "push", "run", "add_torrent", "remove_torrent", "get_files"]
    _ask = []

    def __init__(self):
        self.gossip_cycle = 1
        self.announce_timeout = 10
        self.discovery_period = 2
        self.download_folder = ""
        self.torrents = {}  # Key: File name; Value: Torrent

    @abc.abstractmethod
    def active_thread(self):
        raise NotImplementedError("Subclass must implement abstract method")

    # Don't override
    def announce(self):
        for file_name, torrent in self.torrents.items():
            for tracker in torrent.trackers:
                tracker.announce(file_name, self.proxy)

    # Don't override
    def update_peers(self):
        for file_name, torrent in self.torrents.items():
            torrent.peers = []
            for tracker in torrent.trackers:
                future = tracker.get_peers(file_name, future=True)
                future.add_callback("update_peers_callback")

    def update_peers_callback(self, future):
        if future.result() is None:
            return
        self.torrents[future.result()[0]].peers += future.result()[1]
        print self.id + " has received peers:  " + str(map(lambda proxy: proxy.actor.id, future.result()[1]))

    def run(self, download_folder=""):
        self.download_folder = download_folder
        for torrent in self.torrents.values():
            torrent.completed = torrent.file.initial_status(self.download_folder)
            torrent.trackers = [self.host.lookup(tracker) for tracker in torrent.file.get_json("Trackers")]

        self.loop1 = self.host.interval(self.announce_timeout, self.proxy, "announce")
        self.loop2 = self.host.interval(self.discovery_period, self.proxy, "update_peers")
        self.loop3 = self.host.interval(self.gossip_cycle, self.proxy, "active_thread")

    def add_torrent(self, torrent):
        if torrent.file.name in self.torrents.keys():
            self.torrents[torrent.file.name].trackers += torrent.trackers
            # Remove duplicated trackers
            self.torrents[torrent.file.name].trackers = list(set(self.torrents[torrent.file.name].trackers))
        else:
            self.torrents[torrent.file.name] = torrent

    def remove_torrent(self, torrent):
        self.torrents.pop(torrent)

    def choose_random_peer(self, peers):
        candidate = peers[random.randint(0, len(peers) - 1)]
        while candidate == self.proxy:
            candidate = peers[random.randint(0, len(peers) - 1)]
        return candidate

    def get_files(self):
        return self.torrents.keys()

    # Public actor methods ***************
    def push(self, chunk_id, chunk_data, file_name):
        torrent = self.torrents[file_name]
        if torrent is None or (torrent.file.chunk_map[chunk_id] is True) or torrent.completed:
            return

        file = None
        try:
            torrent.file.set_chunk(chunk_id, chunk_data)
            torrent.update(chunk_id)
        except (IOError, IndexError) as error:
            print "Error on chunk writing"
            return

        finally:
            if file is not None:
                file.close()

    # **********************************


class PushPeer(Peer):
    _tell = ["active_thread", "announce", "update_peers", "push", "run", "add_torrent", "remove_torrent", "get_files"]
    _ask = []

    def __init__(self):
        super(PushPeer, self).__init__()

    def active_thread(self):
        for torrent in self.torrents.values():
            # Critical section with update_peers
            if len(torrent.peers) <= 1:     # Not itself
                return
            p = self.choose_random_peer(torrent.peers)
            # End of critical section
            chunk_index = random.randint(0, torrent.file.size-2)    # Ignore EOF
            if torrent.file.chunk_map[chunk_index]:     # If valid chunk
                p.push(chunk_index, torrent.file.get_chunk(chunk_index), torrent.file.name)
                print self.id + " pushing " + str(chunk_index) + " " + torrent.file.get_chunk(chunk_index) + " to " + p.actor.url


class PullPeer(Peer):
    def __init__(self):
        Peer.__init__(self)


class PushPullPeer(PushPeer, PullPeer):
    def __init__(self):
        Peer.__init__(self)


if __name__ == "__main__":
    if not found:
        print "Missing package bitarray https://pypi.python.org/pypi/bitarray"

    set_context()
    host = create_host()

    tracker = host.spawn("tracker1", Tracker)
    tracker.run()

    # tracker2 = host.spawn("tracker2", Tracker)
    # tracker2.run()

    t1 = Torrent("torrent2.json")
    t2 = Torrent("torrent2.json")
    #t2 = Torrent("torrent2.json")

    t1.refresh_metadata()

    c1 = host.spawn("peer1", PushPeer)
    c1.add_torrent(t1)
    # c1.add_torrent(t2)

    c2 = host.spawn("peer2", PushPeer)
    c2.add_torrent(t2)
    # c2.add_torrent(t2)

    c1.run("./Descargas")
    c2.run()

    #sleep(15)
    #host.stop_actor("peer2")

    serve_forever()
