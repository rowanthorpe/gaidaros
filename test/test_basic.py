import os, sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname('__file__'), '..', 'lib')))
from gaidaros import gaidaros
sys.path.pop(0)
sys.exit(0)
