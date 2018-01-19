import perf
from plaitpy.fakerb import decode

iter_count=1000
def get_names():
    return [decode("#{name.name}") for x in range(iter_count)]


def run_bench():
    runner = perf.Runner()
    runner.timeit("get_names", "get_names()", "from __main__ import get_names",
                  inner_loops=iter_count)


if __name__ == "__main__":
    run_bench()

"""
okay@chalk:~/tonka/src/plait.py$ python tests/perftest.py
.....................
get_names: Mean +- std dev: 9.81 us +- 0.45 us
okay@chalk:~/tonka/src/plait.py$ pypy tests/perftest.py
.........
get_names: Mean +- std dev: 2.24 us +- 0.12 us

"""

