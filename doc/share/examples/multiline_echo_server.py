#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
from gaidaros import Gaidaros

def multiline_split(x):
    _req = x.decode('utf8')
    _loc = _req.find('\n\n') + 2
    return [_req[:_loc], _req[_loc:]]

server = Gaidaros(end_request = lambda x: '\n\n' in x.decode('utf8'), split_request = multiline_split
server.serve()
