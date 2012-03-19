"""
dman - client components
"""
import socket
from server import urldrop_path
import netstring
import sys

def simple_client_main():
    """The is the main() function for a simple
    urldrop ipc client.
    """
    cmd = ' '.join(sys.argv[1:])
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(urldrop_path())

    for url in sys.argv[1:]:
        sock.send(netstring.encode(url))
    sock.close()

