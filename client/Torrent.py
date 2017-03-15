import json
import os
from datetime import datetime

from client.TorrentFile import TorrentFile


class Torrent(object):
    def __init__(self, json_file):
        self.file = TorrentFile(json_file)
        self.peers = []
        self.trackers = []
        self.last_announce = datetime.now()
        self.last_discovery = datetime.now()
        self.stop = False
        self.completed = False

    def update(self, chunk_id):
        self.file.chunk_map[chunk_id] = True
        self.file.downloaded += 1
        if self.file.downloaded >= self.file.size:
            if self.file.validate_checksum():
                self.completed = True
                print "Completed!"

    def refresh_metadata(self):
        self.file.size = os.path.getsize(self.file.path)
        self.file.calculate_checksum()

        self.file.obj["File"]["Size"] = self.file.size
        self.file.obj["File"]["Checksum"] = self.file.checksum

        with open(self.file.json_file, "w+") as file:
            file.write(json.dumps(self.file.obj, indent=4))
            file.close()

