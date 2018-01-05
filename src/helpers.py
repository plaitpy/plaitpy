from __future__ import print_function
from __future__ import unicode_literals

import sys
import time
import random
import re
import math
import os

from . import tween

from os import environ as ENV

DEBUG="DEBUG" in ENV
LAMBDA_TYPE = type(lambda w: w)
VERBOSE=False
TRACEBACK=True

def debug(*args):
    if DEBUG:
        print(" ".join(map(str, args)), file=sys.stderr)

def verbose(*args):
    if VERBOSE:
        print(" ".join(map(str, args)), file=sys.stderr)

def exit():
    sys.exit(1)

def exit_error(e=None):
    import traceback
    if e:
        debug("Error:", e)

    if TRACEBACK:
        traceback.print_exc()
    sys.exit(1)


def make_func(expr, name):
    func = compile_lambda(str(expr), name, 'exec')
    return lambda: eval(func, GLOBALS, LOCALS)

def make_lambda(expr, name):
    func = compile_lambda(str(expr), name)
    return lambda: eval(func, GLOBALS, LOCALS)

def compile_lambda(expr, name, mode='eval'):
    func = compile(expr, name, mode)
    return func

class ObjWrapper(dict):
    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
        return None

    def __setattr__(self, attr, val):
        self[attr] = val



GLOBALS = ObjWrapper({})
RAND_GLOBALS = ObjWrapper({})
LOCALS = ObjWrapper()


def setup_globals():
    if "__plaitpy__" in GLOBALS:
        return

    g = globals()

    GLOBALS.time = time
    GLOBALS.random = random
    GLOBALS.tween = tween
    GLOBALS.re = re
    GLOBALS["__plaitpy__"] = True

    for field in dir(math):
        GLOBALS[field] = getattr(math, field)
        RAND_GLOBALS[field] = getattr(math, field)

    for field in dir(random):
        RAND_GLOBALS[field] = getattr(random, field)

THIS_STACK = []
def push_this_record(this, prev):
    THIS_STACK.append((GLOBALS.this, GLOBALS.prev))

    # setup our globals
    GLOBALS.this = this
    GLOBALS.prev = prev
    RAND_GLOBALS.this = this
    RAND_GLOBALS.prev = prev

def pop_this_record():
    this, prev = THIS_STACK.pop()
    GLOBALS.this = this
    GLOBALS.prev = prev
    RAND_GLOBALS.this = this
    RAND_GLOBALS.prev = prev

PATHS = {}
def add_path(*paths):
    p = os.path.join(*paths)
    path = os.path.realpath(p)
    if not path in PATHS:
        PATHS[path] = path

def add_template_path(*paths):
    paths = list(paths)
    add_path(*paths)
    if paths[-1] != "templates":
        paths.append("templates")
        add_path(*paths)

def clean_json(pr):
    del_keys = []
    for key in pr:
        if key[0] == "_":
            del_keys.append(key)
        else:
            val = pr[key]
            if issubclass(type(val), dict):
                clean_json(val)

    for key in del_keys:
        del pr[key]

add_path(__file__, "..")
add_path(__file__, "..", "..")
# we try to read the file from current path, then
# we try to read from ROOT path
def readfile(filename, mode="r"):
    if os.path.exists(filename):
        return open(filename, mode)


    for path in PATHS:
        fname = os.path.join(path, filename)
        if os.path.exists(fname):
            return open(fname, mode)

    raise Exception("No such file: %s in: %s" % (filename, PATHS.keys()))
