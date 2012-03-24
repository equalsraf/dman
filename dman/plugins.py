# coding: utf-8
"""Download modules for dman

The plugins module holds the download
plugins for dman. Plugins allow dman to
delegate download tasks to other applications
"""

from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
from abc import abstractmethod
import os, logging
from twisted.internet import reactor, protocol
from twisted.internet.error import ProcessDone

DEBUG = os.getenv("DMAN_DEBUG", False)

def which(program):
    "The equivalent to UNIX's which"

    for path in os.environ["PATH"].split(os.pathsep):
        exe_file = os.path.join(path, program)

        if os.path.exists(exe_file) and os.access(exe_file, os.X_OK):
            return exe_file

    return None


class Download(object):
    "The base download class"
    def __init__(self, dman, url, save_in):
        self.dman = dman
        self.url = url
        self.save_in = save_in
    @abstractmethod
    def start(self):
        "Start the download"
        pass
    @abstractmethod
    def stop(self):
        "Stop the download"
        pass
    @abstractmethod
    def started(self):
        """Return True if the download has started
        
        This will be True even if the download has already
        @finished()"""
        pass
    @abstractmethod
    def finished(self):
        """Returns True if the download is finished.

        @see succeeded() to determined if it succeeded
        """
        pass
    @abstractmethod
    def succeeded(self):
        """Returns True if the download started and finished
        successfully.
        """
        pass
    @abstractmethod
    def error(self):
        """Returns an error message for current state
        
        You should check succeeded() before calling this"""
        pass
    @staticmethod
    @abstractmethod
    def plugin_available():
        """Return True if this download plugin class can
        be used
        """
        return False


class ProcessDownload(Download, protocol.ProcessProtocol):
    """
    This classe provides a simple download provider
    that calls a command via a pipe to execute the download.

    Subclasses MUST:
    * Override the download_cmd to build a proper command array

    they also SHOULD:
    * Redefine the _error_ dict that maps return codes into error messages
    * If needed override the succeeded method, it currently checks returncode == 0

    """

    errors = { 0: 'No errors occurred'}

    def __init__(self, dman, url, save_in):
        super(ProcessDownload, self).__init__( dman, url, save_in)
        self.__started = False
        self.process = None
        self.__finished = False
        self.__returncode = -1
    @abstractmethod
    def download_cmd(self):
        """Override this to define a download command

        Returns a command list suitable for subprocess.Popen
        for ex:
            ['wget', self.url]
        """
        pass
    def start(self):
        if self.__started:
            return False

        cmd = self.download_cmd()
        logging.debug( 'starting download: ' + ' '.join(cmd) )
        self.process = reactor.spawnProcess( self, cmd[0], cmd)
        self.__started = True
        return True
    def stop(self):
        if self.__started:
            self.process.signalProcess('INT')
    def started(self):
        return self.__started
    def finished(self):
        return self.__finished
    def succeeded(self):
        return self.__returncode == 0
    def error(self):
        return self.errors.get(self.__returncode, 'Unknown error')
    def processEnded(self, status):
        """Twisted ProcessProtocol exit handler"""
        logging.debug('Download finished '+self.url)
        if isinstance(status.value, ProcessDone):
            self.__returncode = 0
        else:
            self.__returncode = status.value.exitCode
        self.__finished = True
        self.dman.poke()

class WGetDownload(ProcessDownload):
    """A download using the popular WGet"""
    # wget return codes
    errors = {
        0: 'No problems occured',
        1: 'An error has occured',
        2: 'Parse error',
        3: 'I/O error',
        4: 'Network failure',
        5: 'SSL failure',
        6: 'Authentication faillure',
        7: 'Protocol error',
        8: 'Server issued and error'
        }

    wget = which('wget')

    @staticmethod
    def plugin_available():
        if WGetDownload.wget:
            return True
        else:
            return False
    def download_cmd(self):
        "Downloads are just: wget URL"
        cmd = [self.wget, '-P', self.save_in, self.url]
        return cmd

class AriaDownload(ProcessDownload):
    """Download using aria2c"""
    errors = {
        0: 'No problems occured',
        1: 'Unknown error',
        2: 'Timed out',
        6: 'Network error',
        9: 'Not enough disk space',
        17: 'I/O error',
        }

    aria2c = which('aria2c')

    @staticmethod
    def plugin_available():
        if AriaDownload.aria2c:
            return True
        else:
            return False

    def download_cmd(self):
        "aria2c -d <save_in> <url>"
        cmd = [self.aria2c, '-d', self.save_in, self.url]
        return cmd

PLUGINS = [ AriaDownload, WGetDownload ]
AVAILABLE = [ p for p in PLUGINS if p.plugin_available() ]

def new_download(dman, url, save_in):
    "Returns a new Download object"

    if not AVAILABLE:
        return None
    return AVAILABLE[0](dman, url, save_in)

