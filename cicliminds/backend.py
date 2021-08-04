import tempfile
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from cicliminds_lib.bindings import cdo_cat
from cicliminds_lib.bindings import remove_grid

from cicliminds_lib.masks.masks import get_land_mask
from cicliminds_lib.masks.masks import get_antarctica_mask
from cicliminds_lib.masks.masks import iter_reference_region_masks

from cicliminds_lib.plotting.recipes.means_of_hists import plot_means_of_hists
from cicliminds_lib.plotting.recipes.means_of_hists import plot_means_of_hists_diff
from cicliminds_lib.plotting.recipes.hists_of_means import plot_hists_of_means
from cicliminds_lib.plotting.recipes.hists_of_means import plot_hists_of_means_diff
from cicliminds_lib.plotting.recipes.timeavgs import plot_hist_of_timeavgs
from cicliminds_lib.plotting.recipes.timeavgs import plot_hist_of_timeavgs_diff


PLOT_FUNCS = {
    "fldmean first": [plot_hists_of_means, plot_hists_of_means_diff],
    "fldmean last": [plot_means_of_hists, plot_means_of_hists_diff],
    "avg time": [plot_hist_of_timeavgs, plot_hist_of_timeavgs_diff]
}


def process_block_query(fig, ax, datasets, query):
    with tempfile.NamedTemporaryFile("r") as dataset:
        write_dataset_by_query(datasets, query["input_query"], dataset.name)
        meta, variable_data = mask_dataset_by_query(dataset.name, query["input_query"])
    plot_query = parse_plot_query(query["input_query"], query["plot_query"])
    plot_by_query(ax, variable_data, plot_query)
    ax.set_position((0, 0.15, 1, 0.85))
    add_plot_descriptions(fig, ax, variable_data, plot_query, meta)
    plt.close()


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


def mask_dataset_by_query(dataset, input_query):
    with tempfile.NamedTemporaryFile("r") as tmpfile:
        remove_grid(tmpfile.name, dataset)
        raw_data = xr.load_dataset(tmpfile.name)
    masked_data = _mask_regions(raw_data, input_query["regions"])
    variable_data = masked_data[input_query["variable"]]
    meta = {"description": variable_data.long_name}
    return meta, variable_data


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
    return plot_query


def plot_by_query(ax, variable_data, plot_query):
    plot_func = PLOT_FUNCS[plot_query["plot_type"]][int(plot_query["subtract_reference"])]
    plot_func(ax, variable_data, plot_query)


def add_plot_descriptions(fig, ax, variable_data, plot_query, meta):
    reference_tag = "" if not plot_query["subtract_reference"] else " - ref"
    type_tag = f"{plot_query['plot_type']}{reference_tag}"
    title = f"{variable_data.name} [{type_tag}]"
    ax.set_title(title)
    fig.text(0, 0, f"Index description: {meta['description']}", wrap=True)
