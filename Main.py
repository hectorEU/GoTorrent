from pyactor.context import set_context, create_host, serve_forever

from client.Peer import PushPeer
from client.Torrent import Torrent

if __name__ == "__main__":
    set_context()
    host = create_host()
    c1 = host.spawn("peer1", PushPeer)
    t1 = Torrent("jsonfile.json")
    c1.add_torrent(t1)
    c1.run()
    serve_forever()
