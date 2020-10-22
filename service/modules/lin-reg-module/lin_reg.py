import mlflow
import mlflow.sklearn
import json
import sys
import logging

import numpy as np
import pandas as pd

from opendp.smartnoise.client import get_dataset_client
from opendp.smartnoise.data.adapters import load_metadata, load_dataset

from opendp.smartnoise.models import DPLinearRegression
#  TODO add a test for both this and log_reg module in smoke tests


if __name__ == "__main__":
    dataset_name = sys.argv[1]
    budget = float(sys.argv[2])
    # We expect the next two inputs in the following format: json.dumps([col, names, here]) (e.g. '["a","b"]')
    x_features = json.loads(sys.argv[3])
    y_targets = json.loads(sys.argv[4])

    with mlflow.start_run(run_name="diffpriv_covariance_linreg"):
        try:
            # Log mlflow attributes for mlflow UI
            mlflow.log_param("dataset_name", dataset_name)
            mlflow.log_param("budget", budget)
            mlflow.log_param("x_features", x_features)
            mlflow.log_param("y_targets", y_targets)
        except:
            pass  # retries and failures do not work with params


        dataset_document = get_dataset_client().read(dataset_name, budget)
        dataset = load_dataset(dataset_document)
        schema = load_metadata(dataset_document)

        # Find X and y values from dataset
        X = dataset[x_features]
        y = dataset[y_targets]

        # Find ranges for X and ranges for y
        table_name = dataset_name + "." + dataset_name
        x_range_dict = dict([(col, schema.m_tables[table_name][col].maxval - schema.m_tables[table_name][col].minval)
                             for col in x_features])
        y_range_dict = dict([(col, schema.m_tables[table_name][col].maxval - schema.m_tables[table_name][col].minval)
                             for col in y_targets])
        x_range = pd.Series(data=x_range_dict)
        y_range = pd.Series(data=y_range_dict)

        data_range = pd.DataFrame([[schema.m_tables[table_name][col].minval, schema.m_tables[table_name][col].maxval] for col in
                                   (x_features+y_targets)], index=(x_features+y_targets)).transpose()

        # Try multiple times because sometimes noise makes cov matrix not positive definite
        model = None
        for i in range(10):
            try:
                model = DPLinearRegression().fit(X, y, data_range, budget)
            except:
                pass

        if model is None:
            raise Exception("The added noise made your covariance matrix no longer positive definite.")

        # Save model for access through mlflow ui
        mlflow.sklearn.log_model(model, "model")

        results = {
            "run_id": mlflow.active_run().info.run_id,
            "model_name": "diffpriv_linreg"
        }
        with open("result.json", "w") as stream:
            json.dump(results, stream)
        mlflow.log_artifact("result.json")
