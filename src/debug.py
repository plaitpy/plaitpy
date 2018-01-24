from __future__ import print_function
from os import environ as ENV

import sys

DEBUG="DEBUG" in ENV
VERBOSE=False

def debug(*args):
    if DEBUG:
        print(" ".join(map(str, args)), file=sys.stderr)

def verbose(*args):
    if VERBOSE:
        print(" ".join(map(str, args)), file=sys.stderr)
