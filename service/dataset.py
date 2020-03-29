#%%
import os
import json
import yaml

from flask import abort
from secrets import get as secrets_get
from secrets import put as secrets_put


with open(os.path.join(os.path.dirname(__file__), "datasets", "dataverse", "demo_dataverse.yml"), "r") as stream:
    demo_dataverse_schema = json.dumps(yaml.safe_load(stream))

DATASETS = {"example": {
                        "dataset_type": "csv_details",
                        "csv_details": {
                            "local_path": os.path.join(os.path.dirname(__file__), "datasets", "example.csv")
                        },
                        "budget":3.0},
            "iris": {
                        "dataset_type": "csv_details",
                        "csv_details": {
                            "local_path": os.path.join(os.path.dirname(__file__), "datasets", "iris.csv")
                        },
                        "budget":300.0},
            "demo_dataverse": {
                        "dataset_type": "dataverse_details",
                        "dataverse_details": {
                            "local_metadata_path": os.path.join(os.path.dirname(__file__),
                                                                "datasets",
                                                                "dataverse",
                                                                "demo_dataverse.yml"),
                            "host": "https://demo.dataverse.org/api/access/datafile/395811",
                            "schema": demo_dataverse_schema
                        },
                        "budget":300.0}}


KNOWN_DATASET_TYPE_KEYS = ["csv_details", "dataverse_details"]

def read(dataset_request):
    """Get information needed to load the dataset

    :param info: The dataset to read and budget to use.
    :type info: dict {"dataset_name": str, "budget":int}
    :return: A dataset document that contains the type and info of the dataset
    :rtype: dict{"dataset_type": str, dataset_key: dict}
    """
    dataset_name = dataset_request["dataset_name"]

    if dataset_name not in DATASETS:
        abort(400, "Dataset id {} not found.".format(dataset_name))

    dataset = DATASETS[dataset_name]

    # Validate the secret, extract token
    try:
        if dataset["dataset_type"] == "dataverse_details":
            dataset[dataset["dataset_type"]]["token"] = secrets_get(name="dataverse:{}".format(dataset_request["dataset_name"]))["value"]
    except:
        # TODO: Temp fix for testing - Do better cleanup if secret missing
        # dataset["dataset_type"]["token"] = {'name':dataset_name,'value':42}
        pass

    # Check/Decrement the budget before returning dataset
    adjusted_budget = dataset["budget"] - dataset_request["budget"]
    if adjusted_budget >= 0.0:
        dataset["budget"] = adjusted_budget
    else:
        abort(412, "Not enough budget for read. Remaining budget: {}".format(dataset_name))

    return dataset

#%%
def register(dataset):
    dataset_name = dataset["dataset_name"]

    if dataset_name in DATASETS:
        abort(401, "Dataset id {} already exists. Identifies must be unique".format(dataset_name))

    # Add key if possible
    if dataset["dataset_type"] not in KNOWN_DATASET_TYPE_KEYS:
        abort(402, "Given type was {}, must be either csv_details or dataverse_details.".format(str(dataset["dataset_type"])))

    # Add budget if possible 
    if dataset["budget"]:
        if dataset["budget"] <= 0.0: abort(403, "Budget must be greater than 0.")
    else:
        abort(403, "Must specify a budget")

    # Type specific registration
    if dataset["dataset_type"] == "csv_details":
        # Local dataset
        if not os.path.isfile(dataset["csv_details"]["local_path"]):
            abort(406, "Local file path {} does not exist.".format(str(dataset["dataset_type"])))
    elif dataset["dataset_type"] == "dataverse_details":
        # Validate Json schema
        if dataset["dataverse_details"]["schema"]:
            try:
                dataset["dataverse_details"]["schema"] = json.dumps(dataset["dataverse_details"]["schema"])
            except:
                abort(407, "Schema {} must be valid json.".format(str(dataset["dataverse_details"]["schema"])))
        else:
            abort(414, "Schema must exist.")

        # Specify host
        if not dataset["dataverse_details"]["host"]:
            abort(408, "Must specify host, {} is malformed.".format(str(dataset["dataverse_details"]["host"])))

    # TODO: Add support for other types of datasets


    # If everything looks good, register it.
    DATASETS[dataset_name] = dataset

    print(DATASETS.keys())

    return {"result":dataset_name}

