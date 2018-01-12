## debugging

debug output can be sent to stderr by using the `--debug` flag or by setting
`DEBUG=1` as an environment variable.

adding `--exit-on-error` will cause plait.py to end early when errors occur
during field generation.

### static field is missing or misdefined

To see how the static fields are setup in a template, turn on debugging and
redirect stdout to /dev/null. The command output will show what the definition
for each static variable is.

### template returns None

If a template is not returning any results (f.e. [this
issue](https://github.com/plaitpy/plaitpy/issues/3), turn on debugging
to get more details. If that doesn't work, open an issue.

## misc

### using custom imports

Remember to add the `imports` field to your template with the module that is
being imported, like so:

    fields:
      foo:
        lambda: datetime.datetime()

    imports:
      - datetime

## still having trouble?

please open an issue!
