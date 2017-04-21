import abc
import imp
import os
import subprocess
from abc import ABCMeta
from random import choice

from pyactor.context import set_context, create_host, serve_forever, interval, sleep

from Torrent import Torrent
from output import _print, _error
from stats import retrieve, export_csv

try:
    imp.find_module('bitarray')
    found = True
except ImportError:
    found = False


class Peer(object):
    __metaclass__ = ABCMeta  # Abstract class
    _tell = ["push", "add_torrent", "remove_torrent", "run", "announce", "update_peers", "active_thread",
             "set_download_folder"]
    _ask = ["pull"]
    _ref = ["push", "pull"]

    def __init__(self, gossip_cycle=1, announce_timeout=10, discovery_period=2):
        self.gossip_cycle = gossip_cycle
        self.announce_timeout = announce_timeout
        self.discovery_period = discovery_period
        self.download_folder = ""
        self.torrents = {}  # Key: File name; Value: Torrent
        self.current_cycle = 0

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
                tracker.get_peers(file_name, future=True).add_callback(
                    "update_peers_callback")  # Performs a non-blocking call
                # Executes callback when Tracker returns

    def update_peers_callback(self, future):
        file_name = future.result()[0]
        peers = future.result()[1]
        if peers is None:
            return

        if self.proxy in peers:
            peers.remove(self.proxy)

        self.torrents[file_name].peers += peers  # Sum up peers from all trackers
        self.torrents[file_name].peers = list(set(self.torrents[file_name].peers))  # Unique list

        _print(self, "knows these peers: " + str(
            map(lambda proxy: proxy.actor.id, self.torrents[file_name].peers)) + " for file: " + file_name)

    # ***********************************************************

    # Activate peer
    def run(self):
        self.loop1 = interval(self.host, self.announce_timeout, self.proxy, "announce")
        self.loop2 = interval(self.host, self.discovery_period, self.proxy, "update_peers")
        self.loop3 = interval(self.host, self.gossip_cycle, self.proxy, "active_thread")

    def add_torrent(self, torrent):
        if torrent.file.name in self.torrents:
            # If torrent already exists, add trackers
            self.torrents[torrent.file.name].trackers += torrent.trackers
            # Remove duplicated trackers
            self.torrents[torrent.file.name].trackers = list(set(self.torrents[torrent.file.name].trackers))
        else:
            torrent.file.download_path = os.path.join(self.download_folder, torrent.file.name)
            torrent.file.initial_status()
            torrent.trackers = [self.host.lookup_url(tracker, "Tracker", "Tracker") for tracker in
                                torrent.file.get_json("Trackers")]
            self.torrents[torrent.file.name] = torrent

    def remove_torrent(self, torrent):
        self.torrents.pop(torrent)

    def set_download_folder(self, folder="./"):
        self.download_folder = folder  # Sets main download folder
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)

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
        if file_name in self.torrents:  # If this peer is in the swarm, "pull" should be called with correct file_name
            return file_name, chunk_id, self.torrents[file_name].file.get_chunk(chunk_id)
        return file_name, False

        # ***********************************************


class PushPeer(Peer):
    def __init__(self):
        super(PushPeer, self).__init__()

    def active_thread(self):
        self.current_cycle += 1
        for torrent in self.torrents.values():
            retrieve(self.current_cycle, torrent.file.name, torrent.file.downloaded * 100 / torrent.file.size)
            if torrent.file.downloaded == 0 or not torrent.peers:
                continue  # If peer has no content to disseminate from this torrent, try next one
            chunk_id = torrent.file.get_random_chunk_id()
            chunk_data = torrent.file.get_chunk(chunk_id)
            while not chunk_data:  # Loop until valid chunk found
                chunk_id = torrent.file.get_random_chunk_id()
                chunk_data = torrent.file.get_chunk(chunk_id)
            peer = choice(torrent.peers)
            peer.push(chunk_id, chunk_data, torrent.file.name)
            _print(self, "pushing ID:" + str(
                chunk_id) + " <" + chunk_data + "> to " + peer.actor.url + " from file: " + torrent.file.name)


class PullPeer(Peer):
    def __init__(self):
        super(PullPeer, self).__init__()

    def active_thread(self):
        self.current_cycle += 1
        for torrent in self.torrents.values():
            if torrent.file.completed or not torrent.peers:
                continue  # Torrent complete, ask for chunks of incomplete torrents
            peer = choice(torrent.peers)
            chunk_id = torrent.file.get_random_chunk_id()
            while torrent.file.chunk_map[chunk_id]:  # Loop until an empty chunk is found
                chunk_id = torrent.file.get_random_chunk_id()
            future = peer.pull(chunk_id, torrent.file.name, future=True)
            future.add_callback("pull_callback")
            _print(self,
                   "asking for ID:" + str(chunk_id) + " to " + peer.actor.url + " for file: " + torrent.file.name)

    def pull_callback(self, future):
        file_name = future.result()[0]
        chunk_id = future.result()[1]
        chunk_data = future.result()[2]
        if not chunk_data:
            return
        self.torrents[file_name].file.set_chunk(chunk_id, chunk_data)
        self.torrents[file_name].update()
        _print(self, "has pulled: ID:" + str(chunk_id) + " -> <" + chunk_data + "> for file: " + file_name)


class PushPullPeer(PushPeer, PullPeer):
    def __init__(self):
        super(PushPullPeer, self).__init__()

    def active_thread(self):
        for parent in self.__class__.__bases__:
            parent.active_thread(self)


if __name__ == "__main__":
    if not found:
        print "Missing package bitarray https://pypi.python.org/pypi/bitarray"

    subprocess.call("./freePeerPorts.sh", shell=True)

    set_context()

    h = create_host("http://192.168.1.101:6970")

    genesis = h.spawn("Cracker", PushPeer)
    genesis.set_download_folder("Genesis")
    genesis.add_torrent(Torrent("palabra.json"))
    genesis.add_torrent(Torrent("frase.json"))
    genesis.add_torrent(Torrent("parrafo.json"))
    genesis.run()

    type = [PushPeer, PullPeer, PushPullPeer]

    for i in range(0, 5):
        # sleep(randint(1, 5) / 10)
        # client = h.spawn("Peer" + str(i), choice(type))
        client = h.spawn("Peer" + str(i), PushPeer)
        client.set_download_folder("Peer" + str(i))
        client.add_torrent(Torrent("palabra.json"))
        client.add_torrent(Torrent("frase.json"))
        client.add_torrent(Torrent("parrafo.json"))
        client.run()

    sleep(60 * 10)

    export_csv()

    serve_forever()
