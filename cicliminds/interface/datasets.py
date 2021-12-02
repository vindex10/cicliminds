import numpy as np
import pandas as pd

from cicliminds.interface.query_builder.filter_expander import expand_model_scenarios

DATASET_FIELDS = ["model", "scenario", "init_params", "frequency", "variable"]


def get_datasets_for_block(datasets_reg, query):
    mask = get_shallow_filters_mask(datasets_reg, query)
    mask = mask & get_scenarios_mask(datasets_reg, mask, True, True, query)
    return datasets_reg[mask].copy()


def get_shallow_filters_mask(datasets_reg, query):
    mask = pd.Series(np.full(datasets_reg.shape[0], True), index=datasets_reg.index)
    for field in DATASET_FIELDS:
        values = query[field]
        if not values:
            continue
        mask = mask & datasets_reg[field].isin(values)
    return mask


def get_scenarios_mask(datasets_reg, mask, agg_scenarios, agg_years, query):
    blocks_with_mask = [(query, mask)]
    scenarios_mask = pd.Series(np.full(datasets_reg.shape[0], False), index=datasets_reg.index)
    for _, partial_mask in expand_model_scenarios(blocks_with_mask, query, agg_scenarios, agg_years, datasets_reg):
        scenarios_mask = scenarios_mask | partial_mask
    return scenarios_mask
