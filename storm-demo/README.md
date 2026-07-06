# Apache Storm Word-Count Demo (Docker + streamparse on EC2)

A self-contained [Apache Storm](https://storm.apache.org/) cluster running in Docker,
executing a Python [streamparse](https://streamparse.readthedocs.io/) topology that
performs a classic streaming word count. Everything runs on a **single EC2
instance** using Docker Compose — no Kubernetes, no managed services.

```
             ┌──────────┐
             │ Storm UI │  → http://<ec2-public-ip>:8080
             └────┬─────┘
                  │
            ┌─────▼─────┐
            │  Nimbus   │  (Topology scheduler + Thrift API on :6627)
            └─────┬─────┘
                  │
        ┌─────────▼─────────┐
        │    Zookeeper      │  (Cluster coordination / state)
        └─────────┬─────────┘
                  │
     ┌────────────▼────────────┐
     │      Supervisor          │  runs the Python spout/bolt workers
     │  (Workers / Executors)   │
     └─────────────────────────┘
```

---

## Table of contents

1. [What this demo does](#1-what-this-demo-does)
2. [How the pieces fit together](#2-how-the-pieces-fit-together)
3. [Repository layout](#3-repository-layout)
4. [Prerequisites](#4-prerequisites)
5. [Provision the EC2 instance](#5-provision-the-ec2-instance)
6. [Install Docker + Compose](#6-install-docker--compose)
7. [Get the code onto the box](#7-get-the-code-onto-the-box)
8. [Start the cluster](#8-start-the-cluster)
9. [Submit the topology](#9-submit-the-topology)
10. [Verify it's working](#10-verify-its-working)
11. [Manage the topology](#11-manage-the-topology)
12. [Tear down](#12-tear-down)
13. [Local-mode fallback](#13-local-mode-fallback-no-cluster)
14. [How submission actually works](#14-how-submission-actually-works)
15. [Troubleshooting](#15-troubleshooting)
16. [Version matrix](#16-version-matrix)

---

## 1. What this demo does

The topology ([`storm_wordcount/topologies/wordcount_topology.py`](storm_wordcount/topologies/wordcount_topology.py))
wires three Python components into a streaming DAG:

| Component | Class | Parallelism | Job |
|-----------|-------|-------------|-----|
| Spout | `RandomSentenceSpout` | 1 | emits one random sentence per second |
| Bolt  | `SplitSentenceBolt`   | 2 | splits each sentence into words |
| Bolt  | `WordCountBolt`       | 2 | maintains a running count per word and logs `word -> count` |

Data flow:

```
RandomSentenceSpout ──"real time word count demo"──▶ SplitSentenceBolt
                                                          │
                          "real","time","word","count","demo"
                                                          ▼
                                                    WordCountBolt
                                                 (count -> 1,2,3, ...)
```

The counts are visible both in the **Storm UI** (tuple throughput per component)
and in the **worker logs** (the actual `word -> count` lines).

---

## 2. How the pieces fit together

There are **five containers**, all on a private Docker bridge network called
`storm` so they can reach each other by service name:

| Container | Image | Role |
|-----------|-------|------|
| `zookeeper` | `zookeeper:3.8` | Coordination / cluster state |
| `nimbus` | `storm-python:2.2.0` | Master: accepts topology submissions, schedules work |
| `supervisor` | `storm-python:2.2.0` | Worker host: runs the Python spout/bolt processes |
| `ui` | `storm-python:2.2.0` | Web dashboard on port 8080 |
| `submitter` | `storm-submitter:latest` | Build/submit box (JDK + Leiningen + streamparse) |

Two custom images:

- **`storm-python`** ([Dockerfile.storm-python](docker/Dockerfile.storm-python)) —
  the official `storm:2.2.0` image **plus** Python 3 and `streamparse`. The
  supervisor needs this because Storm's *multilang* protocol launches your spouts
  and bolts as **Python subprocesses**; without a Python interpreter + the
  `streamparse` runner on the node, the workers can't start.
- **`storm-submitter`** ([Dockerfile.submitter](docker/Dockerfile.submitter)) —
  a JDK + Leiningen image plus `streamparse`. It builds the topology jar and
  submits it. It is *not* part of the running cluster; it's a throwaway
  "control" box you `exec` into.

Configuration is supplied by [`docker/storm.yaml`](docker/storm.yaml), which is
mounted read-only into each Storm container at `/conf/storm.yaml`. It tells every
node where Zookeeper and Nimbus live and which worker ports the supervisor
offers.

---

## 3. Repository layout

```
storm-demo/
├── docker-compose.yml               # defines all 5 containers + network + volumes
├── docker/
│   ├── Dockerfile.storm-python      # Storm node + Python + streamparse
│   ├── Dockerfile.submitter         # JDK + Leiningen + streamparse (build/submit)
│   └── storm.yaml                   # Storm cluster configuration
└── storm_wordcount/                 # the streamparse project (mounted into submitter)
    ├── config.json                  # streamparse "environments" (defines the "docker" env)
    ├── project.clj                  # Leiningen build file (jar dependencies)
    ├── requirements.txt
    ├── topologies/
    │   └── wordcount_topology.py    # the DAG definition
    ├── src/                         # <- streamparse puts this on PYTHONPATH
    │   ├── spouts/
    │   │   └── random_sentence_spout.py
    │   └── bolts/
    │       ├── split_sentence_bolt.py
    │       └── word_count_bolt.py
    └── virtualenvs/
        └── wordcount_topology.txt   # per-topology Python deps (name matches the topology)
```

> **Why is the code under `src/`?** streamparse adds the project's `src/`
> directory to the Python path at both submit time and run time. That's what lets
> the topology use bare imports like `from spouts.random_sentence_spout import ...`
> and `from bolts.word_count_bolt import ...` without a package prefix. If you
> move the code out of `src/`, those imports break.

> **Why does the venv file's name matter?** streamparse looks for
> `virtualenvs/<topology-name>.txt`, where `<topology-name>` is the topology
> filename without `.py`. Our topology is `wordcount_topology.py`, so the file
> must be `wordcount_topology.txt`.

---

## 4. Prerequisites

- An AWS account with permission to launch EC2 instances and edit security groups.
- An SSH key pair.
- Basic familiarity with the Linux command line.

You do **not** need Java, Python, Storm, or streamparse installed on your laptop —
everything runs inside containers on the EC2 host.

---

## 5. Provision the EC2 instance

1. **Launch an instance:**
   - AMI: **Amazon Linux 2023** or **Ubuntu 22.04 LTS**.
   - Type: **`t3.large`** (2 vCPU / 8 GB) recommended. `t3.medium` (4 GB) is the
     practical minimum — the JVM-based Storm daemons plus the first Maven download
     are memory-hungry, and a `t3.micro` will thrash or OOM.
   - Storage: root volume **≥ 20 GB** (Docker images + Maven cache).
2. **Configure the Security Group** — open inbound:

   | Port | Protocol | Source | Purpose |
   |------|----------|--------|---------|
   | 22   | TCP | **your IP only** | SSH |
   | 8080 | TCP | **your IP only** | Storm UI in the browser |

   > Ports `6627` (Nimbus Thrift) and `6700–6703` (worker slots) are used only
   > *inside* the Docker network. **Do not** expose them to the internet.

3. **SSH in:**

   ```bash
   # Amazon Linux
   ssh -i your-key.pem ec2-user@<ec2-public-ip>

   # Ubuntu
   ssh -i your-key.pem ubuntu@<ec2-public-ip>
   ```

---

## 6. Install Docker + Compose

**Amazon Linux 2023**

```bash
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

**Ubuntu 22.04**

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

**Then log out and back in** (so your shell picks up the `docker` group), and
verify:

```bash
docker --version
docker compose version
```

Both commands should print a version. If `docker compose version` errors, install
the Compose plugin (Ubuntu: `sudo apt-get install -y docker-compose-plugin`).

---

## 7. Get the code onto the box

```bash
git clone <your-repo-url> abde_batch_streaming_processing
cd abde_batch_streaming_processing/storm-demo
```

Confirm you're in the right place — you should see `docker-compose.yml`:

```bash
ls
# docker  docker-compose.yml  README.md  storm_wordcount  architecture.md
```

---

## 8. Start the cluster

```bash
docker compose up -d --build
```

- `--build` builds the two custom images the first time (a few minutes).
- `-d` runs everything in the background.

**Check status:**

```bash
docker compose ps
```

Expected — five services, `nimbus`/`supervisor`/`ui`/`zookeeper` **Up**, and
`submitter` **Up** (it just idles):

```
NAME                IMAGE                    STATUS
storm-nimbus        storm-python:2.2.0       Up
storm-supervisor    storm-python:2.2.0       Up
storm-ui            storm-python:2.2.0       Up
storm-zookeeper     zookeeper:3.8            Up
storm-submitter     storm-submitter:latest   Up
```

**Watch the daemons come up cleanly:**

```bash
docker compose logs -f nimbus supervisor
# Look for "Starting Nimbus..." and "Starting supervisor..." then Ctrl-C
```

**Open the Storm UI** at `http://<ec2-public-ip>:8080`. You should see:
- **1** Nimbus (Leader),
- **1** Supervisor with **4** total slots, **4** free,
- an empty **Topology Summary** (nothing submitted yet).

✅ **Checkpoint:** cluster is healthy and idle.

---

## 9. Submit the topology

The `submitter` container has Leiningen + Python + streamparse and mounts the
project at `/app`. Build and submit from inside it:

```bash
docker compose exec submitter bash -lc "cd /app && sparse submit -e docker --wait 0"
```

- `-e docker` selects the `docker` environment from
  [`config.json`](storm_wordcount/config.json) (points streamparse at the
  `nimbus` host).
- `--wait 0` returns immediately instead of tailing.

**First run** downloads Maven/Clojure build dependencies into a cached volume, so
it can take several minutes and print a lot of `Retrieving ...` lines. Subsequent
submits are fast. A successful run ends with something like:

```
... Uploading topology jar ...
... Submitting topology 'wordcount_topology' ...
... Topology submitted successfully.
```

✅ **Checkpoint:** no Java stack trace, and the final line reports success.

---

## 10. Verify it's working

**A) In the Storm UI** (`http://<ec2-public-ip>:8080`):
- Under **Topology Summary**, `wordcount_topology` appears with status **ACTIVE**.
- Click it. Within ~30s the **Spouts** table shows the sentence spout with a
  rising *Emitted* count, and the two bolts show rising *Executed*/*Transferred*
  counts. Free slots on the cluster drop from 4.

**B) In the worker logs** — the `WordCountBolt` logs every update:

```bash
docker compose exec supervisor bash -lc 'tail -f /logs/workers-artifacts/*/*/worker.log | grep -Ei "->"'
```

You'll see a live stream of counts, e.g.:

```
storm -> 3
stream -> 3
processing -> 3
real -> 5
time -> 5
word -> 5
count -> 5
demo -> 5
```

Press Ctrl-C to stop tailing.

✅ **Checkpoint:** counts climb over time → the topology is processing the live
stream end to end.

---

## 11. Manage the topology

```bash
# list running topologies
docker compose exec submitter bash -lc "cd /app && sparse list -e docker"

# kill it (drains, then removes)
docker compose exec submitter bash -lc "cd /app && sparse kill wordcount_topology -e docker"
```

To redeploy after editing a spout/bolt: `kill`, then `submit` again. (No image
rebuild is needed for Python-only changes because the project is bind-mounted and
the code ships inside the submitted jar.)

---

## 12. Tear down

```bash
docker compose down       # stop & remove containers, keep the volumes
docker compose down -v    # also delete Storm state + the Maven cache volume
```

When you're done with the demo, **stop or terminate the EC2 instance** so you're
not billed for it.

---

## 13. Local-mode fallback (no cluster)

To sanity-check the topology logic without submitting to the cluster, streamparse
can run it in an in-process `LocalCluster`:

```bash
docker compose run --rm submitter bash -lc "cd /app && sparse run"
```

This builds and runs the topology locally and streams the output to your
terminal. Press Ctrl-C to stop. Useful for quickly validating code changes before
a real submit.

---

## 14. How submission actually works

Useful context when debugging:

1. `sparse submit` invokes **Leiningen** (`lein`) to compile
   [`project.clj`](storm_wordcount/project.clj) into an **uber-jar**. That jar
   bundles the Storm client libraries, the multilang-python adapter, and your
   Python source from `src/`.
2. streamparse then talks **Thrift directly to Nimbus** (`nimbus:6627`): it
   uploads the jar and calls `submitTopology`. No `storm` CLI is involved on the
   submitter.
3. Nimbus schedules the topology onto the **supervisor**, which starts JVM
   **workers**. Each worker launches your spout/bolt classes as **Python
   subprocesses** (`python -m streamparse.run ...`) and communicates with them
   over the multilang JSON protocol on stdin/stdout. This is why the supervisor
   image must contain Python + streamparse.

---

## 15. Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `sparse submit` can't connect to Nimbus | Run it from **inside** the `submitter` container (as shown), not from the host — only containers on the `storm` network resolve the `nimbus` hostname. |
| Storm UI won't load in the browser | Confirm port **8080** is open in the EC2 Security Group **and** scoped to your IP; confirm `storm-ui` is `Up` in `docker compose ps`. |
| Topology is ACTIVE but bolts stay at 0 / workers keep dying | Almost always a missing Python runtime on the worker. Check `docker compose logs supervisor` and the `worker.log` files. The `storm-python` image bakes in Python + streamparse; if you edited the Dockerfile, rebuild: `docker compose build supervisor && docker compose up -d supervisor`. |
| `ImportError: No module named spouts/bolts` in worker logs | The Python code must live under `storm_wordcount/src/` so streamparse puts it on the path. Don't move `src/`. |
| First `sparse submit` is extremely slow | Leiningen is downloading Maven dependencies. They're cached in the `lein-cache` volume, so later submits are quick. Don't interrupt the first one. |
| `sparse: command not found` | You're on the host, not in the container. Prefix with `docker compose exec submitter bash -lc "..."`. |
| Version mismatch / Thrift errors on submit | The Storm image (`storm:2.2.0`), the jar deps in [`project.clj`](storm_wordcount/project.clj), and `streamparse==4.1.2` are pinned to match. If you bump one, bump them together. |
| Out-of-memory / instance freezes | Use at least a `t3.medium`; `t3.large` is more comfortable. |

**Handy log commands:**

```bash
docker compose logs nimbus            # scheduler issues
docker compose logs supervisor        # worker launch issues
docker compose exec supervisor bash -lc 'ls /logs/workers-artifacts/*/*/'   # per-worker logs
```

---

## 16. Version matrix

These versions are pinned to be mutually compatible. Change them together.

| Piece | Version | Where it's set |
|-------|---------|----------------|
| Apache Storm (cluster) | 2.2.0 | [`docker/Dockerfile.storm-python`](docker/Dockerfile.storm-python) (`FROM storm:2.2.0`) |
| Apache Storm (jar deps) | 2.2.0 | [`storm_wordcount/project.clj`](storm_wordcount/project.clj) |
| streamparse | 4.1.2 | both Dockerfiles + `requirements.txt` |
| Zookeeper | 3.8 | [`docker-compose.yml`](docker-compose.yml) |
| JDK (build box) | Temurin 11 | [`docker/Dockerfile.submitter`](docker/Dockerfile.submitter) |
| Python (workers/build) | 3.x (Debian) | both Dockerfiles |
