from cicliminds.interface.query_builder.utils import list_product
from cicliminds.interface.query_builder.filter_expander import expand_filters
from cicliminds.interface.query_builder.basic_expanders import blocks_to_json_like
from cicliminds.interface.query_builder.basic_expanders import expand_field


def expand_input_queries(datasets, filter_values, agg_params):
    data_sources = {
            "datasets": expand_filters(datasets, filter_values, agg_params),
            "model_weights": expand_model_weights(agg_params)
    }
    normalized_data_sources = normalize_data_source_queries(data_sources)
    yield from list_product(normalized_data_sources)


def normalize_data_source_queries(data_sources):
    res = {}
    for source, queries in data_sources.items():
        res[source] = list(blocks_to_json_like(queries))
    return res


def expand_model_weights(agg_params):
    model_weights = agg_params["model_weights"] or []
    if model_weights and agg_params["aggregate_model_weights"]:
        model_weights = [[i] for i in model_weights]
    else:
        model_weights = [model_weights]
    weighted_queries = expand_field([{}], "model_weights", model_weights)
    yield from weighted_queries
