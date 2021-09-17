from copy import deepcopy
from itertools import product


from cicliminds.interface.query_builder.input_query_builder import expand_input_queries
from cicliminds.interface.query_builder.plot_query_builder import expand_plot_queries
from cicliminds.interface.query_builder.plot_query_builder import append_plot_query_defaults


def expand_state_into_queries(datasets, filter_values, agg_params):
    input_queries = expand_input_queries(datasets, filter_values, agg_params)
    plot_queries = expand_plot_queries(agg_params)
    for input_query, plot_query in product(input_queries, plot_queries):
        plot_query = append_plot_query_defaults(input_query, plot_query)
        yield {
            "input_query": deepcopy(input_query),
            "plot_query": plot_query
        }
