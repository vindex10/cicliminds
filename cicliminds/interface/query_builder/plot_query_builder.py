from copy import deepcopy
from dataclasses import asdict

from cicliminds_lib.mask.mask import REFERENCE_REGIONS

from cicliminds.interface.query_builder.basic_expanders import expand_field
from cicliminds.interface.plot_query_adapter import PlotQueryAdapter
from cicliminds.interface.plot_types import get_plot_recipe_by_query


def expand_plot_queries(agg_params):
    res = [{
        "reference_window_size": agg_params["reference_window_size"],
        "sliding_window_size": agg_params["sliding_window_size"],
        "slide_step": agg_params["slide_step"],
        "subtract_reference": agg_params["subtract_reference"],
        "normalize_histograms": agg_params["normalize_histograms"]
    }]
    res = expand_regions(res, agg_params)
    res = expand_field(res, "plot_type", agg_params["plot_types"])
    yield from res


def expand_regions(res, agg_params):
    selected_regions = agg_params["select_regions"] or []
    aggregate_regions = agg_params["aggregate_regions"]
    if aggregate_regions:
        selected_regions = [selected_regions]
    elif selected_regions:
        selected_regions = [[r] for r in selected_regions]
    else:
        selected_regions = [[f'{r.abbrev}'] for r in REFERENCE_REGIONS]
    res = expand_field(res, "regions", selected_regions)
    return res


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


def append_plot_query_defaults(input_query, plot_query):
    plot_recipe = get_plot_recipe_by_query(plot_query)
    plot_config_defaults = asdict(plot_recipe.get_default_config(input_query["datasets"]["variable"][0]))
    plot_config_defaults.update(plot_query)
    plot_query_defaults = PlotQueryAdapter.to_json(deepcopy(plot_config_defaults), restrictive=False)
    return plot_query_defaults
