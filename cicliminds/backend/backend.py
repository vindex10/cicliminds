import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import cftime

from cicliminds_lib.masks import get_land_mask
from cicliminds_lib.masks import get_antarctica_mask
from cicliminds_lib.masks import iter_reference_region_masks
from cicliminds_lib.plotting._helpers import _get_variable_name

from cicliminds.backend.merge import get_merged_dataset_by_query
from cicliminds.interface.plot_types import get_plot_recipe_by_query
from cicliminds.interface.plot_query_adapter import PlotQueryAdapter


def process_block_query(fig, ax, datasets_reg, query):
    input_query, plot_query = query["input_query"], query["plot_query"]
    datasets = get_merged_dataset_by_query(datasets_reg, input_query)
    masked_dataset = mask_dataset_by_query(datasets, plot_query)
    plot_datasets(fig, ax, masked_dataset, plot_query)


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


def plot_datasets(fig, ax, masked_dataset, plot_query):
    plot_recipe = get_plot_recipe_by_query(plot_query)
    recipe_config = get_recipe_config(plot_query, masked_dataset)
    plot_recipe.plot(ax, masked_dataset, recipe_config)
    ax.set_position((0, 0.25, 1, 0.85))
    add_plot_descriptions(fig, ax, masked_dataset, plot_query)
    plt.close()


def get_recipe_config(plot_query, masked_dataset):
    parsed_query = PlotQueryAdapter.from_json(plot_query)
    annotate_plot_query(parsed_query, masked_dataset)
    return parsed_query


def annotate_plot_query(plot_query, masked_dataset):
    plot_query["init_year"] = cftime.num2date(masked_dataset.time.data[0],
                                              masked_dataset.time.attrs["units"],
                                              masked_dataset.time.attrs["calendar"]).year


def add_plot_descriptions(fig, ax, dataset, plot_query):
    variable = _get_variable_name(dataset)
    variable_data = dataset[variable]
    description = variable_data.long_name
    reference_tag = "" if not plot_query["subtract_reference"] else " - ref"
    type_tag = f"{plot_query['plot_type']}{reference_tag}"
    title = f"{variable} [{type_tag}]"
    ax.set_title(title)
    txt = fig.text(0, 0, f"Index description: {description}\nRegions: {', '.join(plot_query['regions'])}", wrap=True)
    fig_width, _ = fig.get_size_inches()*fig.dpi
    txt._get_wrap_line_width = lambda : fig_width*0.9
