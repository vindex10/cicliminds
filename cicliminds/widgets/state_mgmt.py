import json
from ipywidgets import HBox, VBox, Button, Textarea, Label
from cicliminds.widgets.common import ObserverWidget


class StateMgmtWidget(ObserverWidget):
    def __init__(self):
        self.state = {}
        self.state["state_widget"] = Textarea(value="",
                                              layout={"flex": "6 1 260px", "height": "10em",
                                                      "overflow": "hidden", "margin": "0 20px 0 0"})
        self.state["dump_state_button"] = self._get_dump_state_button()
        self.state["save_pdf_button"] = self._get_save_pdf_button()
        self.state["stage_state_button"] = self._get_prepend_state_button()
        super().__init__()

    def render(self):
        block = VBox([
            Label("Save and restore blocks:"),
            HBox([self.state["state_widget"], VBox([self.state["dump_state_button"],
                                                    self.state["save_pdf_button"],
                                                    self.state["stage_state_button"]],
                 layout={"flex": "1 1 100px", "margin": "0 20px 0 0"})])
        ], layout={"margin": "5px 0"})
        return block

    def get_state(self):
        str_state = self.state["state_widget"].value
        if not str_state:
            return []
        return json.loads(str_state)

    def set_state(self, new_state):
        self.state["state_widget"].value = json.dumps(new_state, indent=True)

    def clear_state(self):
        self.state["state_widget"].value = ""

    def _get_dump_state_button(self):
        dump_state_button = Button(description="Dump", button_style="info", icon="clipboard")
        dump_state_button.on_click(self.trigger)
        return dump_state_button

    def _get_save_pdf_button(self):
        save_pdf_button = Button(description="Save PDF", button_style="info", icon="file-pdf-o")
        save_pdf_button.on_click(self.trigger)
        return save_pdf_button

    def _get_prepend_state_button(self):
        rebuild_button = Button(description="Stage", button_style="success", icon="plus")
        rebuild_button.on_click(self.trigger)
        return rebuild_button
