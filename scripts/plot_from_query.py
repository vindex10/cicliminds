import os
import json
import matplotlib.pyplot as plt
from cicliminds_lib.query.files import get_datasets
from cicliminds.backend import process_block_query


def main(data_dir, query):
    dataset = get_datasets(data_dir)
    fig, ax = plt.subplots()
    process_block_query(fig, ax, query, dataset, None)
    fig.savefig("figure.png")


if __name__ == "__main__":
    _data_dir = os.environ["DATA_DIR"]

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--json", help="query from json", default=None)
    parser.add_argument("-i", "--input-file", help="query from json file", default=None)
    parsed = parser.parse_args()

    if parsed.json is not None:
        _query = json.loads(parsed.json)
    elif parsed.input_file is not None:
        with open(parsed.input_file, "r") as fin:
            _query = json.load(fin)

    main(_data_dir, _query)
