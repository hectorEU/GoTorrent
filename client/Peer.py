import abc
import imp
import os
from abc import ABCMeta

from pyactor.context import set_context, create_host, serve_forever

from Tracker import Tracker
from client.Torrent import Torrent
from output import _print, _error

try:
    imp.find_module('bitarray')
    found = True
except ImportError:
    found = False


class Peer(object):
    __metaclass__ = ABCMeta  # Abstract class
    _tell = ["push", "add_torrent", "remove_torrent", "run", "announce", "update_peers", "active_thread"]
    _ask = ["pull"]

    def __init__(self):
        self.gossip_cycle = 1
        self.announce_timeout = 10
        self.discovery_period = 2
        self.download_folder = ""
        self.torrents = {}  # Key: File name; Value: Torrent

    @abc.abstractmethod
    def active_thread(self):
        raise NotImplementedError("Subclass must implement abstract method")

    # Announces ownership of every torrent to every tracker
    def announce(self):
        for file_name, torrent in self.torrents.items():
            for tracker in torrent.trackers:
                tracker.announce(file_name, self.proxy)

    # Update active peers from the swarm ************************
    def update_peers(self):
        for file_name, torrent in self.torrents.items():
            torrent.peers = []  # Resets torrent peers
            for tracker in torrent.trackers:
                future = tracker.get_peers(file_name, future=True)  # Performs a non-blocking call
                future.add_callback("update_peers_callback")  # Executes callback when Tracker returns

    def update_peers_callback(self, future):
        file_name = future.result()[0]
        peers = future.result()[1]
        if peers is None or len(peers) == 1:  # Avoid lone peer in swarm
            return
        self.torrents[file_name].peers += peers  # Sum up peers from all trackers
        self.torrents[file_name].peers.remove(self.proxy)
        _print(self, "knows these peers: " + str(map(lambda proxy: proxy.actor.id, self.torrents[file_name].peers)))

    # ***********************************************************

    # Activate peer
    def run(self, download_folder="./"):
        self.download_folder = download_folder  # Sets main download folder
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
        for torrent in self.torrents.values():  # Initializes every tracker
            torrent.file.initial_status(self.download_folder)
            torrent.trackers = [self.host.lookup(tracker) for tracker in torrent.file.get_json("Trackers")]

        self.loop1 = self.host.interval(self.announce_timeout, self.proxy, "announce")
        self.loop2 = self.host.interval(self.discovery_period, self.proxy, "update_peers")
        self.loop3 = self.host.interval(self.gossip_cycle, self.proxy, "active_thread")

    def add_torrent(self, torrent):
        if torrent.file.name in self.torrents.keys():
            # If torrent already exists, add trackers
            self.torrents[torrent.file.name].trackers += torrent.trackers
            # Remove duplicated trackers
            self.torrents[torrent.file.name].trackers = list(set(self.torrents[torrent.file.name].trackers))
        else:
            self.torrents[torrent.file.name] = torrent

    def remove_torrent(self, torrent):
        self.torrents.pop(torrent)

    # Public actor methods ******************************
    # Receive chunk_data
    def push(self, chunk_id, chunk_data, file_name):
        torrent = self.torrents[file_name]
        if torrent is None or torrent.file.completed:  # Filter unwanted chunks
            return
        try:
            torrent.file.set_chunk(chunk_id, chunk_data)
            torrent.update()
        except (IndexError, TypeError):
            _error(self, "invalid push, chunk index out of file bounds or corrupt data")

    # Send chunk_data
    def pull(self, chunk_id, file_name):
        torrent = self.torrents[file_name]
        if torrent is not None:  # If this peer is in the swarm, "pull" should be called with correct file_name
            return file_name, chunk_id, torrent.file.get_chunk(chunk_id)
        return file_name, False

        # ***********************************************


class PushPeer(Peer):
    def __init__(self):
        super(PushPeer, self).__init__()

    def active_thread(self):
        for torrent in self.torrents.values():
            if torrent.file.downloaded == 0:
                continue  # If peer has no content to disseminate from this torrent, try next
            chunk_id = torrent.file.get_random_chunk_id()
            chunk_data = torrent.file.get_chunk(chunk_id)
            while not chunk_data:  # Loop until valid chunk found
                chunk_id = torrent.file.get_random_chunk_id()
                chunk_data = torrent.file.get_chunk(chunk_id)
            for peer in torrent.peers:  # Shares this chunk among known peers
                peer.push(chunk_id, chunk_data, torrent.file.name)
                _print(self, "pushing " + str(chunk_id) + " " + chunk_data + " to " + peer.actor.url)


class PullPeer(Peer):
    def __init__(self):
        super(PullPeer, self).__init__()

    def active_thread(self):
        for torrent in self.torrents.values():
            for peer in torrent.peers:
                if torrent.file.completed:
                    break  # Torrent complete, ask for chunks of incomplete torrents
                chunk_id = torrent.file.get_random_chunk_id()
                while torrent.file.chunk_map[chunk_id]:  # Loop until an empty chunk is found
                    chunk_id = torrent.file.get_random_chunk_id()
                future = peer.pull(chunk_id, torrent.file.name, future=True)
                future.add_callback("pull_callback")
                _print(self, "polling " + str(chunk_id) + " from " + peer.actor.url)

    def pull_callback(self, future):
        file_name = future.result()[0]
        chunk_id = future.result()[1]
        chunk_data = future.result()[2]
        if not chunk_data:
            return
        self.torrents[file_name].file.set_chunk(chunk_id, chunk_data)
        self.torrents[file_name].update()
        _print(self, "has pulled: " + chunk_data + " for file: " + file_name)


class PushPullPeer(PushPeer, PullPeer):
    def __init__(self):
        super(PushPullPeer, self).__init__()

    def active_thread(self):
        super(PushPullPeer, self).active_thread()


if __name__ == "__main__":
    if not found:
        print "Missing package bitarray https://pypi.python.org/pypi/bitarray"

    # root = Gui()

    set_context()
    host = create_host()

    tracker = host.spawn("tracker1", Tracker)
    tracker.run()

    # tracker2 = host.spawn("tracker2", Tracker)
    # tracker2.run()

    t1 = Torrent("torrent1.json")

    t2 = Torrent("torrent1.json")
    # root.add_torrent(t1)
    # t2 = Torrent("torrent2.json")

    c1 = host.spawn("peer1", PushPullPeer)
    c1.add_torrent(t1)
    # c1.add_torrent(t2)

    c2 = host.spawn("peer2", PushPullPeer)
    c2.add_torrent(t2)
    # c2.add_torrent(t2)

    c1.run("Descargas")
    c2.run()

    # sleep(15)
    # host.stop_actor("peer2")

    # root.mainloop()
    serve_forever()
