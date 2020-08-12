from opendp.whitenoise.evaluation.privacyalgorithm._base import PrivacyAlgorithm
from opendp.whitenoise.evaluation.params._dataset_params import DatasetParams
from opendp.whitenoise.evaluation.params._privacy_params import PrivacyParams
from opendp.whitenoise.evaluation.params._eval_params import EvaluatorParams
from opendp.whitenoise.evaluation.params._benchmark_params import BenchmarkParams
from opendp.whitenoise.evaluation.metrics._metrics import Metrics
from opendp.whitenoise.evaluation.metrics._benchmark_metrics import BenchmarkMetrics
from opendp.whitenoise.evaluation.benchmarking._base import Benchmarking
from opendp.whitenoise.evaluation.evaluator._dp_evaluator import DPEvaluator

class DPBenchmarking(Benchmarking):
	"""
	Implement interface to benchmark DP implementations to interface with tests available
	in DP evaluator. Evaluator tests for various properties of DP implementation
	like privacy, accuracy, utility and bias. Benchmark will run the evaluator
	for multiple parameters like epsilon, dataset size etc. 
	"""
	def benchmark(self, bp : BenchmarkParams) -> [BenchmarkMetrics]:
		"""
		Benchmarks properties of privacy algorithm DP implementations using metrics
			- Privacy Promise
			- Accuracy Promise
			- Utility Promise
			- Bias Promise
		
		Returns a benchmark metrics object
		"""
		benchmark_res = []
		ev = DPEvaluator()
		# Iterate through the PrivacyAlgorithm instance and algorithms in it
		for pa, algorithm in bp.pa_algorithms.items():
			# Iterate through the neighboring datasets to test on the algorithms
			for d1_d2 in bp.d1_d2_list:
				# Iterate through the privacy param configurations
				for pp in bp.privacy_params_list:
					d1 = d1_d2[0]
					d2 = d1_d2[1]
					private_algorithm = algorithm[0]
					exact_algorithm = algorithm[1]
					dataset_params = DatasetParams(len(d1))
					bm = BenchmarkMetrics(pa, private_algorithm, exact_algorithm, pp, dataset_params, bp.eval_params, Metrics())
					bm.key_metrics = ev.evaluate(d1, d2, pa, private_algorithm, exact_algorithm, pp, bp.eval_params)
					benchmark_res.append(bm)
		return benchmark_res