from ipywidgets import Label, VBox, HBox, Button, SelectMultiple, Checkbox, IntText

from cicliminds_lib.plotting.config import DEFAULT_RECIPE_CONFIG
from cicliminds_lib.masks import REFERENCE_REGIONS
from cicliminds.widgets.common import ObserverWidget
from cicliminds.interface.plot_types import PLOT_TYPES_SPEC


class StagingWidget(ObserverWidget):
    DEFAULTS = {"plot_type": list(PLOT_TYPES_SPEC)[1],
                "reference_window_size": DEFAULT_RECIPE_CONFIG["reference_window_size"],
                "sliding_window_size": DEFAULT_RECIPE_CONFIG["sliding_window_size"],
                "slide_step": DEFAULT_RECIPE_CONFIG["slide_step"],
                "normalize_histograms": DEFAULT_RECIPE_CONFIG["normalize_histograms"]}

    def __init__(self):
        self.state = {}
        self.state["select_regions"] = self._get_select_regions()
        self.state["aggregate_years"] = Checkbox(description="years (scenarios)", value=True,
                                                 indent=False, layout={"width": "auto"})
        self.state["aggregate_regions"] = Checkbox(description="regions", value=True,
                                                   indent=False, layout={"width": "auto"})
        self.state["aggregate_models"] = Checkbox(description="models", value=True,
                                                  indent=False, layout={"width": "auto"})
        self.state["aggregate_model_ensembles"] = Checkbox(description="model ensembles (init_params)", value=True,
                                                           indent=False, layout={"width": "auto"})
        self.state["plot_types"] = SelectMultiple(options=list(PLOT_TYPES_SPEC), value=(self.DEFAULTS["plot_type"],),
                                                  rows=6, layout={"width": "auto"})
        self.state["subtract_reference"] = Checkbox(description="Subtract reference",
                                                    indent=False, layout={"width": "auto"})
        self.state["normalize_histograms"] = Checkbox(description="Normalize histograms",
                                                      indent=False, value=self.DEFAULTS["normalize_histograms"],
                                                      layout={"width": "auto"})
        self.state["reference_window_size"] = IntText(value=self.DEFAULTS["reference_window_size"],
                                                      layout={"width": "auto"})
        self.state["sliding_window_size"] = IntText(value=self.DEFAULTS["sliding_window_size"],
                                                    layout={"width": "auto"})
        self.state["slide_step"] = IntText(value=self.DEFAULTS["slide_step"],
                                           layout={"width": "auto"})
        self.state["button_stage"] = self._get_button_stage()
        super().__init__()

    def render(self):
        block_layout = {"flex": "1 1 100px", "width": "auto", "margin": "0 20px 0 0"}
        staging_panel = HBox([
            VBox([Label("Regions"), self.state["select_regions"]],
                 layout=block_layout),
            VBox([Label("Aggregate"),
                  self.state["aggregate_years"], self.state["aggregate_regions"],
                  self.state["aggregate_models"], self.state["aggregate_model_ensembles"]],
                 layout=block_layout),
            VBox([Label("Plot type"), self.state["plot_types"],
                  self.state["subtract_reference"], self.state["normalize_histograms"]],
                 layout=block_layout),
            VBox([Label("Reference window size"), self.state["reference_window_size"],
                  Label("Sliding window size"), self.state["sliding_window_size"],
                  Label("Slide step"), self.state["slide_step"]],
                 layout=block_layout),
            VBox([Label(), self.state["button_stage"]],
                 layout=block_layout)
        ])
        return staging_panel

    def get_state(self):
        res = {k: obj.value for k, obj in self.state.items() if k != "button_stage"}
        selected_region_ids = [region.split(":")[0].strip() for region in res["select_regions"]]
        res["select_regions"] = selected_region_ids
        return res

    @staticmethod
    def _get_select_regions():
        region_names = [f'{r.abbrev} :: {r.name}' for r in REFERENCE_REGIONS]
        select = SelectMultiple(options=region_names, value=region_names[:1], rows=10, layout={"width": "auto"})
        return select

    def _get_button_stage(self):
        button_stage = Button(description="Stage", button_style="success", icon="plus")
        button_stage.on_click(self.trigger)
        return button_stage
