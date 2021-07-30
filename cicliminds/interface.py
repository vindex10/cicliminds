from collections import defaultdict
from copy import deepcopy
from itertools import chain


def expand_state_into_queries(models, agg_params):
    res = [{
        "reference_window_size": agg_params["reference_window_size"],
        "sliding_window_size": agg_params["sliding_window_size"],
        "slide_step": agg_params["slide_step"],
        "subtract_reference": agg_params["subtract_reference"],
    }]
    res = expand_plot_types(res, agg_params["plot_types"])

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
