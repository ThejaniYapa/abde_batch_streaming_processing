from pyspark.sql import SparkSession
import time
# Initialize Spark
spark = SparkSession.builder \
    .appName("DockerWordCount") \
    .getOrCreate()

# Load data from the shared volume
input_path = "/opt/bitnami/spark/data/input.txt"
text_file = spark.read.text(input_path).rdd.map(lambda r: r[0])

# Logic
counts = text_file.flatMap(lambda x: x.split(" ")) \
                  .map(lambda x: (x, 1)) \
                  .reduceByKey(lambda x, y: x + y)

# Save results
output_path = "/opt/bitnami/spark/data/output_result"
counts.saveAsTextFile(output_path)
time.sleep(300)  # Wait for a moment to ensure data is written
print("Check results in the 'data/output_result' folder on your host machine.")
spark.stop()