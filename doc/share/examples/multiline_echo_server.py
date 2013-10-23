#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals

from gaidaros import Gaidaros
server = Gaidaros(end_request = lambda x: '\n\n' in x, split_request = lambda x: [x[:x.find('\n\n') + 2], x[x.find('\n\n') + 2:]])
server.serve()
