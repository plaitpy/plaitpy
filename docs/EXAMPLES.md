## Examples

### random walk

    fields:
      value:
        lambda: prev.value + random.random() - 0.5
        initial: 0

      index:
        lambda: prev.index + 1
        initial: 0

      timestamp:
        lambda: time.time() + (this.index * 60)

    hide:
      - index

### nested templates

    # fields prefixed with _ are hidden from the output
    fields:
      _stock1:
        template: "walk/random_walk.yml"
      _stock2:
        template: "walk/random_walk.yml"
      _stock3:
        template: "walk/random_walk.yml"

      val1:
        lambda: this._stock1.value

      val2:
        lambda: this._stock2.value

      val3:
        lambda: this._stock3.value

### supplying args to child templates

    # an example of aligning the sub templates with a parent value
    # using yaml alias (&ts is making the alias, *alias refers to it)
    # NOTE: for lambdas in args:, "this" context will be the parent template
    fields:
      timestamp:
        template: "timestamp/uniform.yaml"

      stock1:
        &stock_obj
        template: "walk/random_walk.yaml"
        args:
          timestamp:
            lambda: this.timestamp

      stock2: *stock_obj
      stock3: *stock_obj

### using mixins and overrides

    mixin:
      - web/browser.yaml

    fields:
      geoip:
        template: address/nyc.yaml
        override:
          country: "United Stated"

### using switch fields (if statements)

    fields:
      hourofday:
        random: randint(0, 24)
      timeofday:
        switch:
          - onlyif: this.hourofday < 10
            value: "morning"
          - onlyif: this.hourofday > 20
            value: "night"
          - default:
            value: "day"

### using mixtures (probabilistic if statements)

    fields:
      hourofday:
        mixture:
          - random: gauss(8, 2)
          - random: gauss(12, 1)
            weight: 2 # twice as important
          - random: gauss(20, 2)
          - random: randint(0, 24)
            weight: 0.5 # not so important

### using CSV files

#### sampling from CSV with weight fields

    # if we have a CSV that is:
    # [useragent, population_count, browser_family, browser_major, browser_minor]
    # we can do the following, to get proportional sampling
    fields:
      useragent:
        csv: useragents.csv
        column: 1
        weight: 2 # the weight column

      # if two CSV fields are specified using the same file, their values will be from the same row in the CSV
      # in this example, browser_family will be from the same row that useragent comes from
      browser_family:
        csv: useragents.csv
        column: 3
        depends: useragent

#### joining to a CSV using indeces

    # if we have two CSV that are:
    # zipcode_pop.csv: [ zipcode, population ]
    # cities.csv: [ state, city, zip code ]
    # we can join them together:
    fields:
      zipcode:
        csv: zipcode_pop.csv
        column: 1
        weight: 2

      state:
        csv: cities.csv
        column: 1
        index: 3
        lookup: this.zipcode

      city:
        csv: cities.csv
        column: 2
        index: 3
        lookup: this.zipcode

### using custom imports

    fields:
      _geoip:
        lambda: geoip.geolite2.lookup(this.ip)

      ip:
        template: web/ip.yaml

      country:
        onlyif: this._geoip and this._geoip.country
        lambda: this._geoip.country

    imports:
      - geoip

    requirements:
      - python-geoip
      - python-geoip-geolite2

If a template fails an import, the **requirements** field will be printed to
the console, letting the caller know which packages might be required for the
template to work.


### using a custom printer

    define:
      N: int(100)
      K: int(100)

    fields:
      n:
        random: randint(0, ${N})
      k:
        random: randint(0, ${K})
      arr:
        random: |
          [ randint(0, this.k) for _ in range(this.n) ]


    printer: |
      print(this.n, this.k)
      print(*this.arr, sep=" ")

notice that the `|` character in yaml is a multi-line comment separated by
newlines. this is really useful for defining multi-line functions. if the `>`
character was used instead, the **printer:** would not work, because `>` is a
comment separated by spaces in YAML and the resulting string would be invalid
code.
