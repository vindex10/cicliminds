import numpy as np
from ipywidgets import Label, VBox, HBox, Button, SelectMultiple
from cicliminds.widgets.common import ObserverWidget


class FilterWidget(ObserverWidget):
    FILTER_FIELDS = ["model", "scenario", "init_params", "frequency", "timespan", "variable"]

    def __init__(self, datasets):
        self.datasets = datasets.copy()
        self.button_reset = self._get_reset_button()
        self.filter_widgets = self._get_filter_widgets()
        super().__init__()

    def render(self):
        filter_controls = VBox([self.button_reset])
        filter_widget_panel = self._get_filter_widget_panel()
        filter_widget = VBox([Label("Configuration filter:"),
                              filter_widget_panel,
                              filter_controls])
        return filter_widget

    def get_filtered_dataset(self):
        mask = np.full(self.datasets.shape[0], True)
        for field, widget in self.filter_widgets.items():
            if not widget.value:
                continue
            mask = mask & self.datasets[field].isin(widget.value)
        return self.datasets[mask].copy()

    def update_state_from_dataset(self, partial_dataset):
        for field, widget in self.filter_widgets.items():
            if widget.value:
                continue
            widget.options = partial_dataset[field].unique()
            widget.notify_change({"type": "change", "name": "options", "new": widget.options})

    def _get_filter_widget_panel(self):
        filters = []
        for field, widget in self.filter_widgets.items():
            filters.append(VBox([Label(field), widget], layout={"flex": "1 1 100px", "width": "auto"}))
        filter_widget = HBox(filters)
        return filter_widget

    def _get_reset_button(self):
        button_reset = Button(description="Reset filter", button_style="danger", icon="broom")
        button_reset.on_click(self._reset_filters)
        return button_reset

    def _reset_filters(self, change):  # pylint: disable=unused-argument
        for widget in self.filter_widgets.values():
            widget.values = tuple()
            widget.notify_change({"type": "change", "name": "value", "new": tuple()})

    def _get_filter_widgets(self):
        filter_widgets = {}
        for field in self.FILTER_FIELDS:
            widget = SelectMultiple(
                options=self.datasets[field].unique(),
                layout={"width": "auto", "margin": "0 20px 0 0"},
                rows=10,
                disabled=False)
            widget.observe(self.trigger, names="value")
            filter_widgets[field] = widget
        return filter_widgets
