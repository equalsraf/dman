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

class DMan(object):
    """
    DMan the download manager interface daemon
    """
    
    def __init__(self, maxdownloads=2):
        self.pending = []
        self.downloading = []
        self.finished = []
        self.maxdownloads = maxdownloads

    def download(self, url):
        "Download a URL"       

        # Moved finished downloads out
        for down in self.downloading:
            if down.finished():
                self.downloading.remove(down)
                self.finished.append(down)

        self.pending.append( new_download(url) )

        # Move pending downloads in
        count = min( len(self.pending), 
                self.maxdownloads - len(self.downloading))
        if count:
            for i in range(count):
                down = self.pending.pop()
                self.downloading.append(down)
                down.start()

