from pyspark.sql import SparkSession
import time

spark = SparkSession.builder \
    .appName("SparkWordSlowCountBatch") \
    .getOrCreate()

sc = spark.sparkContext

lines = sc.textFile("/opt/bitnami/spark/data/input.txt")

counts = (
    lines.flatMap(lambda line: line.split())
         .map(lambda word: (word, 1))
         .reduceByKey(lambda a, b: a + b)
)

# ACTION 1 – forces a job
counts.count()

# Sleep so UI stays visible
print("Sleeping so Spark UI can be inspected...")
time.sleep(160)

# ACTION 2 – second job
counts.saveAsTextFile("/opt/bitnami/spark/data/output_result")

spark.stop()
