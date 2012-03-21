#!/usr/bin/env python
"""The dman scrip

1. When running with no arguments this will start the dman server
2. When running with arguments this will drop the arguments into the
   url drop

"""

from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division
from dman import server
from dman import client
import os
import sys


def main():
    "The main() function"
    if os.getenv("DMAN_DEBUG"):
        if len(sys.argv) > 1:
            client.main()
        else:
            server.main()
    else:
        if server.start_daemon():
            # sleep a bit so the daemon can start
            import time
            time.sleep(2)
        client.main()

if __name__ == '__main__':
    main()

