# testing fields functionality

import unittest
import sys
import os

# i hate the path dance
sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..")))
from src import template
from src import helpers

helpers.TRACEBACK = False
template.TEST_MODE = True
template.EXIT_ON_ERROR = True

from contextlib import contextmanager

@contextmanager
def stdout_redirector(stream):
    old_stdout = sys.stdout
    sys.stdout = stream
    try:
        yield
    finally:
        sys.stdout = old_stdout


class TestTemplateFields(unittest.TestCase):
    def assert_no_errors(self, t):
        self.assert_num_errors(t)

    def assert_num_errors(self, t, n=0):
        self.assertEqual(len(t.field_errors), n)


    def test_imports(self):
        import marshal
        t = template.Template("tests/templates/imports.yaml")
        r = t.gen_record()
        self.assertEqual(r.testfield, marshal)
        self.assert_no_errors(t)

    def test_mixins(self):
        t = template.Template("tests/templates/mixins.yaml")
        r = t.gen_record()
        self.assertEqual(r.foo, "bar")
        self.assertEqual(r.abc, "def")
        self.assert_no_errors(t)

    def test_defines(self):
        t = template.Template("tests/templates/define.yaml")
        r = t.gen_record()
        self.assertEqual(r.foo, "foobarbaz")
        self.assertEqual(r.bar, 510)
        self.assert_no_errors(t)

    # field types
    def test_mixin_overrides(self):
        t = template.Template("tests/templates/mixins_override.yaml")
        r = t.gen_record()
        self.assertEqual(r.foo, "baz")
        self.assertEqual(r.abc, "def")
        self.assert_no_errors(t)

    def test_lambda_fields(self):
        t = template.Template("tests/templates/lambdas.yaml")
        r = t.gen_record()
        self.assertEqual(r.foo, "foobarbaz")
        self.assertEqual(r.sum, 100)
        self.assert_no_errors(t)

    def test_csv_sampling(self):
        t = template.Template("tests/templates/csv_sampling.yaml")
        rs = t.gen_records(100)
        counts = { "foo" : 0, "bar" : 0, "baz" : 0 }
        for r in rs:
            counts[r.foo] += 1

        self.assertTrue(counts["foo"] / 2 > counts["baz"])
        self.assertTrue(counts["baz"] >= 1)
        self.assertEqual(counts["bar"], 0)

    def test_csv_resampling(self):
        t = template.Template("tests/templates/resample.yaml")
        r = t.gen_record()
        self.assertEqual(r.foo * 2, r.bar)
        self.assertEqual(r.foo * 3, r.baz)


    def test_csv_indexing_error(self):
        template.EXIT_ON_ERROR = False
        t = template.Template("tests/templates/csv_indexing_error.yaml")
        with self.assertRaises(SystemExit) as context:
            r = t.gen_record()


        t = template.Template("tests/templates/csv_no_indexing_error.yaml")
        r = t.gen_record()

        self.assertEqual(r.foo, "foobarbaz")
        # this template has a bad lookup in it,
        # so one error (and None returned)
        self.assert_num_errors(t, 1)

    def test_csv_indexing(self):
        t = template.Template("tests/templates/csv_indexing.yaml")
        r = t.gen_record()

        self.assertEqual(r.foo, "foobarbaz")
        # this template has a bad lookup in it,
        # so one error (and None returned)
        self.assert_no_errors(t)

    def test_switch_fields(self):
        t = template.Template("tests/templates/switch.yaml")
        r = t.gen_record()

        self.assertEqual(r.foo, "foo")
        self.assertEqual(r.bar, "bar")
        self.assertEqual(r.baz, None)

    def test_mixture_fields(self):
        t = template.Template("tests/templates/mixture.yaml")
        rs = t.gen_records(1000)

        counts = { 1 :0, 2: 0, 3: 0 }
        for r in rs:
            counts[r.foo] += 1

        self.assertTrue(abs(counts[1] - counts[2]) < 70)
        self.assertTrue(abs(counts[1] - counts[3]) > 10)
        self.assertTrue(abs(counts[2] - counts[3]) > 10)
        self.assertTrue(counts[3] > 500)



    def test_template_fields(self):
        t = template.Template("tests/templates/nesting.yaml")
        r = t.gen_record()
        self.assertEqual(r.nested.foo, "bar")
        self.assertEqual(r.nested.abc, "def")
        self.assert_no_errors(t)

    def test_template_bad_args(self):
        t = template.Template("tests/templates/bad_args.yaml")

        r = None
        with self.assertRaises(SystemExit) as context:
            r = t.gen_record()


    def test_template_args(self):
        t = template.Template("tests/templates/args.yaml")
        r = t.gen_record()
        self.assertEqual(r.nested.foo, "baz")
        self.assertEqual(r.nested.abc, "xyz")
        self.assert_no_errors(t)

    def test_faker_interpolation(self):
        t = template.Template("tests/templates/faker.yaml")
        self.assertEqual(t.field_definitions["foo"], "#{name.name}")

        r = t.gen_record()
        self.assertNotEqual(r.foo, "#{name.name}")
        self.assert_no_errors(t)

    def test_hidden_fields(self):
        t = template.Template("tests/templates/hidden.yaml")
        self.assertEqual(t.field_definitions["_foo"], "bar")
        self.assertEqual(t.field_definitions["vis"], "baz")
        r = t.gen_record()
        self.assertFalse("_foo" in r)
        self.assertTrue(len(r) == 1)
        self.assertEqual(r.vis, "baz")

    def test_random_fields(self):
        t = template.Template("tests/templates/random.yaml")

        rs = t.gen_records(1000)
        for r in rs:
            self.assertTrue(r.foo < 100)
            self.assertTrue(r.foo > 0)

        avg = sum([r.foo for r in rs]) / len(rs)
        self.assertTrue(abs(avg - 50) < 1)

    def test_prev_record(self):
        for _ in range(3):
            t = template.Template("tests/templates/init.yaml")

            r = t.gen_record()
            self.assertEqual(r.foo, 1)

            r = t.gen_record()
            self.assertEqual(r.foo, 2)


    # field operations
    def test_field_cast(self):
        t = template.Template("tests/templates/casts.yaml")
        r = t.gen_record()

        self.assertEqual(type(r.foo), str)
        self.assertEqual(type(r.bar), int)

    def test_field_init(self):
        # inadvertently tests "prev", as well
        t = template.Template("tests/templates/init.yaml")
        r = t.gen_record()

        self.assertEqual(r.foo, 1)

        r = t.gen_record()
        self.assertEqual(r.foo, 2)

    def test_field_finalize(self):
        t = template.Template("tests/templates/finalize.yaml")
        r = t.gen_record()

        self.assertEqual(r.foo, 100)

    def test_field_finalize_json(self):
        t = template.Template("tests/templates/finalize.json")
        r = t.gen_record()

        self.assertEqual(r.foo, 100)

    def test_field_include_json(self):
        t = template.Template("tests/templates/finalize_wrapper.json")
        r = t.gen_record()

        self.assertEqual(r.foo, 100)

    def test_print_csv(self):
        import json
        template.CSV = True
        template.JSON = False

        t = template.Template("tests/templates/print_test.yaml")
        r = t.gen_record()

        import io
        f = io.BytesIO()
        with stdout_redirector(f):
            t.print_records(1)

        self.assertEqual(f.getvalue(), "foo\r\n100\r\n")


    def test_print_json(self):
        import json
        template.JSON = True
        template.CSV = False
        t = template.Template("tests/templates/print_test.yaml")
        r = t.gen_record()

        import io
        f = io.BytesIO()
        with stdout_redirector(f):
            t.print_records(1)

        self.assertEqual(f.getvalue(), json.dumps({"foo" : 100}) + "\n")

    def test_custom_printer(self):
        t = template.Template("tests/templates/printer.yaml")
        r = t.gen_record()

        self.assertEqual(r.foo, 100)

        import io
        f = io.StringIO()
        with stdout_redirector(f):
            t.print_records(1)

        self.assertEqual(f.getvalue(), "foo: 100\n")


    def test_setup(self):
        t = template.Template("tests/templates/setup.yaml")
        r = t.gen_record()

        self.assertEqual(r.foo, 100)

    def test_effects_field(self):
        helpers.GLOBALS.effects_foo = None
        t = template.Template("tests/templates/effects.yaml")
        r = t.gen_record()

        self.assertEqual(helpers.GLOBALS.effects_foo, 100)


    # test field errors
    def test_exit_on_error(self):
        t = template.Template("tests/templates/bad_args.yaml")
        with self.assertRaises(SystemExit) as context:
            r = t.gen_record()

    def test_track_field_errors(self):
        pass


if __name__ == '__main__':
    unittest.main()

