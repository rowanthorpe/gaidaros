#!/usr/bin/env python

from gaidaros import *
server = Gaidaros(handle_request = lambda x: "Hello World: you said \"{}\"\n".format(x.rstrip('\n')))
server.handle()
