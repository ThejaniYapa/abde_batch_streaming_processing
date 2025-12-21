#!/bin/bash
# Set environment variables
export HADOOP_HOME=/root/hadoop
export PATH=$HADOOP_HOME/bin:$PATH

# Submit Hadoop streaming job
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
-input /input/$(date -d "yesterday" +\%Y-\%m-\%d) \
-output /output/$(date -d "yesterday" +\%Y-\%m-\%d) \
-mapper python3 /root/mapper.py \
-reducer python3 /root/reducer.py \
-file /root/mapper.py \
-file /root/reducer.py
