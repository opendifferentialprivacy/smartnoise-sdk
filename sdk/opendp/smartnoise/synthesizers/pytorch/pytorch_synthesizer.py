from functools import wraps

import numpy as np
import pandas as pd

from opendp.smartnoise.synthesizers.preprocessors.preprocessing import GeneralTransformer
from opendp.smartnoise.synthesizers.base import SDGYMBaseSynthesizer


class PytorchDPSynthesizer(SDGYMBaseSynthesizer):
    def __init__(self, epsilon, gan, preprocessor=None):
        """
        Wrapper class to unify pytorch GAN architectures with the SDGYM API.

        :param epsilon: Total epsilon used for the DP Synthesizer
        :type epsilon: float
        :param gan: A pytorch defined GAN
        :type gan: torch.nn.Module
        :param preprocessor: A preprocessor to .transform the input data and
            .inverse_transform the output of the GAN., defaults to None
        :type preprocessor: GeneralTransformer, optional
        """
        self.epsilon = epsilon
        self.gan = gan
        self.preprocessor = preprocessor

        self._data_columns = None

    def _get_training_data(self, data, categorical_columns, ordinal_columns):
        if not self.preprocessor:
            return data
        else:
            self.preprocessor.fit(data, categorical_columns, ordinal_columns)
            return self.preprocessor.transform(data)

    @wraps(SDGYMBaseSynthesizer.fit)
    def fit(self, data, categorical_columns=tuple(), ordinal_columns=tuple()):
        if isinstance(data, pd.DataFrame):
            self._data_columns = data.columns

        self.dtypes = data.dtypes

        training_data = self._get_training_data(data, categorical_columns, ordinal_columns)

        self.gan.train(
            training_data,
            categorical_columns=categorical_columns,
            ordinal_columns=ordinal_columns,
            update_epsilon=self.epsilon,
        )

    @wraps(SDGYMBaseSynthesizer.sample)
    def sample(self, n):
        synth_data = self.gan.generate(n)

        if self.preprocessor is not None:
            if isinstance(self.preprocessor, GeneralTransformer):
                synth_data = self.preprocessor.inverse_transform(synth_data, None)
            else:
                synth_data = self.preprocessor.inverse_transform(synth_data)

        if isinstance(synth_data, np.ndarray):
            synth_data = pd.DataFrame(synth_data, columns=self._data_columns)
        elif isinstance(synth_data, pd.DataFrame):
            # TODO: Add validity check
            synth_data.columns = self._data_columns
        else:
            raise ValueError("Generated data is neither numpy array nor dataframe!")

        return synth_data
