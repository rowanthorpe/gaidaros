#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gaidaros import Gaidaros

# ...handles Unix and MS EOLs

server = Gaidaros(handle_request = lambda x: ("Hello World: you said \"{}\"\r\n".format(x.rstrip('\r\n')), False)
server.handle()
