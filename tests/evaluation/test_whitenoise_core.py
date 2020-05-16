import logging
test_logger = logging.getLogger("whitenoise-core-test-logger")

import sys
import subprocess
import os
import pytest
import pandas as pd
from opendp.whitenoise.evaluation.dp_verification import DPVerification
from opendp.whitenoise.evaluation.exploration import Exploration
from opendp.whitenoise.evaluation.aggregation import Aggregation
import opendp.whitenoise.core as wn

root_url = subprocess.check_output("git rev-parse --show-toplevel".split(" ")).decode("utf-8").strip()
dv = DPVerification(dataset_size=1000, csv_path=os.path.join(root_url, "service", "datasets"))
test_csv_path = os.path.join(root_url, "service", "datasets", "evaluation", "PUMS_1000.csv")
test_csv_names = ["age", "sex", "educ", "race", "income", "married"]

df = pd.read_csv(test_csv_path)
actual_mean = df['race'].mean()
actual_var = df['educ'].var()
actual_moment = df['race'].skew()
actual_covariance = df['age'].cov(df['married'])

class TestWhitenoiseCore:
    def test_dp_whitenoise_core_mean_pums(self):
        logging.getLogger().setLevel(logging.DEBUG)
        dp_res, bias_res = dv.whitenoise_core_test(test_csv_path,
                                                   test_csv_names,
                                                   wn.dp_mean,
                                                   'race',
                                                   "FLOAT",
                                                   epsilon=.65,
                                                   actual=actual_mean,
                                                   data_lower=0.,
                                                   data_upper=100.,
                                                   data_n=1000)
        test_logger.debug("Result of DP Predicate Test on WhiteNoise-Core Mean: " + str(dp_res))
        test_logger.debug("Result of Bias Test on WhiteNoise-Core Mean: " + str(bias_res))
        assert(dp_res)
        assert(bias_res)

    def test_dp_whitenoise_core_var_pums(self):
        logging.getLogger().setLevel(logging.DEBUG)
        dp_res, bias_res = dv.whitenoise_core_test(test_csv_path,
                                                   test_csv_names,
                                                   wn.dp_variance,
                                                   'educ',
                                                   "FLOAT",
                                                   epsilon=.15,
                                                   actual=actual_var,
                                                   data_lower=0.,
                                                   data_upper=12.,
                                                   data_n=1000)
        test_logger.debug("Result of DP Predicate Test on WhiteNoise-Core Variance: " + str(dp_res))
        test_logger.debug("Result of Bias Test on WhiteNoise-Core Variance: " + str(bias_res))
        assert(dp_res)
        assert(bias_res)

    def test_dp_whitenoise_core_moment_pums(self):
        logging.getLogger().setLevel(logging.DEBUG)
        dp_res, bias_res = dv.whitenoise_core_test(test_csv_path,
                                                   test_csv_names,
                                                   wn.dp_moment_raw,
                                                   'race',
                                                   "FLOAT",
                                                   epsilon=.15,
                                                   actual=actual_moment,
                                                   data_lower=0.,
                                                   data_upper=100.,
                                                   data_n=1000,
                                                   order=3)
        test_logger.debug("Result of DP Predicate Test on WhiteNoise-Core Moment: " + str(dp_res))
        test_logger.debug("Result of Bias Test on WhiteNoise-Core Moment: " + str(bias_res))
        assert(dp_res)
        assert(bias_res)

    def test_dp_whitenoise_core_covariance_pums(self):
        logging.getLogger().setLevel(logging.DEBUG)
        dp_res, bias_res = dv.whitenoise_core_test(test_csv_path,
                                                   test_csv_names,
                                                   wn.dp_covariance,
                                                   'age',
                                                   'married',
                                                   "FLOAT",
                                                   actual = actual_covariance,
                                                   epsilon=.15,
                                                   left_n=1000,
                                                   right_n=1000,
                                                   left_lower=0.,
                                                   left_upper=1.,
                                                   right_lower=0.,
                                                   right_upper=1.)
        test_logger.debug("Result of DP Predicate Test on WhiteNoise-Core Covariance: " + str(dp_res))
        test_logger.debug("Result of Bias Test on WhiteNoise-Core Covariance: " + str(bias_res))
        assert(dp_res)
        assert(bias_res)
