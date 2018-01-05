from __future__ import print_function
from src import fakeplate
from os import environ as ENV

PROFILE=False
if PROFILE:
    print("PROFILING")
    import cProfile
    cProfile.run("fakeplate.main()", "restats")

    import pstats
    p = pstats.Stats('restats')
    p.strip_dirs().sort_stats('cumulative').print_stats(50)

else:
    fakeplate.main()
