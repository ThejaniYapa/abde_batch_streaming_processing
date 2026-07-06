# Apache Airflow — A Hands-On Introduction

A ready-to-run [Apache Airflow](https://airflow.apache.org/) demo built for a
**graduate lecture / lab session**. It spins up a real Airflow cluster in Docker
and ships four progressively richer DAGs that tour Airflow's core capabilities —
from "hello world" to dynamic, data-driven pipelines.

> **Goal:** in ~30 minutes a student goes from *never having seen Airflow* to
> triggering pipelines, reading logs, following data between tasks, and
> understanding when/why you'd reach for Airflow.

---

## Table of contents

1. [What is Airflow (and when to use it)](#1-what-is-airflow-and-when-to-use-it)
2. [Core vocabulary](#2-core-vocabulary)
3. [What's in this demo](#3-whats-in-this-demo)
4. [The four demo DAGs](#4-the-four-demo-dags)
5. [How this Docker stack is wired](#5-how-this-docker-stack-is-wired)
6. [Prerequisites](#6-prerequisites)
7. [Quick start](#7-quick-start)
8. [A guided classroom walkthrough](#8-a-guided-classroom-walkthrough)
9. [The Airflow UI — what to point at](#9-the-airflow-ui--what-to-point-at)
10. [Useful CLI commands](#10-useful-cli-commands)
11. [Editing / adding your own DAG](#11-editing--adding-your-own-dag)
12. [Troubleshooting](#12-troubleshooting)
13. [Teardown](#13-teardown)
14. [Running on EC2 (optional)](#14-running-on-ec2-optional)

---

## 1. What is Airflow (and when to use it)

**Apache Airflow is a platform to author, schedule, and monitor workflows as
code.** You describe a pipeline as a Python file; Airflow figures out the order,
runs the steps on a schedule (or on demand), retries failures, and gives you a
web UI to observe everything.

Reach for Airflow when you have **batch workflows with dependencies** — e.g.
"every night: pull yesterday's data, clean it, load it into the warehouse, then
refresh the dashboard." It is *not* a stream processor (that's Storm/Flink/Kafka)
and *not* a heavy compute engine (that's Spark) — Airflow is the **orchestrator**
that tells those systems *what to run and when*, and reacts when something breaks.

| Airflow is good at | Airflow is NOT for |
|--------------------|--------------------|
| Scheduling batch jobs | Low-latency / real-time streaming |
| Managing task dependencies (DAGs) | Heavy in-process data crunching (delegate to Spark, SQL, etc.) |
| Retries, alerting, backfills | Sub-second event handling |
| Orchestrating across systems (S3, Spark, DBs, APIs) | Being a message queue |

## 2. Core vocabulary

| Term | Meaning |
|------|---------|
| **DAG** | *Directed Acyclic Graph* — one workflow. Tasks are nodes, dependencies are edges, no cycles allowed. |
| **Task** | A single node of work in a DAG. |
| **Operator** | A template that *creates* a task — e.g. `BashOperator`, `PythonOperator`. |
| **TaskFlow API** | The modern `@dag`/`@task` decorator style; plain Python functions become tasks. |
| **Scheduler** | The component that parses DAGs and decides which tasks to run when. |
| **Executor** | *How/where* tasks actually run. We use **LocalExecutor** (subprocesses). Production often uses Celery or Kubernetes. |
| **DAG Run** | One execution of a DAG for a given date/interval. |
| **Task Instance** | One task within one DAG Run (has a state: success, failed, skipped, ...). |
| **XCom** | "Cross-communication" — small pieces of data passed between tasks. |
| **Trigger Rule** | The condition under which a task fires given its parents' states (default: all parents succeeded). |
| **Backfill / Catchup** | Running a DAG for past intervals. We disable it (`catchup=False`). |

## 3. What's in this demo

```
airflow/
├── docker-compose.yml           # the Airflow stack (Postgres + init + scheduler + webserver)
├── Dockerfile                   # official Airflow image + pandas
├── requirements.txt             # extra Python libs (pandas)
├── .env                         # AIRFLOW_UID for correct file permissions
├── dags/                        # ← the workflows (this is what you teach from)
│   ├── 01_hello_airflow.py      # basics: operators + dependencies
│   ├── 02_taskflow_etl.py       # TaskFlow API + XComs + a pandas ETL
│   ├── 03_branching_parallel.py # parallel fan-out, branching, trigger rules
│   └── 04_dynamic_task_mapping.py # runtime fan-out with .expand()
├── data/
│   ├── input/sales.csv          # sample input for the ETL DAG
│   └── output/                  # sales_summary.csv is written here
├── logs/                        # task logs (also viewable in the UI)
└── plugins/                     # (empty) custom plugins would live here
```

## 4. The four demo DAGs

Teach them **in order** — each adds one new concept.

| # | DAG | New concepts introduced | Look for... |
|---|-----|-------------------------|-------------|
| 01 | **`01_hello_airflow`** | DAG structure, `BashOperator` + `PythonOperator`, `>>` dependencies, `retries`, `schedule` | A simple 3-task chain going green |
| 02 | **`02_taskflow_etl`** | TaskFlow API (`@dag`/`@task`), automatic **XComs**, a real pandas ETL, reading/writing mounted files | `data/output/sales_summary.csv` appears; inspect each task's XCom |
| 03 | **`03_branching_parallel`** | Parallel fan-out, fan-in join, `BranchPythonOperator`, **trigger rules** | The diamond graph; one branch runs, the other is greyed-out (skipped) |
| 04 | **`04_dynamic_task_mapping`** | Runtime fan-out with `.expand()` (map→reduce) | `process` renders as mapped instances `[0] [1] [2]...` |

## 5. How this Docker stack is wired

Four containers, kept intentionally small for teaching:

| Container | Role |
|-----------|------|
| `airflow-postgres` | **Metadata database** — Airflow's source of truth (DAG states, runs, XComs). |
| `airflow-init` | **One-shot bootstrap** — runs DB migrations and creates the `admin` login, then exits. |
| `airflow-scheduler` | **The brain** — continuously parses `dags/`, schedules tasks, and (with LocalExecutor) runs them as subprocesses. |
| `airflow-webserver` | **The UI** — Flask app on port 8080. |

We use the **LocalExecutor**, so there's no Redis/Celery/worker fleet — simpler
to explain and lighter to run. The `dags/`, `data/`, `logs/`, and `plugins/`
folders are **bind-mounted**, so editing a DAG on your machine is picked up live
(no rebuild needed).

## 6. Prerequisites

- **Docker** and the **Docker Compose plugin** (`docker compose version` works).
  Docker Desktop on macOS/Windows, or Docker Engine on Linux.
- **~4 GB RAM** free for Docker (Airflow's official minimum). On Docker Desktop:
  Settings ▸ Resources ▸ Memory.
- No local Python/Airflow install needed — everything runs in containers.

## 7. Quick start

From this `airflow/` folder:

```bash
# (Linux only) make container-written files owned by you:
#   echo "AIRFLOW_UID=$(id -u)" > .env

# 1. Build the image and start the stack
docker compose up -d --build

# 2. Watch it come up (init runs first, then scheduler + webserver)
docker compose ps
```

Wait until `airflow-webserver` shows **healthy** (30–60s), then open:

**http://localhost:8080** — log in with **`admin` / `admin`**.

You'll land on the DAGs list showing the four demo DAGs, all **paused**.

> First `docker compose up` builds the custom image (installs pandas) and
> initializes the database — give it a couple of minutes. Later starts are fast.

## 8. A guided classroom walkthrough

A suggested 25–30 min live flow:

1. **Orient (2 min).** Show the DAGs list. Point out the four demo DAGs, the
   pause toggle, schedule, tags, and "last run" columns.
2. **DAG 01 — the basics (5 min).**
   - Open `01_hello_airflow`, switch to the **Code** tab, walk the file:
     `DAG(...)`, the two operators, `print_date >> greet >> done`.
   - Unpause it, click ▶ **Trigger DAG**. Switch to **Graph** and watch tasks
     turn green left-to-right.
   - Click the `greet` task ▸ **Logs** to show `Hello from Airflow!`.
   - Mention `retries=2` — Airflow would auto-retry a failed task.
3. **DAG 02 — TaskFlow ETL + XComs (7 min).**
   - Show the `@task` functions. Emphasize: `load(transform(extract()))` builds
     the whole dependency graph from ordinary function calls.
   - Trigger it. Then open `transform` ▸ **XCom** to *see the data* that moved
     between tasks.
   - On the host, show the produced file: `cat data/output/sales_summary.csv`.
4. **DAG 03 — branching & parallelism (6 min).**
   - Trigger it. In **Graph**, show the three `pull_source_*` tasks running at
     once (fan-out), the `combine` join (fan-in), and that exactly **one** of
     `weekday_report` / `weekend_report` ran while the other is **skipped**
     (grey). Explain the trigger rule that lets `finish` still run.
5. **DAG 04 — dynamic mapping (5 min).**
   - Trigger it. Show `process` expanding into mapped instances `[0..4]`, then
     `summarize` reducing them. Tie it back to map→reduce.
6. **Wrap-up (2 min).** Recap: workflows-as-code, the scheduler, retries,
   XComs, the UI for observability.

## 9. The Airflow UI — what to point at

| UI area | What it shows |
|---------|---------------|
| **DAGs list** | All DAGs, pause toggles, schedule, recent run status. |
| **Grid** | Runs (columns) × tasks (rows) as a colored grid — the fastest health view. |
| **Graph** | The DAG topology for a run; colors = task states. Best for teaching dependencies. |
| **Code** | The exact Python source — reinforces "workflows are code". |
| **Logs** (per task) | stdout/stderr of a task instance — where your `print()`s land. |
| **XCom** (per task) | Data a task returned/pushed — great for DAG 02. |
| **Trigger DAG** ▶ | Manually start a run (optionally with a config JSON). |

## 10. Useful CLI commands

Run Airflow's CLI inside the scheduler container:

```bash
# list all DAGs
docker compose exec airflow-scheduler airflow dags list

# show a DAG's tasks
docker compose exec airflow-scheduler airflow tasks list 02_taskflow_etl

# trigger a run from the CLI
docker compose exec airflow-scheduler airflow dags trigger 01_hello_airflow

# run a single task for a date without a full DAG run (great for debugging)
docker compose exec airflow-scheduler \
  airflow tasks test 02_taskflow_etl extract 2024-01-01
```

## 11. Editing / adding your own DAG

The `dags/` folder is mounted into the containers, so:

1. Drop a new `my_dag.py` into `dags/`.
2. The scheduler rescans every ~15s; your DAG appears in the UI shortly after.
3. If it doesn't show up, it usually has an import/parse error — check:
   ```bash
   docker compose exec airflow-scheduler airflow dags list-import-errors
   ```

## 12. Troubleshooting

| Symptom | Fix |
|---------|-----|
| UI not loading at :8080 | Wait for `airflow-webserver` to be **healthy** (`docker compose ps`). First boot takes ~1 min. |
| Can't log in | Credentials are `admin` / `admin`. If the user wasn't created, re-run init: `docker compose up airflow-init`. |
| A new DAG doesn't appear | Parse error — run `airflow dags list-import-errors` (see §11). |
| Tasks stuck in "queued"/"no status" | The scheduler isn't running. `docker compose ps`; check `docker compose logs airflow-scheduler`. |
| `Permission denied` writing logs (Linux) | Set `AIRFLOW_UID` to your user: `echo "AIRFLOW_UID=$(id -u)" > .env` then `docker compose up -d`. |
| Containers get OOM-killed / very slow | Give Docker ≥ 4 GB RAM (Docker Desktop ▸ Settings ▸ Resources). |
| `ModuleNotFoundError: pandas` | Rebuild the image so pandas is installed: `docker compose build && docker compose up -d`. |

Handy logs:

```bash
docker compose logs airflow-scheduler
docker compose logs airflow-webserver
docker compose logs airflow-init
```

## 13. Teardown

```bash
docker compose down        # stop & remove containers (keeps the DB volume)
docker compose down -v      # also wipe the metadata database (fresh start)
```

## 14. Running on EC2 (optional)

To host the demo for a class instead of running locally:

1. Launch an EC2 instance (`t3.medium` or larger, ≥ 20 GB disk), install Docker
   + the Compose plugin (see the `storm-demo/README.md` in this repo for the
   exact install commands).
2. In the **Security Group**, open inbound **TCP 8080** to the classroom/your IP
   (and 22 for SSH). Keep it scoped — the demo login is `admin`/`admin`.
3. Clone the repo, `cd airflow`, run `docker compose up -d --build`.
4. Browse to `http://<ec2-public-ip>:8080`.

> For anything beyond a demo, change the default password, set a real
> `AIRFLOW__CORE__FERNET_KEY`, and put it behind HTTPS.

---

### Version matrix

| Piece | Version |
|-------|---------|
| Apache Airflow | 2.10.4 |
| Executor | LocalExecutor |
| Metadata DB | PostgreSQL 13 |
| pandas | ≥ 2.0 |
| Python | 3.x (from the official Airflow image) |
