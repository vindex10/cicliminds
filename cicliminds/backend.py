from itertools import groupby

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from cicliminds_lib.masks import get_land_mask
from cicliminds_lib.masks import get_antarctica_mask
from cicliminds_lib.masks import iter_reference_region_masks
from cicliminds_lib.plotting._helpers import _get_variable_name

from cicliminds.interface.plot_types import get_plot_recipe_by_query
from cicliminds.interface.plot_query_adapter import PlotQueryAdapter


def process_block_query(fig, ax, datasets, query):
    input_query, plot_query = query["input_query"], query["plot_query"]
    dataset = get_dataset_by_query(datasets, input_query)
    masked_dataset = mask_dataset_by_query(dataset, query["input_query"])
    plot_config_patch = parse_plot_query(input_query, plot_query)
    plot_recipe = get_plot_recipe_by_query(plot_query)
    plot_recipe.plot(ax, masked_dataset, plot_config_patch)
    ax.set_position((0, 0.15, 1, 0.85))
    add_plot_descriptions(fig, ax, masked_dataset, plot_query)
    plt.close()


def get_dataset_by_query(datasets_reg, query):
    common_mask = (datasets_reg["model"].isin(query["model"])) \
               & (datasets_reg["init_params"] == query["init_params"]) \
               & (datasets_reg["frequency"] == query["frequency"]) \
               & (datasets_reg["variable"] == query["variable"]) \
               & (datasets_reg["scenario"].isin(query["scenario"])) \
               & (datasets_reg["timespan"].isin(query["timespan"]))
    filtered_reg = sort_reg(datasets_reg[common_mask], query)
    datasets = read_datasets(filtered_reg)
    datasets = merge_scenarios(datasets)
    datasets = list(merge_models(datasets))
    if len(datasets) > 1:
        raise Exception("Full merge failed for datasets")
    return datasets[0][1]


def sort_reg(datasets_reg, query):
    scenarios = query["scenario"]

    def scenario_to_idx(scenario):
        return scenarios.index(scenario)

    new_reg = datasets_reg.copy()
    new_reg["scenario_idx"] = pd.Series([scenario_to_idx(sc) for sc in new_reg["scenario"]])
    new_reg.sort_values(by=["variable", "model", "init_params", "frequency", "scenario_idx"], inplace=True)
    del new_reg["scenario_idx"]
    return new_reg


def read_datasets(datasets_reg):
    for fname, params in datasets_reg.iterrows():
        list_params = [params[f] for f in ["variable", "model", "init_params", "frequency", "scenario"]]
        yield (list_params, xr.load_dataset(fname))


def merge_scenarios(datasets):
    for _, scenario_group_iter in groupby(datasets, key=lambda row: row[0][:-1]):
        try:
            params, first_elem = next(scenario_group_iter)
        except StopIteration:
            return
        scenario_group = [first_elem]
        for sc in scenario_group_iter:
            scenario_group.append(sc[1])
        yield (params[:-1], xr.concat(scenario_group, dim="time", data_vars="all"))


def merge_models(datasets):
    for _, model_group_iter in groupby(datasets, key=lambda row: row[0][:1] + row[0][2:]):
        param_group, model_group = zip(*model_group_iter)
        model_names = pd.Series([p[1] for p in param_group], name="model")
        yield (param_group[0][:1] + param_group[0][2:], xr.concat(model_group, dim=model_names))


def mask_dataset_by_query(dataset, input_query):
    masked_dataset = _mask_regions(dataset, input_query["regions"])
    return masked_dataset


def _mask_regions(data, regions):
    mask = get_land_mask(data)

    if not regions:
        mask = mask & (~get_antarctica_mask(data))
        return data.where(mask)

    all_reg_mask = np.any([reg_mask for _, reg_mask in iter_reference_region_masks(data, regions)])
    mask = mask & all_reg_mask
    return data.where(mask)


def parse_plot_query(input_query, plot_query):
    plot_query["init_year"] = min(int(year) for timespan in input_query["timespan"] for year in timespan.split("-"))
    return PlotQueryAdapter.from_json(plot_query)


def add_plot_descriptions(fig, ax, dataset, plot_query):
    variable = _get_variable_name(dataset)
    variable_data = dataset[variable]
    description = variable_data.long_name
    reference_tag = "" if not plot_query["subtract_reference"] else " - ref"
    type_tag = f"{plot_query['plot_type']}{reference_tag}"
    title = f"{variable} [{type_tag}]"
    ax.set_title(title)
    fig.text(0, 0, f"Index description: {description}", wrap=True)
