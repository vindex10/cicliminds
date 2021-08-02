import tempfile
import matplotlib.pyplot as plt
from IPython.display import clear_output, display
from ipywidgets import VBox

from cicliminds.widgets.filter import FilterWidget
from cicliminds.widgets.filtered import FilteredWidget
from cicliminds.widgets.staging import StagingWidget
from cicliminds.widgets.staged import StagedWidget
from cicliminds.widgets.block import BlockWidget
from cicliminds.widgets.state_mgmt import StateMgmtWidget

from cicliminds.interface import expand_state_into_queries
from cicliminds.backend import write_dataset_by_query
from cicliminds.backend import plot_by_query


class App:  # pylint: disable=too-few-public-methods
    def __init__(self, datasets):
        self.datasets = datasets
        self.state = {}
        self.state["filter_widget"] = self._get_filter_widget()
        self.state["filtered_widget"] = FilteredWidget()
        self.state["staging_widget"] = self._get_staging_widget()
        self.state["staged_widget"] = self._get_staged_widget()
        self.state["state_mgmt_widget"] = self._get_state_mgmt_widget()

    def _get_filter_widget(self):
        filter_widget = FilterWidget(self.datasets)
        filter_widget.observe(self._update_filters)
        return filter_widget

    def _get_staging_widget(self):
        staging_widget = StagingWidget()
        staging_widget.observe(self._stage_action)
        return staging_widget

    def _get_staged_widget(self):
        staged_widget = StagedWidget()
        staged_widget.observe(self._rebuild_one_block_action)
        return staged_widget

    def _get_state_mgmt_widget(self):
        state_mgmt_widget = StateMgmtWidget()
        state_mgmt_widget.observe(self._dump_state_action)
        state_mgmt_widget.observe(self._stage_state_action)
        return state_mgmt_widget

    def render(self):
        app = VBox([self.state["filter_widget"].render(),
                    self.state["filtered_widget"].render(),
                    self.state["staging_widget"].render(),
                    self.state["staged_widget"].render(),
                    self.state["state_mgmt_widget"].render()])
        self.state["filter_widget"].reset_filters()
        return app

    def _update_filters(self, objs, change):  # pylint: disable=unused-argument
        filters_widget = objs[0]
        filtered_dataset = filters_widget.get_filtered_dataset()
        filters_widget.update_state_from_dataset(filtered_dataset)
        if filtered_dataset.shape[0] > 200:
            return
        self.state["filtered_widget"].update_state_from_dataset(filtered_dataset)

    def _stage_action(self, objs, change):  # pylint: disable=unused-argument
        staging_widget = objs[0]
        to_agg = self.state["filtered_widget"].get_selected_dataset()
        agg_params = staging_widget.get_state()
        queries_to_add = list(expand_state_into_queries(to_agg, agg_params))
        self.state["staged_widget"].add_blocks_from_queries(queries_to_add)

    def _rebuild_one_block_action(self, objs, change):
        block_widget = self._is_rebuild_one_action(objs, change)
        if block_widget is None:
            return
        cfg = block_widget.get_query()
        fig, ax = plt.subplots()
        with tempfile.NamedTemporaryFile("r") as dataset:
            write_dataset_by_query(self.datasets, cfg, dataset.name)
            plot_by_query(ax, dataset.name, cfg)
        plt.close()
        with block_widget.capture_output():
            clear_output()
            display(fig)

    @staticmethod
    def _is_rebuild_one_action(objs, change):
        block_widget = None
        for obj in objs:
            if isinstance(obj, BlockWidget):
                block_widget = obj
                break
        else:
            return None
        if block_widget.state["rebuild_button"] is change:
            return block_widget
        return None

    def _dump_state_action(self, objs, change):  # pylint: disable=unused-argument
        state_mgmt_widget = self.state["state_mgmt_widget"]
        if change is not state_mgmt_widget.state["dump_state_button"]:
            return
        current_state = self.state["staged_widget"].get_state()
        state_mgmt_widget.set_state(current_state)

    def _stage_state_action(self, objs, change):  # pylint: disable=unused-argument
        state_mgmt_widget = self.state["state_mgmt_widget"]
        if change is not state_mgmt_widget.state["stage_state_button"]:
            return
        current_state = state_mgmt_widget.get_state()
        self.state["staged_widget"].add_blocks_from_queries(current_state)
        state_mgmt_widget.clear_state()
