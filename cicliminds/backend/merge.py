from itertools import groupby

import pandas as pd
import xarray as xr

from cicliminds.interface.datasets import get_datasets_for_block
from cicliminds.backend.normalize import safe_drop_bounds
from cicliminds.backend.normalize import get_coarsest_grid
from cicliminds.backend.normalize import normalize_calendar
from cicliminds.backend.normalize import infer_common_time_axis
from cicliminds.backend.normalize import align_time_axes
from cicliminds.backend.normalize import regrid_dataset_group


def get_merged_dataset_by_query(datasets_reg, query):
    filtered_datasets_reg = get_datasets_for_block(datasets_reg, query)
    ordered_by_scenario_reg = order_reg_by_scenario(filtered_datasets_reg, query)
    datasets = read_datasets(ordered_by_scenario_reg)
    merged_time_axes = merge_time_axes(datasets)
    standardized_datasets = standardize_datasets(merged_time_axes)
    merged_scenarios = merge_scenarios(standardized_datasets)
    merged_models = list(merge_models(merged_scenarios))
    return merged_models[0][1]


def order_reg_by_scenario(datasets_reg, query):
    scenarios = query["scenario"]

    def scenario_to_idx(scenario):
        return scenarios.index(scenario)

    new_reg = datasets_reg.copy()
    new_reg["scenario_idx"] = pd.Series([scenario_to_idx(sc) for sc in new_reg["scenario"]], index=new_reg.index)
    new_reg.sort_values(by=["variable", "model", "init_params", "frequency", "scenario_idx"], inplace=True)
    del new_reg["scenario_idx"]
    return new_reg


def read_datasets(datasets_reg):
    for fname, params in datasets_reg.iterrows():
        list_params = [params[f] for f in ["variable", "model", "init_params", "frequency", "scenario"]]
        dataset = xr.load_dataset(fname, use_cftime=False, decode_times=False)
        dataset = safe_drop_bounds(dataset, ["time", "lon", "lat"])
        freq = list_params[-2]
        common_time_ds = normalize_calendar(dataset, freq)
        yield (list_params, common_time_ds)


def merge_time_axes(datasets):
    for _, scenario_group_iter in groupby(datasets, key=lambda row: row[0][:-1]):
        historical, rest = _separate_historical(scenario_group_iter)
        if not historical:
            yield from rest
            return
        hist_params, hist_data = historical
        last_hist_date = hist_data.time.data[-1]
        for params, dataset in rest:
            cut_dataset = dataset.sel(time=slice(last_hist_date + 0.5, None))
            # we assume that projection starts not later than the moment when historical scenario ends
            merged = xr.concat([hist_data, cut_dataset], dim="time", data_vars="all", join="override")
            merged.attrs["merged_from"] = ",".join(params)
            *rest_params, scenario = params
            new_params = rest_params + [f"historical_{scenario}"]
            yield (new_params, merged)


def _separate_historical(datasets):
    historical = None
    rest = []
    for params, dataset in datasets:
        scenario = params[-1]
        if scenario == "historical":
            historical = (params, dataset)
            continue
        rest.append((params, dataset))
    return historical, rest


def standardize_datasets(datasets):
    param_group, dataset_group = zip(*datasets)
    if len(dataset_group) <= 1:
        yield from zip(param_group, dataset_group)
        return
    init_days, time_dim = infer_common_time_axis([m.time.data for m in dataset_group])
    time_aligned = align_time_axes(dataset_group, init_days, time_dim)
    lon, lat = get_coarsest_grid(dataset_group)
    common_grid_dataset = regrid_dataset_group(time_aligned, lon, lat)
    for param, dataset in zip(param_group, common_grid_dataset):
        yield param, dataset


def merge_scenarios(datasets):
    for _, scenario_group_iter in groupby(datasets, key=lambda row: row[0][:-1]):
        param_group, scenario_group = zip(*scenario_group_iter)
        scenarios = [p[-1] for p in param_group]
        if len(scenario_group) <= 1:
            for params, dataset in zip(param_group, scenario_group):
                yield params[:-1], dataset.expand_dims({"scenario": scenarios})
            return
        scenario_names_axis = pd.Series(scenarios, name="scenario")
        merged = xr.concat(scenario_group, dim=scenario_names_axis, join="override")
        yield (param_group[0][:-1], merged)


def merge_models(datasets):
    for _, model_group_iter in groupby(datasets, key=lambda row: row[0][:1] + row[0][3:]):
        param_group, model_group = zip(*model_group_iter)
        model_names = [f"{p[1]}_{p[2]}" for p in param_group]
        if len(model_group) <= 1:
            for params, dataset in zip(param_group, model_group):
                yield params[:-1], dataset.expand_dims({"model": model_names})
            return
        model_names_axis = pd.Series(model_names, name="model")
        merged = xr.concat(model_group, dim=model_names_axis, join="override")
        yield (param_group[0][:1] + param_group[0][3:], merged)
