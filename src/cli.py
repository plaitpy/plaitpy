# this is the CLI entry point for plait.py

from __future__ import print_function

import argparse
import json
import sys
import os

from . import fakerb
from . import template
from . import helpers
from . import debug

def setup_args():
    parser = argparse.ArgumentParser(description='Generate fake datasets from yaml template files')
    parser.add_argument('template', metavar='template.yml', type=str, nargs="?",
                        help='template to generate data from')

    parser.add_argument('--dir', dest='dir', type=str, default=".",
                        help='parent dir for templates and data files')
    parser.add_argument( '--num', dest='num_records', type=int, default=10000,
                        help='number of records to generate')

    parser.add_argument('--csv', dest='csv', default=False, action="store_true",
                        help='encode records as CSV')
    parser.add_argument('--json', dest='json', default=True, action="store_true",
                        help='encode records as JSON')

    # look up data from faker.rb
    parser.add_argument('-l', '--list', dest='list', help='list faker namespaces', action="store_true")
    parser.add_argument('-ll',  '--lookup', dest='lookup', type=str, help='faker namespace to lookup', nargs='?')
    parser.add_argument('--debug', dest='debug', action="store_true", default=False,
                        help='Turn on debugging output for plait.py')
    parser.add_argument('--exit-on-error', dest='exit_error', action="store_true", default=False,
                        help='Exit loudly on any error')

    args = parser.parse_args()

    return args, parser


def main():
    args, parser = setup_args()

    if args.csv:
        template.CSV = True
        template.JSON = False

    elif args.json:
        template.JSON = True
        template.CSV = False

    if args.exit_error:
        args.debug = True
        template.EXIT_ON_ERROR = True

    if args.debug:
        debug.DEBUG = True



    if args.lookup:
        if args.lookup.find("#{") != -1:
            ff = fakerb.decode(args.lookup)
            print("Interpolation of %s" % args.lookup)
        elif args.lookup.find("{") != -1:
            ff = fakerb.decode(args.lookup.replace("{", "#{"), "")
            print("Interpolation of %s" % args.lookup)

        else:
            ff = fakerb.fetch(args.lookup, "", lookup=True)
            print("Contents of %s" % args.lookup)

        if hasattr(ff, "__iter__"):
            for f in ff:
                print(" ", f.encode("utf-8"))
        else:
            print(" ", ff)
        return

    if args.list:
        ff = list(fakerb.list_namespaces())

        remaining = 0
        if len(ff) > 100:
            remaining = len(ff) - 100
            ff = ff[:100]

        for f in ff:
            print(f)

        if remaining > 0:
            print("... and %s more" % (remaining))
        return

    if not args.template:
        print("%s: error: too few arguments!\n" % sys.argv[0])
        parser.print_help()
        return


    template_file = args.template
    helpers.add_template_path(args.dir)
    helpers.setup_globals()

    tmpl = template.Template(template_file)
    debug.debug("*** GENERATING %s RECORDS" % args.num_records)
    tmpl.print_records(args.num_records)
    fakerb.save_cache()
