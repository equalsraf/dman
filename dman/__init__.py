
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

        # FIXME: Wget is hardcoded for now
        self.pending.append( new_download(url) )

        # Move pending downloads in
        count = min( len(self.pending), 
                self.maxdownloads - len(self.downloading))
        if count:
            for i in range(count):
                down = self.pending.pop()
                self.downloading.append(down)
                down.start()


