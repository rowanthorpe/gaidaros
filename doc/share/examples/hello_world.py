#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
from gaidaros import Gaidaros

# ...handles Unix or MS EOLs too

server = Gaidaros(handle_request = lambda x: ("Hello World: you said \"{}\"\r\n".format(x.rstrip('\r\n')), False)
server.handle()
