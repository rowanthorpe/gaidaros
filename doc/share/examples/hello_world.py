#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
from gaidaros import Gaidaros

server = Gaidaros(handle_request = lambda x: "Hello World: you said \"{}\"\r\n".format(x.rstrip('\n').rstrip('\r')).encode('utf8'))
server.handle()
