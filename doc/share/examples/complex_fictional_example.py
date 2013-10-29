#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
from gaidaros import Gaidaros

#NB: this is deliberately not functional, it just shows different syntax possibilities within the same file

server = Gaidaros(
    conf = './conffile.conf',             # Source a custom config
    host = 'ip6-localhost',               # Resolve IPv6 localhost by name
    port = 9000,                          # Custom port
    ip_version = 6,                       # Force IPv6 only
    backlog = 100,                        # Set socket backlog queue to custom value
    poll_timeout = 2,                     # Take longer to respond to signals
    recv_size = 4096,                     # Attempt to read bigger blocks from the socket
    handler_class = 'myclass',            # If a string, it is looked up and sourced
    handler_class_args = (db=db.sqlite, version=3),
                                          # Arguments to pass to the handler's __init__() for accessing an sqlite3 server
    handler_module = mymodule,            # This is an already sourced/defined object, to be accessed directly.
    handle_request = 'handle_request'     # This names the function by string, which is looked for as mymodule.handle_request (or just handle_request, if module unspecified)
    end_request = lambda x: '[separator]' in x,  # This defines a callable inline, which will be used directly
)
server.serve()
