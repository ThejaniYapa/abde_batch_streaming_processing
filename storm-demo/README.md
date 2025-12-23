## Start the Cluster
docker-compose up -d --build


## Verify containers:
docker ps


Access:
Storm UI → http://localhost:8080

# Submitting Your Python Topology (Streamparse)
## Option A: Submit from Host

Install Streamparse on your host machine, then:
'''
sparse submit wordcount_topology
'''

Nimbus will distribute workers across:
supervisor1
supervisor2

## Option B: Submit from Inside Nimbus Container
docker exec -it storm-nimbus bash
pip install streamparse
sparse --help

cd /storm-topologies
sparse submit wordcount_topology

# Simulating Streaming Data 

## Option 1: Time-based Spout 
python code:
def next_tuple(self):
    self.emit([random.choice(self.sentences)])
    time.sleep(1)

## Option 2: File Tail 

Stream new lines from a growing file:

with open("/data/events.log") as f:
    f.seek(self.offset)
    line = f.readline()

## Option 3: Kafka (Industry-grade)

If you want enterprise realism, add:
Kafka broker
KafkaSpout

# Check Storm UI for event flow diagram

In Storm UI, highlight:
Topology graph : Spouts → Bolts
Parallelism : Executors per bolt
Tuple flow : Emitted / Acked counts
Latency : Shows real stream processing

