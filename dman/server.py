# coding: utf-8
"""
dman - local server classes
"""
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
import os, signal
from .netstring import NetStringReader
from twisted.internet import reactor, protocol
import sys
import logging
from .plugins import new_download
import ConfigParser

# Server
def runtime_base_path():
    """Returns the base path to store runtime info
    if the path does not exist it is created

    If the XDG_RUNTIME_DIR is not available
    then $HOME/.dman/ is used"""

    base = os.getenv('XDG_RUNTIME_DIR')
    if base:
        folder = os.path.join(base, 'dman')
    else:
        base = os.path.expanduser("~")
        folder = os.path.join(base, '.dman')

    try:
        os.mkdir(folder)
    except OSError:
        pass
    return folder

def ipc_path():
    "The path to the ipc socket"
    return os.path.join(runtime_base_path(), 'ipc')

def urldrop_path():
    "The path to the urldrop socket"
    return os.path.join(runtime_base_path(), 'urldrop')

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
            except OSError, ex: 
                print("fork failed: ", ex)
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

class DMan(object):
    """
    DMan the download manager interface daemon
    """
    
    def __init__(self, maxdownloads=2):
        self.pending = []
        self.downloading = []
        self.finished = []
        self.maxdownloads = maxdownloads
        self.save_in = DMan.default_download_path()

        try:
            config = ConfigParser.ConfigParser()
            cfp = open(DMan.config_path())
            config.readfp( cfp, 'dman.cfg')
            self.save_in = os.path.expanduser(config.get('dman', 'save_in'))
        except IOError:
            logging.info('No config file was found in ' + DMan.config_path())

    @staticmethod
    def config_path():
        "Path to the config file"
        base = os.path.expanduser("~")
        return os.path.join(base, '.dman', 'dman.cfg')

    @staticmethod
    def default_download_path():
        "Returns a default download folder"
        path = os.path.join( os.path.expanduser("~"), 'Downloads' )

        try:
            os.mkdir(path)
        except OSError:
            pass
        return path

    def download(self, url, save_path=None):
        "Download a URL"       

        if not save_path:
            save_path = self.save_in

        logging.info("Adding %s to the download queue in %s" % (url, save_path))
        #
        # dman has three queues (pending, downloading, finished)
        # - pending is a queue of tuples (url, save_folder)
        # - downloading is a queue of Download objects
        # - finished is a queue of download objects

        # Add download to the pending queue
        self.pending.append( (url, save_path) )
        self.poke()

    def poke(self):
        """
        Poke dman to "do something", this function moves
        finished downloads into the finished queue and
        starts pending downloads
        """
        # Moved finished downloads out
        for download in self.downloading:
            if download.finished():
                self.downloading.remove(download)
                self.finished.append(download)

        # Move pending downloads in
        count = min( len(self.pending), 
                self.maxdownloads - len(self.downloading))
        if count:
            for i in range(count):
                d_url, d_save_in = self.pending.pop()
                download = new_download( self, d_url, d_save_in )
                if not download:
                    # Can't start the download - got back to pending
                    self.pending.append( (d_url, d_save_in) )
                    continue

                self.downloading.append(download)
                download.start()


def main():
    """main() function to execute the server
    
    Params:
    * urls: a list of urls to push into the download queue
    """

    if os.path.exists(urldrop_path()):
        print("The server is already running")
        return

    logging.basicConfig(filename=os.path.join(runtime_base_path(), 'dman.log'), 
                        level=logging.DEBUG)
    logging.info("Starting dman")
    dman = DMan()
    signal.signal(signal.SIGTERM, shutdownDaemon)
    signal.signal(signal.SIGINT, shutdownDaemon)
    reactor.listenUNIX( urldrop_path(), UrlDropFactory(dman) )

    reactor.run()
    logging.info("Shutting down")
    try:
        os.unlink(ipc_path())
        os.unlink(urldrop_path())
    except OSError:
        pass

