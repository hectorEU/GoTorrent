import hashlib
import json
import mmap
import os
import random

from bitarray import bitarray


class TorrentFile(object):
    def __init__(self, json_file):
        self.json_path = json_file  # JSON file at the same execution director
        json_str = self.read(json_file)  # Read raw text

        self.obj = json.loads(json_str)  # Parse text to a JSON object
        # Collect info fields
        self.name = self.obj["File"]["Name"]
        self.download_path = self.obj["File"]["Name"]
        self.size = int(self.obj["File"]["Size"])
        self.checksum = self.obj["File"]["Checksum"]
        self.chunk_map = bitarray(int(self.size))  # Each file byte mapped to 1 bit
        self.downloaded = 0
        self.completed = False

        self.index_size = self.size - 1  # Avoid off-by-one error

    # Peer instance call for full initialization
    # Parameters: folder -> download directory
    def initial_status(self, folder):
        self.download_path = os.path.join(folder, self.download_path)  # Updates download file path

        if os.path.exists(self.download_path) and self.validate_checksum():  # File integrity check
            self.downloaded = self.size  # Set downloaded chunks to number of total chunks (size)
            self.chunk_map.setall(True)  # Fill bitmap with 1
            self.completed = True
        else:
            self.create_file()  # Create file if download path does not exist
            self.downloaded = 0
            self.chunk_map.setall(False)  # Reset bitmap, start or restart download from scratch
            self.completed = False

    # Choose a random chunk_id
    def get_random_chunk_id(self):
        return random.randint(0, self.index_size)

    # Returns the value of a valid chunk_data, else False
    def get_chunk(self, chunk_id):
        if 0 <= chunk_id <= self.index_size and self.chunk_map[chunk_id]:
            chunk_data = self.read(self.download_path, byte=chunk_id)
            return chunk_data
        else:
            return False

    # Retrieves either the json object or one of its main fields
    def get_json(self, field=""):
        if field == "":
            return self.obj
        return self.obj[field]

    # Saves a chunk in the file via a byte index, without spoiling other chunks nor overwriting them
    def set_chunk(self, chunk_id, chunk_data):
        try:
            file = os.open(self.download_path, os.O_RDWR)
            try:
                m = mmap.mmap(file, 0)  # View file as table of bytes
                m[chunk_id] = chunk_data  # Assign chunk_data to the specified position
                if not self.chunk_map[chunk_id]:
                    self.downloaded += 1  # Increase downloading account for new chunks
                self.chunk_map[chunk_id] = True  # Keeps record of this new chunk
                # We could carry out download completion check here, but it would delay the process for large files.
                # Moreover we allow replacement of chunks in case of fake incoming data, until the file has passed
                # checksum verification
            except (IOError, OSError):
                print "Error: Setting chunk: " + chunk_data + "index: " + str(chunk_id)
                return False
            finally:
                os.close(file)
        except (IOError, OSError):
            print "Error: Opening file: " + self.download_path + " for setting chunk: " + chunk_data
            return False
        return True

    # Create new empty file
    def create_file(self):
        with open(self.download_path, "w+") as file:
            file.seek(self.index_size)
            file.write("0")  # Write only the last char to make file of specific size

    # Compare current file checksum to the json declared checksum
    def validate_checksum(self):
        validator = hashlib.sha512()
        validator.update(self.read(self.download_path))
        return True if validator.hexdigest() == self.checksum else False

    # Updates instance file checksum overriding json
    def calculate_checksum(self):
        generator = hashlib.sha512()
        generator.update(self.read(self.download_path))
        self.checksum = generator.hexdigest()

    # Read the whole file and return it as a raw string
    @staticmethod
    def read(file_name, byte=None):
        with open(file_name, "r") as file:  # Unicode (utf-8) encoding
            if byte is None:
                data = file.read()
            else:
                file.seek(byte)
                data = file.read(1)
            return data
