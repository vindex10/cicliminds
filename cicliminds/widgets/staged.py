from ipywidgets import HBox, VBox, Button, Label
from cicliminds.widgets.common import ObserverWidget
from cicliminds.widgets.block import BlockWidget


class StagedWidget(ObserverWidget):
    def __init__(self):
        self.state = {}
        self.state["button_rebuild_all"] = self._get_rebuild_all_button()
        self.state["button_build_new"] = self._get_build_new_button()
        self.state["button_unstage_all"] = self._get_button_unstage_all()
        self.state["staged_list"] = VBox()
        self._block_widgets = []
        super().__init__()

    def render(self):
        staged_controls = HBox([self.state["button_rebuild_all"],
                                self.state["button_build_new"],
                                self.state["button_unstage_all"]])
        staged_widget = VBox([
            Label("Staged for plotting:"),
            staged_controls,
            self.state["staged_list"]])
        return staged_widget

    def add_blocks_from_queries(self, queries):
        rendered_blocks = []
        for query in queries:
            new_block = BlockWidget(query)
            new_block.observe(self._unstage_one_action)
            new_block.observe(self.propagate)
            rendered_blocks.append(new_block.render())
            self._block_widgets.insert(0, new_block)
        self.state["staged_list"].children = tuple(rendered_blocks[::-1]) + self.state["staged_list"].children

    def get_state(self):
        res = []
        for block in self._block_widgets:
            block_state = block.get_query()
            res.append(block_state)
        return res

    def _get_rebuild_all_button(self):
        button_rebuild_all = Button(description="Rebuild all", icon="redo", button_style="success")
        button_rebuild_all.on_click(self._rebuild_all_action)
        return button_rebuild_all

    def _get_build_new_button(self):
        button_build_new = Button(description="Build new", icon="redo", button_style="info")
        button_build_new.on_click(self._build_new_action)
        return button_build_new

    def _get_button_unstage_all(self):
        button_unstage_all = Button(description="Unstage all", icon="trash", button_style="danger")
        button_unstage_all.on_click(self._unstage_all_action)
        return button_unstage_all

    def _unstage_one_action(self, obj, change):
        block_widget = obj[0]
        if block_widget.state["unstage_button"] is not change:
            return
        block_idx = None
        for block_idx, block in enumerate(self._block_widgets):
            if block.state["unstage_button"] is change:
                break
        staged_blocks = self.state["staged_list"].children
        self.state["staged_list"].children = staged_blocks[:block_idx] + staged_blocks[block_idx+1:]
        del self._block_widgets[block_idx]

    def _rebuild_all_action(self, change):  # pylint: disable=unused-argument
        for block in self._block_widgets:
            block.state["rebuild_button"].click()

    def _build_new_action(self, change):  # pylint: disable=unused-argument
        for block in self._block_widgets:
            if block.state["output"].outputs:
                continue
            block.state["rebuild_button"].click()

    def _unstage_all_action(self, change):  # pylint: disable=unused-argument
        self._block_widgets = []
        self.state["staged_list"].children = tuple()
