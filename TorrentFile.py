import hashlib
import json


class TorrentFile(object):
    def __init__(self, fp):
        self.fp = fp
        file = open(fp, "r")
        json_str = file.read()
        file.close()
        self.obj = json.loads(json_str)
        self.name = self.obj["File"]["Name"]
        self.size = self.obj["File"]["Size"]
        self.checksum = self.obj["File"]["Checksum"]
        self.downloaded = 0

    def get_chunk(self, chunk_index):
        file = open(self.fp, "r")
        file.seek(chunk_index)
        chunk = file.read(1)
        file.close()
        return chunk

    def get_json(self, field=""):
        if field == "":
            return self.obj
        return self.obj[field]

    def read_all(self):
        with open(self.fp, "r") as file:
            data = file.read().replace('\n', '')
            file.close()
        return data

    def validate_checksum(self):
        validator = hashlib.sha512()
        validator.update(self.read_all())
        return True if self.checksum == validator.digest() else False
