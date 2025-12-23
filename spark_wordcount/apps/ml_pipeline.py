from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import Tokenizer, HashingTF
from pyspark.ml.classification import LogisticRegression
import time

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("SparkMLPipeline") \
    .getOrCreate()

# 1. Prepare training data (Labeled: 1.0 for positive/spam, 0.0 for negative/ham)
training = spark.createDataFrame([
    (0, "spark is great for big data", 1.0),
    (1, "i love working with python", 1.0),
    (2, "the weather is sunny today", 0.0),
    (3, "docker makes deployment easy", 0.0)
], ["id", "text", "label"])

# 2. Define Pipeline Stages
tokenizer = Tokenizer(inputCol="text", outputCol="words")
hashingTF = HashingTF(inputCol=tokenizer.getOutputCol(), outputCol="features")
lr = LogisticRegression(maxIter=10, regParam=0.01)

# 3. Build the Pipeline
pipeline = Pipeline(stages=[tokenizer, hashingTF, lr])

# 4. Train the Model
model = pipeline.fit(training)

# 5. Prepare test data
test = spark.createDataFrame([
    (4, "spark python"),
    (5, "sunny weather")
], ["id", "text"])

# 6. Make Predictions
prediction = model.transform(test)
selected = prediction.select("id", "text", "probability", "prediction")
for row in selected.collect():
    rid, text, prob, pred = row
    print(f"ID: {rid} - Text: {text} --> Prediction: {pred}")

# Keep alive to check the DAG
print("Pipeline complete. UI alive at http://localhost:4040 for 5 mins.")
time.sleep(300)

spark.stop()