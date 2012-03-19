
# About *dman*

_dman_ is the download manager interface daemon. _dman_
is not a download manager, although it sometimes behaves like one,
dman is a portable interface to call other download managers.

## What? Why?

There are lots of download managers out there, and I have no intention of
implementing yet another download (manager/accelerator).
What annoys me is that I lack a portable way to programmatically call
my download manager, i.e.:

* When I'm on Linux I use KGet
* On OpenBSD wget/aria2/Fatrat
* On Windows, only god knows what

Some of those are full fledged download managers, other are lack queueing
features/single instance.

Basically _dman_ is wrapper around whatever download managers you have in
your system. If for example KGet is available then it simply forwards to
KGet, otherwise call applications like wget but manages download queues
internally.

It is a meta-Download-Manager :D


## How do I use it?

Just call the dman command:

    $ dman http://...

## What applications do you support?

At this point only Wget is supported


# dman IPC

dman has 2 IPC mechanisms you can use to interact with the
download manager: json-rpc and the urldropper socket.

Both operate as a UNIX socket, and accept messages as netstring
frames.

## urldropper

The urldropper interface is the simplest interface to start a download.
It simply accepts URLs for download.
It does not return error codes, or offer any other functionality.

This interface simply consists of writing URLs into a socket.
The urls are encoded as netstrings.
Any number of urls can be written in the same connection.

So, a simple python example could be:

    import socket
    from dman import client, netstring
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(client.urldrop_path())
    sock.send(netstring.encode(url))
    sock.close()



## Json RPC

TBD ...

