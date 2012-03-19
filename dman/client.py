# coding: utf-8
"""
dman - client components
"""
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import socket
from .server import urldrop_path
from .netstring import encode as netstring_encode
import sys

def dman_send_url(urls):
    """Send URLs to the dman urldrop
    
    This method accepts a single argument, either a url string
    or a list of urls"""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(urldrop_path())

    if isinstance(urls, list):
        for url in urls:
            sock.send(netstring_encode(url))
    else:
        sock.send(netstring_encode(url))
    sock.close()

def main():
    """The is the main() function for a simple
    urldrop ipc client.

    All program arguments are treated as urls and send to
    the urldrop.
    """
    dman_send_url(sys.argv[1:])

