## template.yml spec

the template.yml file specifies how to generate records, it has several top level keys:

* **mixins** - a list of templates to mixin to the current template
* **defines** or **static** - a list of static variable definitions
* **fields** - the list of fields in the records that this template generates
* **args** - a list of fields that can be passed in from above (useful for composing templates)

## mixin overview

the **mixin** variable is a list of templates to ["mix
in"](https://en.wikipedia.org/wiki/Mixin) to our current template.  a mixin
takes the whole child template and includes it into our current template's
context before evaluating the current template.  any fields or variables in the
current template will override the definitions from the mixin.

## define overview

the fields in **define** are static variables that get evaluated once when the
template is created. they can be lambda expressions or fixed values and can
be referenced using the `${var}` syntax.

example:

    # defines.yaml
    define:
      bar: 20 + ${foo}
      foo: 10
      baz: ${foo} ** ${bar}

use `DEBUG=1 plait.py defines.yaml --num 1` to see how the static variables
have resolved.

## fields overview


the fields specified in **fields** are fields generated for each record.  each
field can be of multiple types, including:

* **switch**: specifies that this field is a switch field (similar to if / else if clauses)
* **csv**: specifies that this field is generated via sampling from a CSV file
* **lambda**: specifies that this field is generated via custom lambda function
* **effect**: specifies that this field is an effect field with sideeffects
* **mixture**: specifies that this field is a mixture field (similar to a probabilistic if clause)
* **random**: specifies that this field should be generated from random module
* **template**: specifies that this field is generated from another template
* **value**: specifies that this field is a fixed value

### common parameters

all of the fields in the fields section support the following commands as well:

params:

  * cast: the type to cast this field to, "int", "float", "str", etc
  * initial: the initial value for this field (if it is self-referential)
  * finalize: a final lambda expression to be run on this field (a finalizer)
  * suppress: suppress errors from this field (if its known to throw any)
  * onlyif: only add this field if it matches the supplied expr

##  fields API

### csv

**csv** specifies that this field is generated via sampling from a CSV file

params:

  * csv: filename.csv that livesin data/LOCALE/
  * column: index of column to use for sampling
  * weight: \[optional\] index of column to use for representative sampling

if the same csv is specified multiple times, the row of the first field that
specified that CSV will be used. this is to make sure that consistent data is
generated from a CSV.

### lambda

**lambda**: specifies that this field is generated via custom lambda function

params:

  * lambda: a valid python expression. 'this' references the current sample, 'prev' references the previous record from this template

example:

    fields:
      hour:
        lambda: time.time() % 3600

### random

**random**: specifies that this field should be generated from a lambda expression
that uses functions from the random module. it is a shortcut to save typing

example:

    fields:
      speed:
        random: randint(1,10)
      distance:
        random: random()

### template

**template**: specifies that this field is generated from another template.

params:

  * template: filename.yml that lives in templates/
  * override: a list of fields to override with new values


### switch

*switch* fields are if / else if statements that are executed in order. if no matches
are found, then the **default** value is used.

params:

  * an array of fields with **case** clauses

example:

    fields:
      hourofday:
        random: randint(0, 24)
      timeofday:
        case:
          - onlyif: this.hourofday < 10
            value: "morning"
          - onlyif: this.hourofday > 20
            value: "night"
          - default:
            value: "day"


### mixture

**mixture**: specifies that this field is a probabilstic clause.

params:

  * an array of fields and their weighting functions

example:

    fields:
      hourofday:
        mixture:
            - random: gauss(8, 2)
            - random: gauss(12, 1)
              weight: 2 # twice as important
            - random: gauss(20, 2)
            - random: randint(0, 24)
              weight: 0.5 # not so important


## args overview

the **args** of a template are just like the **fields**, but they allow a parent
template to override their values. they are useful for creating templates
that act as "functions". an example:

consider this template we will call "sum.yaml"

    args:
      a: 1
      b: 2

    fields:
      sum:
        lambda: this.a + this.b

    hide:
      - a
      - b


another template can refer to the "sum.yaml" and supply their own args:

    fields:
      foo:
        template: sum.yaml
        args:
          a:
            lambda: this._bar
          b:
            lambda: this._baz

      _bar: 2
      _baz: 3
      sum:
        lambda: this.foo.sum


### args vs override

notice that **a** and **b** refer to **this** - the context of **this** for
args is the **parent template**.

you may have noticed that some template fields use **override** instead of
**args**.  an **override** let's us add new fields into the child template that
execute in the context of the **child template**, changing what **this** refers
to and adding new fields to the child record.
