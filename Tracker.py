
from pyactor.context import set_context, create_host, sleep, shutdown

from collections import defaultdict

from datetime import datetime

class Tracker(object):
    _tell = ['announce']
    _ask = ['get_peers']

    info = defaultdict(defaultdict)

    def announce(self, torrent_hash, peer_ref):
        self.info[torrent_hash][peer_ref] = datetime.now()

    def get_peers(self, torrent_hash):
        return self.info[torrent_hash].keys()

    def swarm_control(self):
        for peers in self.info.values():
            for peer,time in peers.items():
                if(datetime.now()-time==0):
                    peers.pop(peer)