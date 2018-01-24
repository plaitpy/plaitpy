from __future__ import print_function
from __future__ import unicode_literals

import sys
import time
import random
import re
import math
import os

from . import debug

from os import environ as ENV

LAMBDA_TYPE = type(lambda w: w)
TRACEBACK=True

class DotWrapper(dict):
    def __getattr__(self, attr):
        if attr in self:
            return self[attr]

        if not attr in self:
            debug.debug("MISSING ATTR", attr)

    def __setattr__(self, attr, val):
        self[attr] = val


def exit():
    sys.exit(1)

def exit_error(e=None):
    import traceback
    if e:
        debug.debug("Error:", e)

    if TRACEBACK:
        traceback.print_exc()
    sys.exit(1)

# from comment on http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/
def memoize(f):
    """ Memoization decorator for functions taking one or more arguments. """
    class memodict(dict):
        def __init__(self, f):
            self.f = f
        def __call__(self, *args):
            return self[args]
        def __missing__(self, key):
            ret = self[key] = self.f(*key)
            return ret
    return memodict(f)

@memoize
def make_func(expr, name):
    func = compile_lambda(str(expr), name, 'exec')
    return lambda: eval(func, GLOBALS, LOCALS)

@memoize
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

class GlobalAssigner(dict):
    def __str__(self):
        return "GLOBAL ASSIGNER %s" % (id(self))

    def __setitem__(self, attr, val):
        GLOBALS[attr] = val
        RAND_GLOBALS[attr] = val

    def __setattr__(self, attr, val):
        GLOBALS[attr] = val
        RAND_GLOBALS[attr] = val

    def __getitem__(self, attr):
        if attr in RAND_GLOBALS:
            return RAND_GLOBALS[attr]

    def __getattr__(self, attr):
        if attr in RAND_GLOBALS:
            return RAND_GLOBALS[attr]

def setup_globals():
    if "__plaitpy__" in GLOBALS:
        return

    ga = GlobalAssigner()
    ga["__plaitpy__"] = True
    ga.time = time
    ga.random = random
    ga.re = re
    ga.GLOBALS = ga
    ga.globals = ga

    from . import tween
    ga.tween = tween

    for field in dir(math):
        ga[field] = getattr(math, field)

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
