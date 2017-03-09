
from pyactor.context import set_context, create_host, sleep, shutdown

class Peer(object):
    _tell = ['push']
    _ask = []
    trackers = []
    peers = []
    chunk = []

    def __init__(self, delta=1):
        self.gossip_cycle = delta

    def active_thread(self):
        while True:
            sleep(self.gossip_cycle)
            peer = self.choose_random_peer(self.trackers)


    def push(self, chunk_id, chunk_data):
        self.chunk[chunk_id] = chunk_data


    def run(self, msg):
        while True:
            sleep(self.gossip_cycle)

    @staticmethod
    def choose_random_peer(trackers):
        for tracker in trackers:
            tracker.g