from copy import deepcopy
from dataclasses import asdict
from itertools import product

import numpy as np
import pandas as pd

from cicliminds.interface.plot_query_adapter import PlotQueryAdapter
from cicliminds.interface.plot_types import get_plot_recipe_by_query


def expand_state_into_queries(datasets, filter_values, agg_params):
    input_queries = expand_input_queries(datasets, filter_values, agg_params)
    plot_queries = expand_plot_queries(agg_params)
    for input_query, plot_query in product(input_queries, plot_queries):
        plot_query = append_plot_query_defaults(input_query, plot_query)
        yield {
            "input_query": deepcopy(input_query),
            "plot_query": plot_query
        }


def append_plot_query_defaults(input_query, plot_query):
    plot_recipe = get_plot_recipe_by_query(plot_query)
    plot_config_defaults = asdict(plot_recipe.get_default_config(input_query[0]["variable"]))
    plot_config_defaults.update(plot_query)
    plot_query_defaults = PlotQueryAdapter.to_json(deepcopy(plot_config_defaults), restrictive=False)
    return plot_query_defaults


def expand_plot_queries(agg_params):
    res = [{
        "reference_window_size": agg_params["reference_window_size"],
        "sliding_window_size": agg_params["sliding_window_size"],
        "slide_step": agg_params["slide_step"],
        "subtract_reference": agg_params["subtract_reference"],
        "normalize_histograms": agg_params["normalize_histograms"]
    }]
    res = expand_plot_types(res, agg_params["plot_types"])
    yield from res


def expand_plot_types(queries, plot_types):
    res = []
    for block in queries:
        for plot_type in plot_types:
            new_block = deepcopy(block)
            new_block.update({
                "plot_type": plot_type,
            })
            res.append(new_block)
    return res


def expand_input_queries(datasets, filter_values, agg_params):
    blocks_with_mask = expand_filters(datasets, filter_values, agg_params)
    blocks = (block for block, mask in blocks_with_mask)
    blocks = expand_regions(blocks, agg_params)
    yield from blocks


def expand_filters(datasets, filter_values, agg_params):
    mask = pd.Series(np.full(datasets.shape[0], True), index=datasets.index)
    blocks_with_mask = [({}, mask)]
    blocks_with_mask = expand_model_field(blocks_with_mask, "model", filter_values,
                                          agg_params["aggregate_models"], datasets)
    blocks_with_mask = expand_model_field(blocks_with_mask, "init_params", filter_values,
                                          agg_params["aggregate_model_ensembles"], datasets)
    blocks_with_mask = expand_model_field(blocks_with_mask, "frequency", filter_values, False, datasets)
    blocks_with_mask = expand_model_scenarios(blocks_with_mask, filter_values, agg_params["aggregate_years"], datasets)
    yield from blocks_with_mask


def apply_scenario_filter(datasets, mask, scenarios):
    new_mask = mask.copy()
    scenarios_set = set(scenarios)
    columns_without_scenario = [i for i in datasets.columns if i not in ["scenario", "timespan"]]
    for _, group in datasets[mask].groupby(columns_without_scenario):
        group_scenarios = set(group["scenario"].values)
        if not scenarios_set - group_scenarios:
            continue
        new_mask[group.index] = False
    return new_mask


def apply_scenario_filter_to_blocks(blocks_with_mask, datasets):
    for block, known_mask in blocks_with_mask:
        scenarios = block["scenario"]
        new_mask = apply_scenario_filter(datasets, known_mask, scenarios)
        if new_mask is None:
            continue
        yield block, new_mask


def expand_model_scenarios(blocks_with_mask, filter_values, agg, datasets):
    values = filter_values["scenario"]
    if not values:
        values = datasets["scenario"].unique()
    values = get_scenario_pairs(values) if agg else [[i] for i in values]
    for block, known_mask in blocks_with_mask:
        unfiltered_blocks = expand_field([block], "scenario", values)
        scenarios_column = datasets["scenario"]
        only_existing_blocks = drop_nonexisting_blocks(unfiltered_blocks, known_mask, scenarios_column)
        only_full_scenarios = apply_scenario_filter_to_blocks(only_existing_blocks, datasets)
        yield from reduce_values_to_existing(only_full_scenarios, scenarios_column)


def get_scenario_pairs(scenarios):
    if "historical" not in scenarios:
        return [[scenario] for scenario in scenarios]
    if len(scenarios) == 1:
        return [["historical"]]
    return [["historical", scenario] for scenario in scenarios if scenario != "historical"]


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


def expand_field(blocks, field, values):
    res = []
    for block in blocks:
        for value in values:
            new_block = deepcopy(block)
            new_block[field] = deepcopy(value)
            res.append(new_block)
    return res


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


def expand_regions(res, agg_params):
    selected_regions = agg_params["select_regions"] or []
    aggregate_regions = agg_params["aggregate_regions"]
    if aggregate_regions or not selected_regions:
        selected_regions = [selected_regions]
    res = expand_field(res, "regions", selected_regions)
    return res
