import json
from ipywidgets import HBox, VBox, Button, Textarea, Output
from cicliminds.widgets.common import ObserverWidget


class BlockWidget(ObserverWidget):
    def __init__(self, query):
        self.state = {}
        self.state["config_widget"] = Textarea(value=json.dumps(query, indent=True),
                                               layout={"flex": "6 1 260px", "height": "10em",
                                                       "overflow": "hidden", "margin": "0 20px 0 0"})
        self.state["unstage_button"] = self._get_unstage_button()
        self.state["rebuild_button"] = self._get_rebuild_button()
        self.state["output"] = Output(layout={"flex": "1 1 0px"})
        self._real_output = None
        super().__init__()

    def render(self):
        block = VBox([
            HBox([self.state["config_widget"], VBox([self.state["unstage_button"], self.state["rebuild_button"]],
                 layout={"flex": "1 1 100px", "margin": "0 20px 0 0"})]),
            self.state["output"]
        ], layout={"margin": "5px 0"})
        return block

    def get_query(self):
        return json.loads(self.state["config_widget"].value)

    def capture_output(self):
        return self.state["output"]

    def replace_real_output(self, new_output):
        self._real_output = new_output

    def get_real_output(self):
        return self._real_output

    def _get_unstage_button(self):
        unstage_button = Button(description="Unstage", button_style="danger", icon="trash")
        unstage_button.on_click(self.trigger)
        return unstage_button

    def _get_rebuild_button(self):
        rebuild_button = Button(description="Rebuild", button_style="success", icon="redo")
        rebuild_button.on_click(self.trigger)
        return rebuild_button
