from __future__ import print_function
from src import cli
from os import environ as ENV

PROFILE=False
if PROFILE:
    print("PROFILING")
    import cProfile
    cProfile.run("cli.main()", "restats")

    import pstats
    p = pstats.Stats('restats')
    p.strip_dirs().sort_stats('cumulative').print_stats(50)

else:
    cli.main()
