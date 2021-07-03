from ipywidgets import Label, VBox, HBox, Button, SelectMultiple, Checkbox, IntText
from cicliminds_lib.masks.loaders import load_reference_regions_meta
from cicliminds.widgets.common import ObserverWidget


class StagingWidget(ObserverWidget):
    PLOT_TYPES = ["fldmean first", "fldmean last", "avg time"]
    DEFAULTS = {"plot_type": "fldmean last",
                "reference_window_size": 50,
                "sliding_window_size": 20,
                "slide_step": 10}

    def __init__(self):
        self.state = {}
        self.state["select_regions"] = self._get_select_regions()
        self.state["aggregate_years"] = Checkbox(description="years", value=True,
                                                 indent=False, layout={"width": "auto"})
        self.state["aggregate_regions"] = Checkbox(description="regions",
                                                   indent=False, layout={"width": "auto"})
        self.state["plot_types"] = SelectMultiple(options=self.PLOT_TYPES, value=(self.DEFAULTS["plot_type"],),
                                                  rows=6, layout={"width": "auto"})
        self.state["subtract_reference"] = Checkbox(description="Subtract reference",
                                                    indent=False, layout={"width": "auto"})
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
            VBox([Label("Aggregate"), self.state["aggregate_years"], self.state["aggregate_regions"]],
                 layout=block_layout),
            VBox([Label("Plot type"), self.state["plot_types"], self.state["subtract_reference"]],
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
        region_names = [f'{r["LAB"]} :: {r["NAME"]}' for _, r in load_reference_regions_meta().iterrows()]
        select = SelectMultiple(options=region_names, value=region_names[:1], rows=10, layout={"width": "auto"})
        return select

    def _get_button_stage(self):
        button_stage = Button(description="Stage", button_style="success", icon="plus")
        button_stage.on_click(self.trigger)
        return button_stage