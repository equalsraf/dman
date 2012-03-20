# coding: utf-8
"""
dman is a Meta-download manager

* for client functions check the *client* module
* the *server* module holds the server bits
* for netstring encoding/decoding check the *netstring* module
* the *plugins* modules holds all download implementations,
  if you are thinking about implementing support for other
  applications, you should start there

"""
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
from .plugins import new_download
import os

class DMan(object):
    """
    DMan the download manager interface daemon
    """
    
    def __init__(self, maxdownloads=2):
        self.pending = []
        self.downloading = []
        self.finished = []
        self.maxdownloads = maxdownloads

    @staticmethod
    def default_download_folder():
        "Returns a default download folder"
        path = os.path.join( os.path.expanduser("~"), 'Downloads' )

        try:
            os.mkdir(path)
        except OSError:
            pass
        return path

    def download(self, url, save_in=None):
        "Download a URL"       

        if not save_in:
            save_in = DMan.default_download_folder()

        #
        # dman has three queues (pending, downloading, finished)
        # - pending is a queue of tuples (url, save_folder)
        # - downloading is a queue of Download objects
        # - finished is a queue of download objects

        # Add download to the pending queue
        self.pending.append( (url, save_in) )

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
                d_url,d_save_in = self.pending.pop()
                download = new_download( d_url, d_save_in )
                if not download:
                    # Can't start the download - got back to pending
                    self.pending.append( (d_url,d_save) )
                    continue

                self.downloading.append(download)
                download.start()


