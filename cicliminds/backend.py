from itertools import groupby

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
import cftime

from cicliminds_lib.masks import get_land_mask
from cicliminds_lib.masks import get_antarctica_mask
from cicliminds_lib.masks import iter_reference_region_masks
from cicliminds_lib.bindings import cdo_remapcon_from_data
from cicliminds_lib.plotting._helpers import _get_variable_name

from cicliminds.interface.plot_types import get_plot_recipe_by_query
from cicliminds.interface.plot_query_adapter import PlotQueryAdapter


def process_block_query(fig, ax, datasets_reg, query):
    input_query, plot_query = query["input_query"], query["plot_query"]
    filtered_datasets_reg = filter_datasets_by_query(datasets_reg, input_query)
    datasets = merge_datasets_by_query(filtered_datasets_reg, input_query)
    masked_dataset = mask_dataset_by_query(datasets, plot_query)
    plot_config_patch = parse_plot_query(plot_query)
    annotate_plot_query(plot_config_patch, filtered_datasets_reg)
    plot_recipe = get_plot_recipe_by_query(plot_query)
    plot_recipe.plot(ax, masked_dataset, plot_config_patch)
    ax.set_position((0, 0.15, 1, 0.85))
    add_plot_descriptions(fig, ax, masked_dataset, plot_query)
    plt.close()


def merge_datasets_by_query(filtered_datasets_reg, query):
    ordered_by_scenario_reg = order_reg_by_scenario(filtered_datasets_reg, query)
    datasets = read_datasets(ordered_by_scenario_reg)
    merged_scenarios = merge_scenarios(datasets)
    merged_models = list(merge_models(merged_scenarios))
    return merged_models[0][1]


def filter_datasets_by_query(datasets_reg, query):
    common_mask = (datasets_reg["model"].isin(query["model"])) \
                & (datasets_reg["init_params"].isin(query["init_params"])) \
                & (datasets_reg["frequency"] == query["frequency"][0]) \
                & (datasets_reg["variable"] == query["variable"][0]) \
                & (datasets_reg["scenario"].isin(query["scenario"]))
    return datasets_reg[common_mask]


def order_reg_by_scenario(datasets_reg, query):
    scenarios = query["scenario"]

    def scenario_to_idx(scenario):
        return scenarios.index(scenario)

    new_reg = datasets_reg.copy()
    new_reg["scenario_idx"] = pd.Series([scenario_to_idx(sc) for sc in new_reg["scenario"]])
    new_reg.sort_values(by=["variable", "model", "init_params", "frequency", "scenario_idx"], inplace=True)
    del new_reg["scenario_idx"]
    return new_reg


def safe_drop_bounds(dataset, fields):
    to_drop = []
    for field in fields:
        try:
            bound_name = getattr(dataset, field).bounds
            to_drop.append(bound_name)
        except AttributeError:
            pass
    return dataset.drop_vars(to_drop)


def read_datasets(datasets_reg):
    for fname, params in datasets_reg.iterrows():
        list_params = [params[f] for f in ["variable", "model", "init_params", "frequency", "scenario"]]
        dataset = xr.load_dataset(fname)
        if not isinstance(dataset.time.values[0], np.datetime64):
            dataset["time"] = cftime.date2num(dataset.time.values, "seconds since 1970-01-01").astype("datetime64[s]")
        dataset = safe_drop_bounds(dataset, ["time", "lon", "lat"])
        yield (list_params, dataset)


def merge_scenarios(datasets):
    for _, scenario_group_iter in groupby(datasets, key=lambda row: row[0][:-1]):
        try:
            params, first_elem = next(scenario_group_iter)
        except StopIteration as e:
            raise Exception("something is wrong with scenario merging") from e
        scenario_group = [first_elem]
        for sc in scenario_group_iter:
            scenario_group.append(sc[1])
        merged = xr.concat(scenario_group, dim="time", data_vars="all")
        yield (params[:-1], merged)


def get_coarsest_grid(model_group):
    lon_dims = []
    lat_dims = []
    time_dims = []
    for model in model_group:
        lat_dims.append(model.lat.shape[0])
        lon_dims.append(model.lon.shape[0])
        time_dims.append(model.time.shape[0])
    return min(time_dims), min(lon_dims), min(lat_dims)


def unify_models_times(model_group, timeslice):
    res = []
    first_time = model_group[0].isel(time=timeslice).time
    for model in model_group:
        new = model.isel(time=timeslice).copy()
        new["time"] = first_time
        res.append(new)
    return res


def regrid_model_group(model_group, lon, lat):
    res = []
    for model in model_group:
        regrided_model = cdo_remapcon_from_data(model, lon, lat)
        res.append(regrided_model)
    return res


def merge_models(datasets):
    for _, model_group_iter in groupby(datasets, key=lambda row: row[0][:1] + row[0][3:]):
        param_group, model_group = zip(*model_group_iter)
        model_names = [f"{p[1]}_{p[2]}" for p in param_group]
        model_names_axis = pd.Series(model_names, name="model")
        if len(model_group) > 1:
            timerange, lon, lat = get_coarsest_grid(model_group)
            common_time_models = unify_models_times(model_group, slice(0, timerange))
            common_grid_models = regrid_model_group(common_time_models, lon, lat)
            merged = xr.concat(common_grid_models, dim=model_names_axis)
        else:
            merged = model_group[0].expand_dims({"model": model_names})
        yield (param_group[0][:1] + param_group[0][3:], merged)


def mask_dataset_by_query(dataset, plot_query):
    masked_dataset = _mask_regions(dataset, plot_query["regions"])
    return masked_dataset


def _mask_regions(data, regions):
    mask = get_land_mask(data)

    if not regions:
        mask = mask & (~get_antarctica_mask(data))
        return data.where(mask)

    all_reg_masks = [reg_mask for _, reg_mask in iter_reference_region_masks(data, regions)]
    reg_dim = pd.Series(regions, name="regions")
    merged_reg_mask = xr.concat(all_reg_masks, dim=reg_dim).any(dim="regions")
    mask = mask & merged_reg_mask
    return data.where(mask)


def parse_plot_query(plot_query):
    return PlotQueryAdapter.from_json(plot_query)


def annotate_plot_query(plot_query, datasets):
    plot_query["init_year"] = min(int(year) for timespan in datasets["timespan"].values for year in timespan.split("-"))


def add_plot_descriptions(fig, ax, dataset, plot_query):
    variable = _get_variable_name(dataset)
    variable_data = dataset[variable]
    description = variable_data.long_name
    reference_tag = "" if not plot_query["subtract_reference"] else " - ref"
    type_tag = f"{plot_query['plot_type']}{reference_tag}"
    title = f"{variable} [{type_tag}]"
    ax.set_title(title)
    fig.text(0, 0, f"Index description: {description}", wrap=True)
