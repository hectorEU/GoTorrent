import random
from collections import defaultdict
from datetime import datetime, timedelta


class Tracker(object):
    _tell = ["announce", "update", "run"]
    _ask = ["get_peers"]

    def __init__(self, peers_offer=3, announce_timeout=12):
        self.index = defaultdict(list)              # Key: File name; Value: List of peer proxies
        self.last_announces = {}                    # Key: Peer url; Value: Timestamp
        self.peers_offer = peers_offer              # Max. random sample
        self.announce_timeout = announce_timeout    # Disconnected peer clean-up

    # Public actor methods *************************
    def announce(self, file_name, peer_ref):
        if peer_ref.actor.url not in self.last_announces.keys():
            self.index[file_name] += [peer_ref]     # First time announce

        self.last_announces[peer_ref.actor.url] = datetime.now()
        print "Announce received from " + peer_ref.actor.url    # Debug

    def get_peers(self, file_name):
        return (file_name, random.sample(self.index[file_name],     # Select a random sample of connected peers
                             self.peers_offer if self.peers_offer <= len(self.index[file_name]) else len(self.index[file_name])))

    # ***********************************************

    def update(self):
        # Remove inactive peers from self.last_announces
        self.last_announces = {peer: timestamp for peer, timestamp in self.last_announces.items() if
                               datetime.now() - timestamp <= timedelta(seconds=self.announce_timeout)}

        # Remove inactive peers from self.index
        for file_name, peers in self.index.items():
            for peer in peers:
                if peer.actor.url not in self.last_announces.keys():
                    self.index[file_name].remove(peer)
                    print "Unsuscribed: " + file_name + peer.actor.url  # Debug
                else:
                    print "Suscribed: " + file_name + peer.actor.url    # Debug

    def run(self):
        # Removes inactive peers from swarm
        self.loop1 = self.host.interval(self.announce_timeout, self.proxy, "update")
