## plait.py

plait.py is a program for generating fake data from composable yaml templates.

The idea behind plait.py is that it should be easy to model fake data that
has an interesting shape. Currently, many fake data generators model their data as a
collection of
[IID](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables)
variables; with plait.py we can stitch together those variables into a more
coherent model.

some example uses for plait.py are:

* generating mock application data in test environments
* validating the usefulness of statistical techniques
* creating synthetic datasets for performance tuning databases

### features

* declarative syntax
* use basic [faker.rb](https://github.com/stympy/faker) fields with #{} interpolators
* sample and join data from CSV files
* lambda expressions, switch and mixture fields
* nested and composable templates
* static variables and hidden fields

### an example template

    # a person generator
    define:
      min_age: 10
      minor_age: 13
      working_age: 18

    fields:
      age:
        random: gauss(25, 5)
        # minimum age is $min_age
        finalize: max($min_age, value)

      gender:
        mixture:
          - value: M
          - value: F

      name: "#{name.name}"
      job:
        value: "#{job.title}"
        onlyif: this.age > $working_age

      address:
        template: address/usa.yaml
      phone: # add a phone if the person is older than the minor age
        template: device/phone.yaml
        onlyif: this.age > ${minor_age}

      # we model our height as a gaussian that varies based on
      # age and gender
      height:
        lambda: this._base_height * this._age_factor
      _base_height:
        switch:
          - onlyif: this.gender == "F"
            random: gauss(60, 5)
          - onlyif: this.gender == "M"
            random: gauss(70, 5)

      _age_factor:
        switch:
          - onlyif: this.age < 15
            lambda: 1 - (20 - (this.age + 5)) / 20
          - default:
            value: 1



### how its different

some specific examples of what plait.py can do:

* generate proportional populations using census data and CSVs
* create realistic zipcodes by state, city or region (also using CSVs)
* create a taxi trip dataset with a cost model based on geodistance
* add seasonal patterns (daily, weekly, etc) to data

## usage

### installation

    # install with python
    pip install plaitpy

    # or with pypy
    pypy-pip install plaitpy

### cloning the repo for development

    git clone https://github.com/plaitpy/plaitpy

    # get the fakerb repo
    git submodule init
    git submodule update

### generating records from command line

specify a template as a yaml file, then generate records from that yaml file.

    # a simple example (if cloning plait.py repo)
    python main.py templates/timestamp/uniform.yaml

    # if plait.py is installed via pip
    plait.py templates/timestamp/uniform.yaml

### generating records from API

    import plaitpy
    t = plaitpy.Template("templates/timestamp/uniform.yaml")
    print t.gen_record()
    print t.gen_records(10)

### looking up faker fields

plait.py also simplifies looking up faker fields:

    # list faker namespaces
    plait.py --list
    # lookup faker namespaces
    plait.py --lookup name

    # lookup faker keys
    # (-ll is short for --lookup)
    plait.py --ll name.suffix

## documentation

### yaml file commands

* see docs/FORMAT.md

### datasets

* see docs/EXAMPLES.md
* also see templates/ dir

### troubleshooting

* see docs/TROUBLESHOOTING.md


### Dependent Markov Processes

To simulate data that comes from many markov processes (a markov ecosystem),
see the [plaitpy-ipc](https://github.com/plaitpy/plaitpy-ipc) repository.

### future direction

If you have ideas on features to add, open an issue - Feedback is appreciated!

### License

[MIT](https://github.com/plaitpy/plaitpy/blob/master/LICENSE.txt)
