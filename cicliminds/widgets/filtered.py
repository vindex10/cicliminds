import pandas as pd
from ipywidgets import Label, VBox, SelectMultiple
from cicliminds.widgets.filter import FilterWidget


class FilteredWidget:
    MAX_ROWS_TO_SHOW = 20

    def __init__(self):
        self.configurations_select = self._get_configurations_select()
        super().__init__()

    @staticmethod
    def _get_configurations_select():
        return SelectMultiple(disabled=False, layout={"width": "auto"})

    def update_state_from_dataset(self, dataset):
        options = []
        for _, row in dataset.iterrows():
            options.append((",").join(map(str, row[FilterWidget.FILTER_FIELDS].values)))
        self.configurations_select.options = options
        rows = min(self.MAX_ROWS_TO_SHOW, len(options))
        self.configurations_select.rows = rows
        self.configurations_select.notify_change({"type": "change", "name": "rows", "new": rows})
        self.configurations_select.notify_change({"type": "change", "name": "options", "new": options})

    def get_selected_dataset(self):
        models = self.configurations_select.value or self.configurations_select.options
        models_fields = (model.strip().split(",") for model in models)
        model_dicts = (dict(zip(FilterWidget.FILTER_FIELDS, model_fields)) for model_fields in models_fields)
        return pd.DataFrame(model_dicts)

    def render(self):
        return VBox([Label("Filtered configurations:"), self.configurations_select])
