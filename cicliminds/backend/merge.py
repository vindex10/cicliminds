from itertools import groupby

import numpy as np
import pandas as pd
import xarray as xr

import cftime

from cicliminds.backend.normalize import safe_drop_bounds
from cicliminds.backend.normalize import get_coarsest_grid
from cicliminds.backend.normalize import unify_models_times
from cicliminds.backend.normalize import regrid_model_group


def get_merged_dataset_by_query(filtered_datasets_reg, query):
    ordered_by_scenario_reg = order_reg_by_scenario(filtered_datasets_reg, query)
    datasets = read_datasets(ordered_by_scenario_reg)
    merged_scenarios = merge_scenarios(datasets)
    merged_models = list(merge_models(merged_scenarios))
    return merged_models[0][1]


def order_reg_by_scenario(datasets_reg, query):
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
            # otherwise might just raise StopIteration when it should fail
            raise Exception("something is wrong with scenario merging") from e
        scenario_group = [first_elem]
        for sc in scenario_group_iter:
            scenario_group.append(sc[1])
        merged = xr.concat(scenario_group, dim="time", data_vars="all")
        yield (params[:-1], merged)


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
