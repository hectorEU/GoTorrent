import hashlib
import json
from bitarray import bitarray
import os, mmap


class TorrentFile(object):
    def __init__(self, json_file):
        self.json_file = json_file
        file = open(json_file, "r")
        json_str = file.read()
        file.close()
        self.obj = json.loads(json_str)
        self.name = os.path.basename(self.obj["File"]["Name"])
        self.path = self.obj["File"]["Name"]
        self.size = int(self.obj["File"]["Size"])
        self.checksum = self.obj["File"]["Checksum"]
        self.chunk_map = bitarray(int(self.size))
        self.downloaded = 0

    def initial_status(self, folder):
        self.path = os.path.join(folder, self.path)
        if self.validate_checksum():
            self.downloaded = self.size
            self.chunk_map.setall(True)
            return True
        else:
            file = open(self.path, "w+")
            file.write("\0"*(self.size-1))
            file.close()
            self.chunk_map.setall(False)
            return False

    def get_chunk(self, chunk_index):
        if self.chunk_map[chunk_index]:
            file = open(self.path, "r")
            file.seek(chunk_index)
            chunk = file.read(1)
            file.close()
            return chunk
        else:
            return False

    def set_chunk(self, chunk_index, chunk_data):
        file = os.open(self.path, os.O_RDWR)
        m = mmap.mmap(file, 0)
        m[chunk_index] = chunk_data
        self.chunk_map[chunk_index] = True
        os.close(file)

    def get_json(self, field=""):
        if field == "":
            return self.obj
        return self.obj[field]

    def validate_checksum(self):
        validator = hashlib.sha512()
        validator.update(self.read_all())
        return True if validator.hexdigest() == self.checksum else False

    def calculate_checksum(self):
        generator = hashlib.sha512()
        generator.update(self.read_all())
        self.checksum = generator.hexdigest()

    def read_all(self):
        if not os.path.exists(self.path):
            return ""
        with open(self.path, "r") as file:
            data = file.read().replace('\n', '')
            file.close()
        return data
