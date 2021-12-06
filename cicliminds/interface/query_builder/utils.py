from copy import deepcopy
from itertools import product


def list_product(name_to_stream):
    keys = list(name_to_stream)
    for vals in product(*name_to_stream.values()):
        copied = map(deepcopy, vals)
        yield dict(zip(keys, copied))
