import random
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta

from pyactor.context import interval, set_context, create_host, serve_forever

from output import _print


class Tracker(object):
    _tell = ["announce", "update", "run"]
    _ask = ["get_peers"]

    def __init__(self, peers_offer=3, announce_timeout=12):
        self.index = defaultdict(list)  # Key: File name; Value: List of peer proxies
        self.last_announces = {}  # Key: Peer url; Value: Timestamp
        self.peers_offer = peers_offer  # Max. random sample
        self.announce_timeout = announce_timeout  # Disconnected peer clean-up

    # Public actor methods *************************
    def announce(self, file_name, peer_ref):
        if peer_ref not in self.index[file_name]:
            self.index[file_name].append(peer_ref)  # First time announce, add member to swarm

        self.last_announces[peer_ref.url] = datetime.now()  # Keep announce timestamp
        _print(self, "Subscribed: " + peer_ref.url + " in: " + file_name)

    def get_peers(self, file_name):
        if file_name not in self.index:  # Control invalid requests from members out of the swarm
            return file_name, None
        peers = self.index[file_name]
        return (file_name, random.sample(peers,  # Select a random sample of connected peers
                                         self.peers_offer if self.peers_offer <= len(peers) else len(peers)))

    # ***********************************************

    # Removes inactive peers from the swarms
    def update(self):
        # Remove inactive peers from self.last_announces
        self.last_announces = {peer: timestamp for peer, timestamp in self.last_announces.items() if
                               datetime.now() - timestamp <= timedelta(seconds=self.announce_timeout)}

        # Remove inactive peers from self.index
        for file_name, peers in self.index.items():
            for peer in peers:
                if peer.url not in self.last_announces:
                    self.index[file_name].remove(peer)
                    _print(self, "Unsubscribed: " + peer.url + " of: " + file_name)

    # Activates tracker
    def run(self):
        self.loop1 = interval(self.host, self.announce_timeout, self.proxy, "update")


if __name__ == "__main__":
    subprocess.call("./freeTrackerPorts.sh", shell=True)
    set_context()
    h1 = create_host("http://127.0.0.1:7969/")

    tracker = h1.spawn("tracker1", Tracker)
    tracker.run()

    serve_forever()
