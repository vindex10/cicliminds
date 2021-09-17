from copy import deepcopy
import numpy as np


def blocks_to_json_like(blocks):
    for block in blocks:
        for key, val in block.items():
            if not isinstance(val, list):
                block[key] = list(val)
        yield block


def expand_field(blocks, field, values):
    for block in blocks:
        for value in values:
            new_block = deepcopy(block)
            new_block[field] = deepcopy(value)
            yield new_block


def drop_nonexisting_blocks(unfiltered_blocks, known_mask, datasets_field):
    field = datasets_field.name
    for block in unfiltered_blocks:
        filtered_mask = known_mask & datasets_field.isin(block[field])
        if not np.any(filtered_mask):
            continue
        yield block, filtered_mask


def reduce_values_to_existing(blocks_with_mask, datasets_field):
    field = datasets_field.name
    for block, known_mask in blocks_with_mask:
        field_values_for_block = datasets_field[known_mask]
        new_values = field_values_for_block.unique()
        block[field] = new_values
        yield block, known_mask
