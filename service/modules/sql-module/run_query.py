import mlflow
import json
import sys

import pandas as pd

from opendp.whitenoise.client import get_dataset_client
from opendp.whitenoise.data.adapters import load_reader, load_metadata, load_dataset
from opendp.whitenoise.sql import PrivateReader
from pandasql import sqldf


if __name__ == "__main__":
    dataset_name = sys.argv[1]
    budget = float(sys.argv[2])
    query = sys.argv[3]

    with mlflow.start_run():
        dataset_document = get_dataset_client().read(dataset_name, budget)
        dataset = load_dataset(dataset_document)
        reader = load_reader(dataset_document)
        schema = load_metadata(dataset_document)
        private_reader = PrivateReader(schema, reader, budget)
        rowset = private_reader.execute(query)

        result = {"query_result": rowset}
        df = pd.DataFrame(rowset[1:], columns=rowset[0])
        with open("result.json", "w") as stream:
            json.dump(df.to_dict(), stream)
        mlflow.log_artifact("result.json")
