import pyspark
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import FloatType, BooleanType
spark = SparkSession.builder.getOrCreate()

# change this to location of pums CSV
pums_path = "../../../../dp-test-datasets/data/PUMS_california_demographics_1000/data.csv"

pums = spark.read.load(pums_path, format="csv", sep=",",inferSchema="true", header="true")

pums = pums.withColumn("income", col("income").cast(FloatType()))
pums = pums.withColumn("married", col("married").cast(BooleanType()))

pums.createOrReplaceTempView("PUMS")
pums.persist()

n = pums.count()  # count rows to force fast fail if file doesn't parse

print("Registered table PUMS with {0} rows.".format(n))
