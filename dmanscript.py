#!/usr/bin/env python
"""The dman scrip

1. When running with no arguments this will start the dman server
2. When running with arguments this will drop the arguments into the
   url drop

"""

from dman import server
from dman import client
import sys, os


def main():
    """The main() function
    
    In a nutshell:
    1. If the urldropper socket exists run the client
    2. If it does not run the server
    3. In both cases all arguments are treated as URLs to download
    """

    if not os.path.exists(server.urldrop_path()):
        # start dman
        print("dman is not running, starting daemon")
        urls = sys.argv[1:]
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
                    print "Daemon PID %d" % pid 
                    sys.exit(0) 
            except OSError, e: 
                print("fork failed: ", e)
                sys.exit(1)
            server.server_main(urls)
    elif len(sys.argv) > 1:
        client.simple_client_main()

if __name__ == '__main__':
    main()

