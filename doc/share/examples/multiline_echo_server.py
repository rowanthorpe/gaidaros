#!/usr/bin/env python

from gaidaros import Gaidaros
server = Gaidaros(end_request = lambda x: '\n\n' in x, split_request = lambda x: [x[:x.find('\n\n') + 1], x[x.find('\n\n') + 1:]])
server.serve()
