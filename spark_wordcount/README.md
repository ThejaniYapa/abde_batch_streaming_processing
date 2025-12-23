spark-wordcount/
├── docker-compose.yml
├── Dockerfile
├── wordcount.py
└── data/
    └── input.txt

# Build and Run the Docker Cluster
## Navigate to project folder
cd spark-wordcount

## Start cluster in detached mode
docker-compose up -d --build

verify Cluster
docker ps

docker cp app/wordcount.py spark-master:/opt/spark-apps/test.py
## Open Spark UI:

http://52.11.63.33:8080
http://localhost:8080

## Submit WordCount Job
docker exec -it spark-master bash
ls apps/
ls data/

## Submit job
spark-submit --master spark://spark-master:7077 /opt/bitnami/spark/apps/wordcount.py
spark-submit --master spark://spark-master:7077 /opt/bitnami/spark/apps/test.py
spark-submit --master spark://spark-master:7077 /opt/bitnami/spark/apps/ml_pipeline.py
## Notes for Isolation & Cleanup

The cluster is fully isolated inside spark-network.
Containers are named spark-master, spark-worker-1, spark-worker-2.

### To stop and remove the cluster:

docker-compose down


### To rebuild the containers after code changes:

docker-compose build --no-cache
docker-compose up -d

## troubleshoot

docker exec -it spark-master netstat -tulpn | grep 8080