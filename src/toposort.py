from functools import reduce

# https://rosettacode.org/wiki/Topological_sort#Python
# data is a dict from key -> its dependencies
# a: [1,2,3] means a depends on 1,2,3
# return is line by line of values that can be processed
# in parallel before moving to next line
def toposort2(data):
    for k, v in data.items():
        v.discard(k) # Ignore self dependencies
    extra_items_in_deps = reduce(set.union, data.values()) - set(data.keys())
    data.update({item:set() for item in extra_items_in_deps})
    while True:
        ordered = set(item for item,dep in data.items() if not dep)
        if not ordered:
            break
        yield sorted(ordered)
        data = {item: (dep - ordered) for item,dep in data.items()
                if item not in ordered}
    assert not data, "A cyclic dependency exists amongst %r" % data

