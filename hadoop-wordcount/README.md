hadoop-multinode/
│
├── docker-compose.yml
├── Dockerfile
├── config/
│   ├── core-site.xml
│   ├── hdfs-site.xml
│   ├── yarn-site.xml
│   ├── mapred-site.xml
│   └── hadoop-env.sh
│
├── python/
│   ├── mapper.py
│   └── reducer.py
│
└── input/
    └── input.txt
## Install Docker
'''
sudo apt update
sudo apt install -y docker.io
sudo apt  install docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
<!-- sudo usermod -aG docker $USER -->
newgrp docker
'''

Verify:
'''
docker --version
'''
Create Project Directory
'''
mkdir hadoop-wordcount
cd hadoop-wordcount
'''
## Build & Start Cluster
'''
docker-compose up -d --build
'''

Check:
'''
docker ps
'''
## Make executable:
'''
chmod +x python/*.py
'''
## Prepare Input Data
echo "hello hadoop hello mapreduce hadoop" > input/input.txt

# From host (assuming mapper.py and reducer.py are in current dir)
docker cp python/mapper.py hadoop-namenode:/root/
docker cp python/reducer.py hadoop-namenode:/root/
docker cp input/input.txt hadoop-namenode:/tmp/input.txt

In NameNode:
'''
docker exec -it hadoop-namenode bash
java -version
'''
Inside container:


hdfs dfs -mkdir /input
hdfs dfs -put /tmp/input.txt /input/
hdfs dfs -ls /input


hdfs dfs -rm -r /output
ls -l /root/
hdfs dfs -ls /output
hdfs dfs -cat /output/part-00000
## Run Python MapReduce via Hadoop Streaming
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -input /input \
  -output /output \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py" \
  -file /root/mapper.py \
  -file /root/reducer.py


## View Output
hdfs dfs -cat /output/part-00000

## Monitoring (Optional)

HDFS UI: http://54.187.110.63:9870

YARN UI: curl http://127.0.0.1:8088

## Add more data
 Upload local test file (assuming test.txt exists inside container)
echo -e "hello world\nhello hadoop" > /root/test.txt
 Put file into HDFS
hdfs dfs -put /root/test.txt /input/
## Cleanup
docker-compose down -v

## Show input file on local FS
cat input/input.txt

## optimized for batch reads and writes
Upload to HDFS (Batch ingestion)
docker exec -it hadoop-namenode bash
hdfs dfs -ls /
hdfs dfs -put /input/input.txt /input
hdfs dfs -ls /input

## Submit the MapReduce Job
'''
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
-input /input \
-output /output \
-mapper python3 mapper.py \
-reducer python3 reducer.py \
-file mapper.py \
-file reducer.py
'''
This job is submitted to YARN and executed as a batch job

## Job Lifecycle in YARN UI (MOST IMPORTANT)

Open browser:

http://<EC2_IP>:8088

Check
Application ID

State: RUNNING → FINISHED

Maps running first

Reduce starts after shuffle

YARN schedules containers, allocates resources, and tracks job progress.

Check Map Phase (With Logs)
Mapper Logic (show code briefly)
print(f"{word}\t1")
Show intermediate output conceptually

Check Shuffle & Sort (Key Batch Concept)

“After the map phase, Hadoop performs a global shuffle and sort.
All values for the same key are grouped together before reduction.”

Visual:

hello → [1,1]
hadoop → [1,1]

Mention:

Network-heavy

Blocking phase

Only possible because data is finite (batch)

Check Reduce Phase

Reducer logic:

current_count += count


Say:

“Reducers aggregate all values per key and write final results back to HDFS.”

Final Batch Output
hdfs dfs -cat /output/part-00000

The output is persisted in HDFS — batch processing always produces durable output.

Failure Recovery (If Time)

Kill a NodeManager:

docker stop hadoop-nodemanager
YARN reschedules failed tasks — batch jobs are fault-tolerant.”

Restart:

docker start hadoop-nodemanager

## Troubleshooting
If you’re using Ubuntu, the instance may have ufw enabled:

sudo ufw status


If it’s active, allow port 8088:

sudo ufw allow 8088/tcp
sudo ufw reload