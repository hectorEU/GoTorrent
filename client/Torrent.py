from datetime import datetime

from TorrentFile import TorrentFile


class Torrent(object):
    def __init__(self, fp):
        self.file = TorrentFile(fp)
        self.peers = []
        self.trackers = self.file.get_json("Trackers")
        self.announce_timeout = 10
        self.last_announce = datetime.now()
        self.discovery_period = 2
        self.last_discovery = datetime.now()
        self.stop = False
        self.completed = False

    def update(self):
        self.file.downloaded += 1
        if self.file.downloaded >= self.file.size:
            if self.file.validate_checksum():
                self.completed = True
