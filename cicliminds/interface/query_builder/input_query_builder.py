from cicliminds.interface.query_builder.filter_expander import expand_filters
from cicliminds.interface.query_builder.basic_expanders import blocks_to_json_like


def expand_input_queries(datasets, filter_values, agg_params):
    input_queries_with_masks = expand_filters(datasets, filter_values, agg_params)
    input_queries = (block for block, _ in input_queries_with_masks)
    yield from blocks_to_json_like(input_queries)
