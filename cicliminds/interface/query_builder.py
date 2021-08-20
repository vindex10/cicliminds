from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
from itertools import chain
from itertools import product

from cicliminds.widgets.filter import FilterWidget

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


def expand_input_queries(models, agg_params):
    res = [{}]
    res = expand_regions(res, agg_params)
    res = expand_models(res, models)
    res = agg_model_years(res, agg_params)
    res = agg_model_types(res, agg_params)
    yield from res


def expand_regions(res, agg_params):
    selected_regions = agg_params["select_regions"] or []
    aggregate_regions = agg_params["aggregate_regions"]
    if aggregate_regions or not selected_regions:
        res = expand_regions_agg(res, selected_regions)
    else:
        res = expand_regions_noagg(res, selected_regions)
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


def expand_models(queries, models):
    for block in queries:
        for _, model in models.iterrows():
            new_block = deepcopy(block)
            new_block.update(model.to_dict())
            new_block["scenario"] = [new_block["scenario"]]
            new_block["timespan"] = [new_block["timespan"]]
            new_block["model"] = [new_block["model"]]
            yield new_block


def agg_model_years(res, agg_params):
    indexed_res = build_models_index(res, ["scenario", "timespan"])
    put_historical_first(indexed_res)
    if agg_params["aggregate_years"]:
        yield from agg_indexed_models_by_years(indexed_res)
    else:
        yield from chain.from_iterable(indexed_res.values())


def put_historical_first(indexed_res):
    for row in indexed_res.values():
        for i, model in enumerate(row):
            if model["scenario"][0] == "historical":
                break
        else:
            continue
        del row[i]  # pylint: disable=undefined-loop-variable
        row.insert(0, model)  # pylint: disable=undefined-loop-variable


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


def agg_model_types(queries, agg_params):
    if not agg_params["aggregate_models"]:
        yield from queries
        return

    model_index = build_models_index(queries, ignore_fields=["model"])
    for blocks in model_index.values():
        models = [block["model"][0] for block in blocks]
        new_block = deepcopy(blocks[0])
        new_block["model"] = models
        yield new_block


def build_models_index(queries, ignore_fields=None):
    ts_index = defaultdict(list)
    for block in queries:
        new_block = deepcopy(block)
        key = dataset_key_from_block(new_block, ignore_fields)
        ts_index[key].append(new_block)
    return ts_index


def dataset_key_from_block(block, ignore_fields=None):
    if ignore_fields is None:
        ignore_fields = []
    parts = [_join_list(block[f]) for f in FilterWidget.FILTER_FIELDS if f not in ignore_fields]
    return ";".join(parts)


def _join_list(obj):
    if isinstance(obj, list):
        return ":".join(obj)
    return obj
