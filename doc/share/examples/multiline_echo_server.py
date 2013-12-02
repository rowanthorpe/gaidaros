#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gaidaros import Gaidaros

def multiline_split(x):
    _loc = x.find('\n\n') + 2
    if _loc - 2 < len(x):
        return (x[:_loc], x[_loc:])
    else:
        return (x, '')

server = Gaidaros(end_request = lambda x: '\n\n' in x, split_request = multiline_split)
server.serve()
