"""
dman - local server classes
"""
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import os, signal
from .netstring import NetStringReader
from twisted.internet import reactor, protocol
from . import DMan

# Server
def runtime_base_base():
    """Returns the path to the IPC socket
    if the path does not exist it is created"""
    base = os.environ['XDG_RUNTIME_DIR']
    folder = os.path.join(base, 'dman')
    try:
        os.mkdir(folder)
    except OSError:
        pass
    return folder

def ipc_path():
    "The path to the ipc socket"
    return os.path.join(runtime_base_base(), 'ipc')

def urldrop_path():
    "The path to the urldrop socket"
    return os.path.join(runtime_base_base(), 'urldrop')

def shutdownDaemon(sig, stack):
    "Stop the reactor"
    reactor.stop()

class UrlDropHandler(NetStringReader, protocol.Protocol):
    """urldrop handler
    
    The urldrop ipc setups a UNIX socket where urls
    can be writen into. Each url is written as a netstring"""
    def __init__(self, dman):
        NetStringReader.__init__(self)
        self.dman = dman
    def dataReceived(self, data):
        """Feed data into the netstring parser"""
        self.feed(data)

    def stringReceived(self, string):
        "Overrides the base class - pushes a url for download"
        self.dman.download(string)

class UrlDropFactory(protocol.Factory):
    "urldrop socket factory"
    protocol = UrlDropHandler

    def __init__(self, dman):
        self.dman = dman
    def buildProtocol(self, addr):
        return UrlDropHandler(self.dman)

def server_main(urls=[]):
    """main() function to execute the server
    
    Params:
    * urls: a list of urls to push into the download queue
    """

    if os.path.exists(urldrop_path()):
        print("The server is already running")
        return

    dman = DMan()
    for url in urls:
        dman.download(url)
    signal.signal(signal.SIGTERM, shutdownDaemon)
    signal.signal(signal.SIGINT, shutdownDaemon)
    reactor.listenUNIX( urldrop_path(), UrlDropFactory(dman) )

    reactor.run()
    print("Shutting down")
    try:
        os.unlink(ipc_path())
        os.unlink(urldrop_path())
    except OSError:
        pass




