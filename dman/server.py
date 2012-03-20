# coding: utf-8
"""
dman - local server classes
"""
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import os, signal
from .netstring import NetStringReader
from twisted.internet import reactor, protocol
from . import DMan
import sys

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

def start_daemon():
    """Launch the dman daemon

    If the dman daemon is not running, launch it and return True
    If the daemon is already running return False

    """
    if not os.path.exists(urldrop_path()):
        # start dman
        pid = os.fork()
        if pid == 0:
            # child process
            os.setsid()
            sys.stdout = open("/dev/null", 'w')
            sys.stdin = open("/dev/null", 'r')

            try: 
                pid = os.fork() 
                if pid > 0:
                    # exit from second parent, print eventual PID before
                    sys.exit(0) 
            except OSError, e: 
                print("fork failed: ", e)
                sys.exit(1)

            # redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            si = file('/dev/null', 'r')
            so = file('/dev/null', 'a+')
            se = file('/dev/null', 'a+', 0)
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

            main()
            sys.exit(0) # Make sure we exit 
    else:
        return False
    return True



def main():
    """main() function to execute the server
    
    Params:
    * urls: a list of urls to push into the download queue
    """

    if os.path.exists(urldrop_path()):
        print("The server is already running")
        return

    print("Starting dman")
    dman = DMan()
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

