import tempfile
import numpy as np
import xarray as xr

from cicliminds_lib.bindings import cdo_cat
from cicliminds_lib.bindings import remove_grid

from cicliminds_lib.masks.masks import get_land_mask
from cicliminds_lib.masks.masks import get_antarctica_mask
from cicliminds_lib.masks.masks import iter_reference_region_masks

from cicliminds_lib.plotting.plot_recipes import plot_means_of_hists
from cicliminds_lib.plotting.plot_recipes import plot_means_of_hists_diff
from cicliminds_lib.plotting.plot_recipes import plot_hists_of_means
from cicliminds_lib.plotting.plot_recipes import plot_hists_of_means_diff
from cicliminds_lib.plotting.plot_recipes import plot_hist_of_timeavgs
from cicliminds_lib.plotting.plot_recipes import plot_hist_of_timeavgs_diff


PLOT_FUNCS = {
    "fldmean first": [plot_hists_of_means, plot_hists_of_means_diff],
    "fldmean last": [plot_means_of_hists, plot_means_of_hists_diff],
    "avg time": [plot_hist_of_timeavgs, plot_hist_of_timeavgs_diff]
}


def write_dataset_by_query(datasets, query, output):
    common_mask = (datasets["model"] == query["model"]) \
               & (datasets["init_params"] == query["init_params"]) \
               & (datasets["frequency"] == query["frequency"]) \
               & (datasets["variable"] == query["variable"]) \
               & (datasets["scenario"].isin(query["scenario"])) \
               & (datasets["timespan"].isin(query["timespan"]))

    def scenario_to_idx(scenario):
        return query["scenario"].index(scenario)
    files = datasets[common_mask].sort_values(by=["scenario"],
                                              key=lambda x: x.apply(scenario_to_idx))
    cdo_cat(output, files.index.values)


def plot_by_query(ax, dataset, query):
    with tempfile.NamedTemporaryFile("r") as tmpfile:
        remove_grid(tmpfile.name, dataset)
        raw_data = xr.load_dataset(tmpfile.name)
    masked_data = _mask_regions(raw_data, query["regions"])
    plot_func = PLOT_FUNCS[query["plot_type"]][int(query["subtract_reference"])]
    plot_func(ax, masked_data[query["variable"]])


def _mask_regions(data, regions):
    mask = get_land_mask(data)

    if not regions:
        mask = mask & (~get_antarctica_mask(data))
        return data.where(mask)

    all_reg_mask = np.any([reg_mask for _, reg_mask in iter_reference_region_masks(data, regions)])
    mask = mask & all_reg_mask
    return data.where(mask)
