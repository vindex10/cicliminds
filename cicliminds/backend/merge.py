from itertools import groupby

import pandas as pd
import xarray as xr

from cicliminds.interface.datasets import get_datasets_for_block
from cicliminds.backend.normalize import safe_drop_bounds
from cicliminds.backend.normalize import get_coarsest_grid
from cicliminds.backend.normalize import normalize_time
from cicliminds.backend.normalize import regrid_model_group


def get_merged_dataset_by_query(datasets_reg, query):
    filtered_datasets_reg = get_datasets_for_block(datasets_reg, query)
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
        dataset = xr.load_dataset(fname, use_cftime=False, decode_times=False)
        dataset = safe_drop_bounds(dataset, ["time", "lon", "lat"])
        freq = list_params[-2]
        common_time_ds = normalize_time(dataset, freq)
        yield (list_params, common_time_ds)


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
        merged = xr.concat(scenario_group, dim="time", data_vars="all", join="override")
        merged.attrs["merged_from"] = ",".join(params)
        yield (params[:-1], merged)


def merge_models(datasets):
    for _, model_group_iter in groupby(datasets, key=lambda row: row[0][:1] + row[0][3:]):
        param_group, model_group = zip(*model_group_iter)
        model_names = [f"{p[1]}_{p[2]}" for p in param_group]
        model_names_axis = pd.Series(model_names, name="model")
        if len(model_group) > 1:
            lon, lat = get_coarsest_grid(model_group)
            common_grid_models = regrid_model_group(model_group, lon, lat)
            merged = xr.concat(common_grid_models, dim=model_names_axis, join="inner")
        else:
            merged = model_group[0].expand_dims({"model": model_names})
        yield (param_group[0][:1] + param_group[0][3:], merged)