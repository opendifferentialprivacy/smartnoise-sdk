# SparkSQL Setup

Look at `runspark.py` and make sure the path to the PUMS CSV file is correct.  Then launch `pyspark`:

```bash
export PYTHONSTARTUP=runspark.py pyspark
pyspark
```

If you already have a different startup script specified for your Spark install, copy and paste the relevant lines from `runspark.py` to your startup script, taking care to ensure the datasets path is searchable from the location where `pyspark` will be launched. 