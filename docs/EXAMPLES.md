## Examples

#### random walk

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
