from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
from itertools import chain
from itertools import product

from cicliminds.interface.plot_query_adapter import PlotQueryAdapter
from cicliminds.interface.plot_types import get_plot_recipe_by_query


def expand_state_into_queries(models, agg_params):
    input_queries = expand_input_queries(models, agg_params)
    plot_queries = expand_plot_queries(agg_params)
    for input_query, plot_query in product(input_queries, plot_queries):
        plot_query = append_plot_query_defaults(input_query, plot_query)
        yield {
            "input_query": deepcopy(input_query),
            "plot_query": plot_query
        }


def append_plot_query_defaults(input_query, plot_query):
    plot_recipe = get_plot_recipe_by_query(plot_query)
    plot_config_defaults = asdict(plot_recipe.get_default_config(input_query["variable"]))
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


def expand_input_queries(models, agg_params):
    res = [{}]
    selected_regions = agg_params["select_regions"] or []
    aggregate_regions = agg_params["aggregate_regions"]
    if aggregate_regions or not selected_regions:
        res = expand_regions_agg(res, selected_regions)
    else:
        res = expand_regions_noagg(res, selected_regions)
    indexed_res = expand_models_indexed(res, models)
    if agg_params["aggregate_years"]:
        yield from agg_indexed_models_by_years(indexed_res)
    else:
        yield from chain.from_iterable(indexed_res.values())


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


def expand_regions_agg(queries, regions):
    res = []
    for block in queries:
        new_block = deepcopy(block)
        new_block.update({
            "regions": regions
        })
        res.append(new_block)
    return res


def expand_regions_noagg(queries, regions):
    res = []
    for block in queries:
        for region in regions:
            new_block = deepcopy(block)
            new_block.update({
                "regions": [region]
            })
            res.append(new_block)
    return res


def expand_models_indexed(queries, models):
    ts_index = defaultdict(list)
    for block in queries:
        for _, model in models.iterrows():
            new_block = deepcopy(block)
            new_block.update(model.to_dict())
            key = ":".join(model.drop(["scenario", "timespan"]).values)
            new_block["scenario"] = [new_block["scenario"]]
            new_block["timespan"] = [new_block["timespan"]]
            if new_block["scenario"][0] == "historical":
                ts_index[key].insert(0, new_block)
            else:
                ts_index[key].append(new_block)
    return ts_index


def agg_indexed_models_by_years(indexed_queries):
    for blocks in indexed_queries.values():
        if len(blocks) > 1:
            yield from agg_years(blocks)
            continue
        yield from blocks


def agg_years(query_group):
    hist_block = query_group[0]
    for block in query_group[1:]:
        new_block = deepcopy(hist_block)
        new_block["scenario"] += block["scenario"]
        new_block["timespan"] += block["timespan"]
        yield new_block
