from __future__ import print_function
from __future__ import unicode_literals

import csv
import json

import math
import random
import re
import sys
import time
import yaml
from os import environ as ENV

from . import debug
from . import fakerb
from . import toposort
from .helpers import *

JSON = False
CSV = False
CUSTOM_OUT=True
SKIP = False

DEBUG_FIELD_SETUP = False
DEBUG_GEN_TIMINGS = "TIMING" in ENV
PROFILE_EVERY=25 # profile every 25 records
TEST_MODE = False

DROP_BAD_RECORDS = False

DEBUG_FIELD_ERRORS = True

# for testing columns
EXIT_ON_ERROR="DEBUG" in ENV

STATIC_BRACE_CAPTURE = "\${(.*?)}"
STATIC_NOBRACE_CAPTURE = "\$(\w+)"

LANGUAGE = "en_US"

CSV_WRITER = None
def print_record(process, r, csv_writer=None):
    if CUSTOM_OUT and process.output_func:
        process.output_func(r)
    elif CSV and csv_writer:
        pr = {}
        for field in process.public_fields():
            pr[field] = r[field]
        csv_writer.writerow(pr)
    elif JSON:
        pr = {}
        for field in process.public_fields():
            if field not in r:
                continue

            if r[field] is not None and r[field] is not "":
                pr[field] = r[field]

        clean_json(pr)
        print(json.dumps(pr))
    else:
        raise Exception("UNDEFINED PRINT")

class RecordWrapper(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

        self.__profile = False
        self.__template = None

    def start_profile(self):
        self.__profile = True
    def stop_profile(self):
        self.__profile = False

    def set_template(self, template):
        self.__template = template
        self.__id = id(self.__template)

    def get_id(self):
        return self.__id

    def populate_field(self, field):
        if field in self:
            return

        push_this_record(self, self.__template.prev_record)

        # get our val for the current field
        val = self.__template.field_data[field]
        if self.__profile:
            if not field in self.__template.timings:
                self.__template.timings[field] = 0
            start = time.time()

        if type(val) == LAMBDA_TYPE:
            try:
                self[field] = val()
            except Exception as e:
                self.__template.error("ERROR POPULATING FIELD", field, "TEMPLATE IS", self.__template.name, "RECORD IS", self)
                exit_error()

        if self.__profile:
            end = time.time()
            self.__template.timings[field] += (end - start)

        pop_this_record()

    def __getattr__(self, attr):
        if not attr in self:
            self.populate_field(attr)

        if attr in self:
            return self[attr]

YAML_CACHE = {}
REGISTERED = {}
class Template(object):
    def __init__(self, template, overrides=None, hidden=None, depth=0, quiet=False):
        self.name = template
        setup_globals()

        self.field_data = {}
        self.field_errors = {}
        self.field_definitions = {}

        # fields in ignore_errors should have their errors not halt program
        self.ignore_errors = {}

        self.error_types = {}
        self.count_until_profile = -1
        if DEBUG_GEN_TIMINGS:
            self.count_until_profile = 0



        self.depth = depth
        self.pad = "  " * self.depth
        self.quiet = quiet

        self.templates = {}
        self.timings = {}
        self.csv_row = {}
        self.csv_dropped = {}
        self.csv_files = {}

        self.hidden = {}
        if hidden:
            self.hidden = dict(zip(hidden, hidden))

        self.total_dropped = 0

        self.num_records = 0
        self.mixins = []

        self.prev_record = RecordWrapper({})

        self.record = RecordWrapper({})
        self.record.set_template(self)
        self.record_invalid = False

        overrides = overrides or {}
        self.overrides = {}

        self.static = DotWrapper({})
        self.static_init = DotWrapper({})

        self.register_paths()

        self.output_func = None

        self.debug("*** LOADING TEMPLATE", template)
        for o in overrides:
            if o[0] == "$":
                self.static_init[o.lstrip("$")] = overrides[o]
                self.debug("ADDED OVERRIDE %s - %s" % (template, o))
            else:
                self.debug("ADDED OVERRIDE %s - %s" % (template, o))
                self.overrides[o] = overrides[o]


        self.setup_template(template)
        all_keys = {}
        for k in self.field_data:
            all_keys[k] = 1
        for k in self.overrides:
            all_keys[k] = 1
        self.field_list = all_keys.keys()


    def register_paths(self):
        if self.name in REGISTERED:
            return

        REGISTERED[self.name] = 1
        # setup any paths on the way to the template (for convenience)
        this_path = os.path.realpath(".")
        that_path = os.path.realpath(self.name)
        rel_path  = os.path.relpath(that_path, this_path)

        tokens = rel_path.split(os.path.sep)
        fullpath = "."
        for token in tokens[:-1]:
            fullpath = os.path.join(fullpath, token)
            debug.debug("ADDING PATH", fullpath)
            add_path(fullpath)



    def error(self, *args):
        if debug.DEBUG or not TEST_MODE:
            print("%s" % (" ".join(map(str, args))), file=sys.stderr)

    def debug(self, *args):
        if self.quiet:
            return

        if debug.DEBUG:
            print("%s%s" % (self.pad, " ".join(map(str, args))), file=sys.stderr)

    def build_template(self, name, data):
        if type(data) == dict:
            overrides = {}

            # TODO: fix this reaching in up. the data can come from
            # an mixin field or from a template field, so we need
            # to consolidate how they call build_template()
            nested_data = {}
            if "template" in data:
                tmpl = data["template"]
                if type(tmpl) == dict:
                    if name in tmpl:
                        nested_data = tmpl[name]


            hidden = []
            overrides = None
            for d in [nested_data, data]:
                if "override" in d:
                    overrides = d["override"]

                for key in ["hide", "exclude"]:
                    if key in d:
                        hidden = d[key]

            return Template("%s" % name, overrides=overrides, hidden=hidden, depth=self.depth+1, quiet=self.quiet)

        else:
            return Template("%s" % name, depth=self.depth+1, quiet=self.quiet)

    def setup_template(self, template):

        if template in YAML_CACHE:
            return self.setup_template_from_cache(template)

        if template.endswith(".json"):
            with readfile(template) as f:
                try:
                    data = yaml.safe_dump(json.load(f), default_flow_style=False)
                except Exception as e:
                    self.error("Couldn't parse template %s" % (template), e)
                    raise(e)

        elif template.endswith(".yaml") or template.endswith(".yml"):
            with readfile(template) as f:
                data = f.read()
        else:
            self.error("Unknown template type: %s" % template)
            exit_error()


        return self.setup_template_from_data(template, data)

    def setup_template_from_cache(self, template):
        doc = YAML_CACHE[template]
        return self.setup_template_from_yaml_doc(template, doc)


    def setup_template_from_data(self, template, data):
        doc = yaml.load(data)

        YAML_CACHE[template] = doc
        return self.setup_template_from_yaml_doc(template, doc)

    def setup_template_from_yaml_doc(self, template, doc):
        self.include = {}

        for choice in [ "include", "includes" ]:
            if choice in doc:
                include = doc[choice]
                for f in include:
                    self.include[f] = True


        for choice in ["exclude", "hidden", "hide"]:
            if choice in doc:
                exclude = doc[choice]
                for f in exclude:
                    self.hidden[f] = True

        pre_defined = {}
        for choice in ["$", "define", "static", "defines"]:
            if choice in doc:
                for field in doc[choice]:
                    field = field.lstrip("$")
                    # we skip overriden fields from above

                    if field in self.static_init:
                        pre_defined[field] = True
                        continue

                    self.static_init[field] = doc[choice].get(field)

        self.setup_statics()
        for o in self.static:
            if o in pre_defined:
                self.debug("DEF^  %s - $%s as %s" % (template, o, self.static[o]))

            else:
                self.debug("DEF.  %s - $%s as %s" % (template, o, self.static[o]))

        if "imports" in doc:
            for m in doc["imports"]:
                if type(m) == str:
                    d = {}
                    d[m] = m
                    m = d

                try:
                    for modname in m:
                        asname = m[modname]
                        mod = __import__(modname)

                        GLOBALS[asname] = mod
                        RAND_GLOBALS[asname] = mod
                        self.debug("IMPORTING", modname, "AS", asname)
                except ImportError as e:
                    self.debug("*** COULD NOT IMPORT MODULE %s" % m)
                    if "requirements" in doc:
                        self.debug("*** MAKE SURE TO INSTALL ALL REQUIREMENTS:", ", ".join(doc["requirements"]))

                    exit_error()


        for choice in [ "setup", "init" ]:
            if choice in doc:
                init_data = self.replace_statics(doc[choice])
                init_lambda = make_func(init_data, "<setup:%s>" % (self.name))
                init_lambda()


        for choice in [ "print", "printer", "format", "output" ]:
            if choice in doc:
                print_lambda = make_func(doc[choice], "<printer:%s>" % (self.name))
                def print_func(r):
                    push_this_record(r, None)
                    print_lambda()
                    pop_this_record()
                self.output_func = print_func
                debug.debug("ADDED CUSTOM PRINTER TO", self.name)

        for g in [ "mixin", "mixins"]:
            if g in doc:
                self.setup_mixins(template, doc[g])


        if "embed" in doc:
            raise Exception("Embeds are not supported")

        field_data = {}

        fields = doc.get("fields", {})
        self.args = doc.get("args", {})


        for field in self.args:
            field_data[field] = self.args.get(field, {})

        for field in fields:
            field_data[field] = fields.get(field, {})

        for field in self.overrides:
            field_data[field] = {}


        self.setup_fields(template, field_data)
        self.headers = list(self.public_fields())

    def setup_mixins(self, template, mixins):
        if type(mixins) == str:
            mixins = [ mixins ]

        for mixin in mixins:
            fieldname = "%s:mixin:%s" % (template, mixin)
            if type(mixins) == dict:
                data = mixins[mixin]
            else:
                data = {}

            data["template"] = mixin

            d = {}
            data["override"] = d
            for s in self.static_init:
                d["$%s" % s] = self.static_init[s]


            self.debug("*** MIXING", mixin, "INTO", self.name)
            ef = self.setup_template_field(fieldname, **data)
            template = ef.template

            # we pull the template's field_data and static data in,
            # but we have a problem because our statics were not properly
            # over-riding the sub-template statics
            self.field_data.update(template.field_data)

            self.debug("*** MIXED", template.name, "INTO", self.name)
            self.mixins.append((mixin, ef))

    # CSV field is specified like:
    # csv filename <field_id>
    def load_csv_file(self, filename):
        if filename in self.csv_files:
            return self.csv_files[filename]

        with readfile(filename, "r") as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)

            reader = csv.reader(csvfile, dialect)
            csv_data = list(reader)

            self.csv_files[filename] = csv_data

        return csv_data

    def setup_csv_field(self, field, **kwargs):
        filename = kwargs.get("csv")
        field_dist = {}

        csv_data = self.load_csv_file(filename)

        field_type = "int"

        row_id = kwargs.get("index", [])
        if type(row_id) != list:
            row_id = [ row_id ]


        weight_id = None
        total_count = 0.0
        counts = {}
        weight_id = kwargs.get("weight", None)

        field_id = kwargs.get("column")
        try:
            field_id = int(field_id)
        except:
            pass


        csv_lookup = {}

        for row in csv_data:
            if type(field_id) == int:
                if len(row) <= field_id:
                    continue

                if weight_id is not None and len(row) <= weight_id:
                    continue

            elif type(field_id) == str:
                if field_id not in row:
                    continue
                if weight_id is not None and weight_id not in row:
                    continue

            if weight_id is not None:
                try:
                    count = int(row[weight_id].replace(',', ''))
                except:
                    count = 0

                if row[field_id] in counts:
                    counts[row[field_id]] += count
                else:
                    counts[row[field_id]] = count



            row_key = "\t".join([ row[f] for f in row_id])

            if not row_key in csv_lookup:
                csv_lookup[row_key] = [row]
            else:
                csv_lookup[row_key].append(row)


        for key in counts:
            total_count += counts[key]

        if weight_id is not None:
            for key in csv_lookup:
                p = []
                seen = {}
                this_csv_data = csv_lookup[key]
                key_count = 0
                for row in this_csv_data:
                    row_key = row[field_id]
                    if row_key in seen:
                        continue
                    seen[row_key] = 1

                    count = counts[row_key]
                    key_count += count
                    p.append(count)

                if key_count == 0:
                    key_count = 1.0
                    p = [ 1.0/len(p) for c in p]
                else:
                    p = [ c / float(key_count) for c in p]

                field_dist["%s:%s" % (field, key)] = p

        row_lambda = None
        if "lookup" in kwargs:
            row_lambda_str = kwargs.get('lookup')
            def row_lookup():
                ret = []
                for k in row_lambda_str:
                    kl = make_lambda(str(k), "<csv_lookup:%s:%s>" % (field, k))
                    ret.append(kl)

                return lambda: "\t".join(map(lambda r: str(r()), ret))

            if type(row_lambda_str) == list:
                row_lambda = row_lookup()
            else:
                row_lambda = make_lambda(str(kwargs.get('lookup')), "<csv_lookup: %s>" % field)
        # we rely on csv_row getting clear on every record run
        # if get_csv_field is called twice in a row, we re-use
        # the value from the first time (hence the 'i' and filename caching)
        drop_missing = True
        def get_csv_field():
            retry = False

            if row_lambda:
                key = row_lambda()
                if type(key) == list:
                    key = "\t".join(key)
            else:
                key = ""

            this_csv_data = csv_data

            if key != "":
                if key in csv_lookup:
                    this_csv_data = csv_lookup[key]
                elif DROP_BAD_RECORDS:
                    self.record_invalid = True
                elif drop_missing:
                    if not field in self.csv_dropped:
                        self.csv_dropped[field] = 0
                    self.csv_dropped[field] += 1

                    return ""

            if not filename in self.csv_row:
                field_key = "%s:%s" % (field, key)
                if field_key in field_dist:
                    ch = random.random()
                    i = 0
                    for p in field_dist[field_key]:
                        ch -= p
                        if ch <= 0:
                            break

                        i += 1
                        if i >= len(this_csv_data):
                            e = "Error generating %s" % field
                            self.track_error(field, e)
                            break

                else:
                    i = int(random.random() * len(this_csv_data))

                row = self.csv_row[filename] = this_csv_data[i]
            else:
                row = self.csv_row[filename]

            return row[field_id]


        return get_csv_field


    def setup_random_field(self, field, **kwargs):
        """
        random fields are like lambda expressions, except they have the all of
        the functions from the random module imported into the local namespace
        """
        import random

        randfunc = compile_lambda(kwargs.get("random"), '<random_field>')
        ll = locals()
        for f in dir(random):
            if f[0] != "_":
                ll[f] = getattr(random, f)


        def run_random():
            return eval(randfunc, RAND_GLOBALS, ll)

        return run_random

    def setup_fixed_field(self, field, **field_data):
        value = field_data.get('value')
        return lambda: value

    def setup_mixture_field(self, field, **field_data):
        cases = []
        default_func = None
        case_id = 0
        total_weight = 0.0
        for obj in field_data["mixture"]:
            val_func = self.setup_field("%s:mix:%s" % (field, case_id), obj)
            case_id += 1

            weight = 1
            if "weight" in obj:
                weight_data = obj["weight"]
                weight_name = "%s:weight" % field
                if type(weight_data) == dict:
                    weight_func = self.setup_field(weight_name, weight_data)
                    weight = weight_func()
                else:
                    weight_func = make_lambda(obj["weight"], "%s:weight%s" % (field, case_id))
                    weight = weight_func()

            total_weight += weight
            cases.append([weight, case_id, val_func])

        debug.debug("CASES ARE", cases)
        cases.sort(reverse=True)
        for c in cases:
            c[0] = c[0]/total_weight

        def pick_case():
            ch = random.random()
            i = 0
            for p,case_id,val_func in cases:
                ch -= p
                if ch <= 0:
                    break

                i += 1

            try:
                ret = val_func()
                return ret
            except Exception as e:
                self.track_error(field, e)


        return pick_case

    def setup_switch_field(self, field, **field_data):
        cases = []
        default_func = None
        case_id = 0
        for obj in field_data["switch"]:
            val_func = self.setup_field("%s:case:%s" % (field, case_id), obj)
            case_id += 1

            if "onlyif" in obj:
                cases.append(val_func)


            if "default" in obj:
                if default_func is not None:
                    raise Exception("Two defaults declared for field %s in %s", field, self.name)

                default_func = val_func


        def pick_case():
            for obj in cases:
                try:
                    ret = obj()
                    if ret:
                        return ret

                except Exception as e:
                    self.track_error(field, e)

            if default_func:
                return default_func()


        return pick_case


    def setup_effect_field(self, field, **kwargs):
        return make_func(str(kwargs.get('effect')), '<effect_field: %s>' % field)

    def setup_lambda_field(self, field, **kwargs):
        return make_lambda(str(kwargs.get('lambda')), '<lambda_field: %s>' % field)

    def setup_template_field(self, field, **kwargs):
        data = kwargs.get("template")
        if type(data) == str:
            data = { data: kwargs }

        data = self.replace_statics(data)

        args = kwargs.get("args") or []


        for tmpl in data:
            template = self.build_template(tmpl, kwargs)
            self.templates[template] = 1

            arg_funcs = []
            for arg in args:
                fieldname = "%s:arg:%s" % (field, arg)
                arg_funcs.append((arg, self.setup_field(fieldname, args[arg])))

            def gen_template():
                arg_data = {}
                for arg, func in arg_funcs:
                    arg_data[arg] = func()


                push_this_record(template.record, template.prev_record)

                ret = template.gen_record(arg_data, scrub_record=False)
                # copy children errors up
                self.record_invalid = template.record_invalid

                pop_this_record()
                return ret

            gen_template.template = template

            return gen_template


    def setup_fields(self, template, fields):
        # need to load the fields off disk
        for field in fields:
            field_data = self.replace_statics(fields[field])
            self.field_definitions[field] = field_data

            try:
                start = time.time()
                val_func = self.setup_field(field, field_data)
                self.field_data[field] = val_func
                duration = time.time() - start
                if DEBUG_FIELD_SETUP:
                    self.debug("TOOK %s TO SET UP %s" % (duration, field))
            except Exception as e:
                self.error("ERROR SETTING UP FIELD %s IN %s" % (field, template))
                exit_error()

    def setup_field(self, field, field_data):
        field_data = self.replace_statics(field_data)

        if field in self.overrides:
            if type(field_data) == dict:
                # TODO: verify this is the behavior we want:
                # only updating the keys inside the dict
                if type(self.overrides[field]) == dict:
                    field_data.update(self.overrides[field])
                else:
                    field_data = self.overrides[field]
            else:
                field_data = self.overrides[field]

        if type(field_data) == dict:
            # setup any type casts
            field_cast = None
            field_finalize = None
            if "cast" in field_data:
                field_cast = eval(field_data["cast"])

            if "finalize" in field_data:
                field_finalize = eval("lambda value: %s" % field_data["finalize"])

            if "initial" in field_data:
                init_data = field_data["initial"]
                init_name = "%s:initial" % field
                if type(init_data) == dict:
                    init_func = self.setup_field(init_name, init_data)
                    val = init_func()
                else:
                    val = field_data["initial"]

                self.record[field] = val
                self.debug("DEF. ", self.name, "-", init_name, "as %s(%s)" % (type(val).__name__, val))

            field_replace = None
            if "replace" in field_data:
                field_replace = field_data["replace"]

            # only if is a lambda that gets evaluated to see if we fill out this field
            onlyif = None
            if "onlyif" in field_data:
                onlyif = make_lambda(field_data["onlyif"], '<onlyif_expr>')

            deps = []
            if "depends" in field_data:
                deps = field_data["depends"]
                if type(deps) == str:
                    deps = [ deps ]

            if "suppress" in field_data:
                self.ignore_errors[field] = True

            val_func = None
            ## the heart of it all
            if "value" in field_data:
                val_func = self.setup_fixed_field(field, **field_data)
            elif "random" in field_data:
                val_func = self.setup_random_field(field, **field_data)
            elif "csv" in field_data:
                val_func = self.setup_csv_field(field, **field_data)
            elif "lambda" in field_data:
                val_func = self.setup_lambda_field(field, **field_data)
            elif "template" in field_data:
                val_func = self.setup_template_field(field, **field_data)
            elif "switch" in field_data:
                val_func = self.setup_switch_field(field, **field_data)
            elif "effect" in field_data:
                val_func = self.setup_effect_field(field, **field_data)
            elif "onlyif" in field_data:
                val_func = self.setup_fixed_field(field, value="true")
            elif "mixture" in field_data:
                val_func = self.setup_mixture_field(field, **field_data)
            else:
                self.error("UNRECOGNIZED FIELD", field, field_data)
                exit_error()


            def ret_func():
                if deps:
                    for sub in deps:
                        self.record.populate_field(sub)

                if onlyif and not onlyif():
                    return


                try:
                    val = val_func()
                    if field_cast:
                        val = field_cast(val)

                    if field_finalize:
                        val = field_finalize(val)
                        if field_cast:
                            val = field_cast(val)
                except Exception as e:
                    self.track_error(field, e)
                    if DROP_BAD_RECORDS:
                        self.record_invalid = True

                    return


                if field_replace and val:
                    for r in field_replace:
                        v = field_replace[r]
                        val = val.replace(r, v)

                if type(val) == str:
                    val = fakerb.decode(val)

                return val

        elif type(field_data) in [ str, float, int ]:
            rf = self.setup_fixed_field(field, value=field_data)
            ret_func = lambda: fakerb.decode(rf())
        else:
            self.error("UNKNOWN FIELD DATA", field_data, type(field_data))

        if ret_func:
            if field in self.hidden or field[0] == "_":
                self.debug("ADDED", self.name, "-", field)
            else:
                self.debug("ADDED", self.name, "+", field)

            return ret_func

        self.debug("UNRECOGNIZED FIELD", field, field_data)

    # since static fields can refer to each other, we have
    # to do a topological sort and then fill them out
    def setup_statics(self):
        dep_matrix = {}
        for s in self.static_init:
            deps = []
            val = self.static_init[s]
            def replace_field(m):
                deps.append(m.group(1))
                return m.group(1)

            val = str(val)
            replaced = re.sub(STATIC_BRACE_CAPTURE, replace_field, val)
            replaced = re.sub(STATIC_NOBRACE_CAPTURE, replace_field, replaced)
            dep_matrix[s] = set(deps)

        ret = toposort.toposort2(dep_matrix)

        if len(dep_matrix) > 0:
            for row in ret:
                for field in row:
                    static_init = self.replace_statics(self.static_init[field])
                    static_lambda = make_lambda(static_init, '<static_field::%s>' % field)
                    self.static[field] = static_lambda()

    def replace_statics(self, field_data):
        def replace_field(m):
            return str(self.static[m.group(1)])

        if type(field_data) == dict:
            for field in field_data:
                val = field_data[field]
                if type(val) == dict:
                    self.replace_statics(val)
                elif type(val) == str:
                    replaced = re.sub(STATIC_BRACE_CAPTURE, replace_field, val)
                    replaced = re.sub(STATIC_NOBRACE_CAPTURE, replace_field, replaced)
                    field_data[field] = replaced

        if type(field_data) == str:
            field_data = re.sub(STATIC_BRACE_CAPTURE, replace_field, field_data)
            field_data = re.sub(STATIC_NOBRACE_CAPTURE, replace_field, field_data)


        return field_data

    def public_fields(self):
        for field in self.list_fields():
            if field in self.hidden:
                continue
            if field[0] == "_":
                continue

            yield field


    def list_fields(self):
        if self.include:
            return self.include.keys()

        all_keys = {}
        for k in self.field_data:
            all_keys[k] = 1
        for k in self.overrides:
            all_keys[k] = 1

        self.field_list = all_keys.keys()
        return all_keys.keys()

    def track_error(self, field, e):
        if not field in self.field_errors:
            self.field_errors[field] = 1
        else:
            self.field_errors[field] += 1

        if DEBUG_FIELD_ERRORS:
            err_str = str(e)
            if not field in self.error_types:
                error_types = self.error_types[field] = {}
            else:
                error_types = self.error_types[field]

            if not err_str in error_types:
                error_types[err_str] = 1
            else:
                error_types[err_str] += 1

        if field not in self.ignore_errors or EXIT_ON_ERROR:
            exit_error()


    def print_timings(self):
        self.debug("*** PER COLUMN ESTIMATED TIMINGS FOR", self.name)
        field_timings = []

        total_timing = 0.0
        for field in self.field_data:
            if field in self.timings:
                field_timings.append((self.timings[field], field))
                total_timing += self.timings[field]

        field_timings.sort(reverse=True)
        for timing, field in field_timings:
            self.debug("%s: %.02f%%" % (field, timing/total_timing * 100))

        for embed in self.templates:
            embed.print_timings()

    def print_dropped(self):
        if self.total_dropped > 0 :
            self.debug("*** DROPPED %s/%s RECORDS FROM %s" % (self.total_dropped, self.num_records, self.name))

        if len(self.csv_dropped) or len(self.field_errors) or len(self.error_types):
            self.debug("*** TEMPLATE ERRORS", self.name)


            for field in self.field_errors:
                self.debug("FIELD: %s, FIELD ERRORS: %s/%s" % (field, self.field_errors[field], self.num_records))
                if field in self.error_types:
                    for type in self.error_types[field]:
                        self.debug("   ERROR COUNTS: %s, %s" % (self.error_types[field][type], type))

            for field in self.csv_dropped:
                self.debug("FIELD: %s, MISSING LOOKUPS: %s/%s" % (field, self.csv_dropped[field], self.num_records))

        for embed in self.templates:
            embed.print_dropped()


    def turnover_record(self):
        self.num_records += 1
        self.prev_record = self.record

        self.record = RecordWrapper()
        self.record.set_template(self)

        self.record_invalid = False

        self.csv_row.clear()


    def gen_record(self, args={}, scrub_record=True):
        self.turnover_record()

        for k in args:
            if not k in self.args:
                self.error("Error: %s is not an args: field in %s" % (k, self.name))
                exit_error()

            self.record[k] = args[k]


        profiling = False
        if self.count_until_profile == 0:
            self.count_until_profile = PROFILE_EVERY
            self.record.start_profile()
            profiling = True

        self.count_until_profile -= 1

        for field in self.field_list:
            self.record.populate_field(field)

        ret = RecordWrapper({})
        ret.set_template(self)


        for field in self.field_list:
            if not field in self.record:
                continue

            if field in self.hidden:
                continue

            ret[field] = self.record[field]

        if profiling:
            self.record.stop_profile()

        if self.record_invalid and DROP_BAD_RECORDS:
            self.total_dropped += 1

        if scrub_record:
            clean_json(ret)

        return ret

    def print_headers(self):
        self.csv_writer = None
        if CSV:
            self.csv_writer = csv.DictWriter(sys.stdout, fieldnames=self.headers)
            self.csv_writer.writeheader()


    def print_records(self, num_records):
        chunk_size = 1000
        self.print_headers()


        for _ in range(num_records // chunk_size):
            for r in self.gen_records(chunk_size, print_timing=False):
                print_record(self, r, csv_writer=self.csv_writer)

        if num_records % chunk_size != 0:
            for r in self.gen_records(num_records % chunk_size, print_timing=False):
                print_record(self, r, csv_writer=self.csv_writer)

        self.print_dropped()
        if DEBUG_GEN_TIMINGS:
            self.print_timings()

    def gen_records(self, num_records, print_timing=True):
        ret = []
        try:
            for i in range(num_records):
                r = self.gen_record()

                if self.record_invalid:
                    self.debug("INVALID RECORD SKIPPING", self.total_dropped)
                    continue

                if SKIP:
                    continue

                ret.append(r)

        except Exception as e:
            debug.debug(e)
        finally:
            if print_timing:
                self.print_dropped()
                if DEBUG_GEN_TIMINGS:
                    self.print_timings()

        return ret
