# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class DatasetReadRequest(Model):
    """DatasetReadRequest.

    :param dataset_name: The name for the dataset
    :type dataset_name: str
    :param budget: Budget used by this read request
    :type budget: float
    """

    _attribute_map = {
        'dataset_name': {'key': 'dataset_name', 'type': 'str'},
        'budget': {'key': 'budget', 'type': 'float'},
    }

    def __init__(self, dataset_name=None, budget=None):
        super(DatasetReadRequest, self).__init__()
        self.dataset_name = dataset_name
        self.budget = budget
