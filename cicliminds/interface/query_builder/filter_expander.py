import numpy as np
import pandas as pd

from cicliminds.interface.datasets import apply_scenario_filter
from cicliminds.interface.query_builder.basic_expanders import expand_field
from cicliminds.interface.query_builder.basic_expanders import drop_nonexisting_blocks
from cicliminds.interface.query_builder.basic_expanders import reduce_values_to_existing


def expand_filters(datasets, filter_values, agg_params):
    mask = pd.Series(np.full(datasets.shape[0], True), index=datasets.index)
    blocks_with_mask = [({}, mask)]
    blocks_with_mask = expand_model_field(blocks_with_mask, "variable", filter_values, False, datasets)
    blocks_with_mask = expand_model_field(blocks_with_mask, "model", filter_values,
                                          agg_params["aggregate_models"], datasets)
    blocks_with_mask = expand_model_field(blocks_with_mask, "init_params", filter_values,
                                          agg_params["aggregate_model_ensembles"], datasets)
    blocks_with_mask = expand_model_field(blocks_with_mask, "frequency", filter_values, False, datasets)
    blocks_with_mask = expand_model_scenarios(blocks_with_mask, filter_values,
                                              agg_params["aggregate_years"], agg_params["aggregate_scenarios"],
                                              datasets)
    yield from blocks_with_mask


def expand_model_field(blocks_with_mask, field, filter_values, agg, datasets):
    values = filter_values[field]
    if not values:
        values = datasets[field].unique()
    values = [values] if agg else [[i] for i in values]
    for block, known_mask in blocks_with_mask:
        unfiltered_blocks = expand_field([block], field, values)
        field_column = datasets[field]
        only_existing_blocks = drop_nonexisting_blocks(unfiltered_blocks, known_mask, field_column)
        yield from reduce_values_to_existing(only_existing_blocks, field_column)


def expand_model_scenarios(blocks_with_mask, filter_values, agg_scenarios, agg_years, datasets):
    values = filter_values["scenario"]
    if not values:
        values = datasets["scenario"].unique()

    if agg_scenarios:
        values = [values]
    elif agg_years:
        values = _get_scenario_pairs(values)
    else:
        values = [[i] for i in values]

    for block, known_mask in blocks_with_mask:
        unfiltered_blocks = expand_field([block], "scenario", values)
        scenarios_column = datasets["scenario"]
        only_existing_blocks = drop_nonexisting_blocks(unfiltered_blocks, known_mask, scenarios_column)
        only_full_scenarios = apply_scenario_filter_to_blocks(only_existing_blocks, datasets)
        yield from reduce_values_to_existing(only_full_scenarios, scenarios_column)


def _get_scenario_pairs(scenarios):
    if "historical" not in scenarios:
        return [[scenario] for scenario in scenarios]
    if len(scenarios) == 1:
        return [["historical"]]
    return [["historical", scenario] for scenario in scenarios if scenario != "historical"]


def apply_scenario_filter_to_blocks(blocks_with_mask, datasets):
    for block, known_mask in blocks_with_mask:
        scenarios = block["scenario"]
        new_mask = apply_scenario_filter(datasets, known_mask, scenarios)
        if new_mask is None:
            continue
        yield block, new_mask
