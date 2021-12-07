import matplotlib.pyplot as plt
import cftime

from cicliminds_lib.unify.api import get_merged_inputs_by_query
from cicliminds_lib.mask.api import get_dataset_mask_by_query
from cicliminds_lib.plotting._helpers import _get_variable_name

from cicliminds.interface.plot_types import get_plot_recipe_by_query
from cicliminds.interface.plot_query_adapter import PlotQueryAdapter


def process_block_query(fig, ax, query, datasets_reg, model_weights_reg):
    input_query, plot_query = query["input_query"], query["plot_query"]
    input_regs = {
        "datasets": datasets_reg,
        "model_weights": model_weights_reg
    }
    inputs = get_merged_inputs_by_query(input_regs, input_query)
    mask = get_dataset_mask_by_query(inputs["datasets"], plot_query)
    inputs["datasets"] = inputs["datasets"].where(mask)
    plot_datasets(fig, ax, plot_query, inputs)


def plot_datasets(fig, ax, plot_query, inputs):
    plot_recipe = get_plot_recipe_by_query(plot_query)
    recipe_config = get_recipe_config(plot_query, inputs["datasets"])
    plot_recipe.plot(ax, recipe_config, inputs)
    ax.set_position((0, 0.25, 1, 0.85))
    add_plot_descriptions(fig, ax, plot_query, inputs)
    plt.close()


def get_recipe_config(plot_query, masked_dataset):
    parsed_query = PlotQueryAdapter.from_json(plot_query)
    annotate_plot_query(parsed_query, masked_dataset)
    return parsed_query


def annotate_plot_query(plot_query, masked_dataset):
    plot_query["init_year"] = cftime.num2date(masked_dataset.time.data[0],
                                              masked_dataset.time.attrs["units"],
                                              masked_dataset.time.attrs["calendar"]).year


def add_plot_descriptions(fig, ax, plot_query, inputs):
    dataset = inputs["datasets"]
    variable = _get_variable_name(dataset)
    variable_data = dataset[variable]
    description = variable_data.long_name
    reference_tag = "" if not plot_query["subtract_reference"] else " - ref"
    type_tag = f"{plot_query['plot_type']}{reference_tag}"
    title = f"{variable} [{type_tag}]"
    ax.set_title(title)
    txt = fig.text(0, 0, f"Index description: {description}\nRegions: {', '.join(plot_query['regions'])}", wrap=True)
    fig_width, _ = fig.get_size_inches()*fig.dpi
    txt._get_wrap_line_width = lambda: fig_width*0.9
