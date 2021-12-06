from cicliminds.interface.query_builder.utils import list_product
from cicliminds.interface.query_builder.input_query_builder import expand_input_queries
from cicliminds.interface.query_builder.plot_query_builder import expand_plot_queries
from cicliminds.interface.query_builder.plot_query_builder import append_plot_query_defaults


def expand_state_into_queries(datasets, filter_values, agg_params):
    query_types = {
        "input_query": expand_input_queries(datasets, filter_values, agg_params),
        "plot_query": expand_plot_queries(agg_params)
    }
    combined_queries = list_product(query_types)
    yield from set_plot_query_defaults(combined_queries)


def set_plot_query_defaults(queries):
    for query in queries:
        query["plot_query"] = append_plot_query_defaults(query["input_query"], query["plot_query"])
        yield query
