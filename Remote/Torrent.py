import json
import os
from datetime import datetime

from TorrentFile import TorrentFile


class Torrent(object):
    def __init__(self, json_file):
        self.file = TorrentFile(json_file)
        self.peers = []
        self.trackers = []
        self.last_announce = datetime.now()
        self.last_discovery = datetime.now()
        self.stop = False

    # Check whether the download has finished
    def update(self):
        print str(self.file.downloaded) + " vs " + str(self.file.size)
        if self.file.downloaded == self.file.size and self.file.validate_checksum():
            self.file.completed = True
            print "Torrent: " + self.file.name + " has been completed!"

    # Update json file
    def refresh_metadata(self):
        self.file.size = os.path.getsize(self.file.download_path)
        self.file.calculate_checksum()

        self.file.obj["File"]["Size"] = self.file.size
        self.file.obj["File"]["Checksum"] = self.file.checksum
        self.file.obj["Trackers"] = self.trackers

        with open(self.file.json_path, "w+") as file:
            file.write(json.dumps(self.file.obj, indent=4))
