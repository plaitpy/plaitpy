# compatibility with faker.rb yaml file interpolation
import os
import yaml
import random
import re
import hashlib

from .debug import debug, verbose
from .helpers import LAMBDA_TYPE, readfile, exit_error

# a key looks like: base.field
# base maps to faker/lib/locales/en/base.yaml
# field maps into that file. fields can be defined
# recursively

LOCALE = "en"

from os import environ as ENV
if "LOCALE" in ENV:
    LOCALE = ENV["LOCALE"]

DEFAULT_LOCALE = "en"

OPENED_DATA = {}
CACHE_DIR = os.path.expanduser("~/.cache/plait.py/")
DIRTY_CACHE = False

SCRIPT_PATH = os.path.realpath(__file__)
FAKER_DIR = os.path.realpath(os.path.join(__file__, "..", "..", "vendor/faker/"))
LOCALE_DIR = "lib/locales/"

if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR)
    except:
        debug("Can't create cache for fakerb data in", CACHE_DIR)
        pass

FAKERB_PICKLE = "%s/fakerb.pickle" % CACHE_DIR

def setup_data(filename, doc, data):
    global DIRTY_CACHE
    OPENED_DATA[filename] = doc
    data = str(data).encode("utf-8")
    OPENED_DATA[filename]["md5"] = hashlib.md5(data).hexdigest()

    DIRTY_CACHE=True

def list_namespaces():
    files = os.listdir(os.path.join(FAKER_DIR, LOCALE_DIR, DEFAULT_LOCALE))

    for f in sorted(files):
        if f.find("yml") != -1:
            yield f.replace(".yml", "")

def parse_key(fullkey, basename=None):
    if not OPENED_CACHE:
        open_cache()

    if type(fullkey) != str:
        return fullkey

    tokens = fullkey.split()
    plan = []

    start_i = 0
    end_i = -1

    def make_fetcher(group, basename):
        return lambda: fetch(group, basename)

    while True:
        start_i = fullkey.find("#{", start_i);

        if start_i == -1:
            break
        else:
            if end_i+1 < start_i:
                plan.append(fullkey[end_i+1:start_i])

            end_i = fullkey.find("}", start_i)

            if end_i == -1:
                break

            group = fullkey[start_i+2:end_i]

            plan.append(make_fetcher(group, basename))


        start_i = end_i

    if start_i == -1 and end_i == 0:
        plan.append(fullkey)

    return plan


# decode turns a string into its matching value,
# but it is slow to continually reparse the same string
# so if we can come up with an execution plan (of lambdas),
# we are better off
PLANS={}
def decode(fullkey,basename=None):
    if type(fullkey) != str:
        return fullkey

    if fullkey.find("#{") == -1:
        return fullkey

    if fullkey in PLANS:
        plan = PLANS[fullkey]
    else:
        verbose("BUILDING FETCH PLAN FOR FAKER KEY", fullkey)
        plan = parse_key(fullkey, basename)
        PLANS[fullkey] = plan

    ret = [ x() if type(x) == LAMBDA_TYPE else x for x in plan]

    return "".join(ret)

try:
    import cPickle as pickle
except:
    import pickle as pickle

OPENED_CACHE=False
def open_cache():
    global OPENED_DATA, DIRTY_CACHE,OPENED_CACHE
    try:
        with open(FAKERB_PICKLE) as f:
            loaded = pickle.load(f)
        OPENED_DATA = loaded
    except Exception as e:
        debug(e)

    expired = []
    for file in OPENED_DATA:

        if not os.path.exists(file):
            expired.append(file)
            verbose("EXPIRING NON EXISTENT FILE", file)
            continue

        with readfile(file) as f:
            data = f.read()

        h = hashlib.md5(data)
        d = h.hexdigest()

        if not "md5" in OPENED_DATA[file] or d != OPENED_DATA[file]["md5"]:
            verbose("EXPIRING CACHED FILE", file)
            expired.append(file)
            continue

    for file in expired:
        del OPENED_DATA[file]


    DIRTY_CACHE = False
    OPENED_CACHE = True

    open_locale(LOCALE)


def save_cache():
    global DIRTY_CACHE
    if DIRTY_CACHE:
        with open(FAKERB_PICKLE, "wb") as f:
            pickle.dump(OPENED_DATA, f)

        DIRTY_CACHE = False


LOCALE_DATA = {}
def open_locale(locale):
    global LOCALE
    LOCALE = locale
    fname = "%s/%s/%s.yml" % (FAKER_DIR, LOCALE_DIR, locale)

    if not fname in OPENED_DATA:
        verbose("READING LOCALE FROM FILE")
        with readfile(fname) as f:
            data = f.read().encode("utf-8")


        d = hashlib.md5(data).hexdigest()

        doc = yaml.load(data)
        setup_data(fname, doc[LOCALE]["faker"], data)

    LOCALE_DATA.clear()
    LOCALE_DATA.update(OPENED_DATA[fname])


def fetch(key, fallback_base, lookup=False):
    tokens = key.split(".")
    if len(tokens) > 1:
        basename = tokens[0].lower()
        tokens.pop(0)
    else:
        if lookup:
            basename = key
            tokens.pop()
        else:
            basename = fallback_base

    fields = None
    if basename in LOCALE_DATA:
        fields = LOCALE_DATA[basename]
        if tokens[0] not in fields:
            fields = None

    if not fields:
        dirname = "%s/lib/locales/%s/" % (FAKER_DIR, DEFAULT_LOCALE)
        filename = "%s/%s.yml" % (dirname, basename)
        if not filename in OPENED_DATA:
            verbose("OPENING FAKER FILE", filename)

            with readfile(filename) as f:
                data = f.read()

            doc = yaml.load(data)
            setup_data(filename, doc, data)
        else:
            doc = OPENED_DATA[filename]
        fields = doc[DEFAULT_LOCALE]["faker"][basename]

    for field in tokens:
        fields = fields[field]

    if lookup:
        return fields

    if type(fields) == list:
        fields = random.choice(fields)


    # replace "#" character with random numbers
    if type(fields) == str:
        fields = decode(fields,basename)

        def replace_wildnum(match):
            return str(random.randint(0, 9))

        if fields.find("#") != -1:
            fields = re.sub("#", replace_wildnum, fields)



    return fields

if __name__ == "__main__":
    decode("name.last_name")
