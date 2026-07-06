"""
01 · Hello, Airflow!
====================
The smallest useful DAG. It introduces the three ideas every Airflow user needs:

  1. A **DAG**  = a workflow: a graph of tasks plus a schedule.
  2. A **Task** = one unit of work, created from an **Operator**.
  3. **Dependencies** = the arrows (``>>``) that set execution order.

In the UI: unpause this DAG (toggle on the left), then hit ▶ "Trigger DAG"
and watch the tasks go green in the Graph view.
"""
from __future__ import annotations

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# default_args are applied to *every* task in this DAG unless a task overrides
# them. This is where you set retry behaviour, ownership, alerting, etc.
default_args = {
    "owner": "data-eng-101",
    "retries": 2,                                   # on failure, retry twice ...
    "retry_delay": pendulum.duration(seconds=30),   # ... 30s apart
}


def say_hello(**context):
    """A plain Python function, run by a PythonOperator.

    Airflow injects a `context` dict with runtime info. Here we read the
    *logical date* — the timestamp of the scheduled interval this run represents.
    """
    logical_date = context["logical_date"]
    print(f"Hello from Airflow! This run is for {logical_date:%Y-%m-%d}.")
    return "greeting-done"   # whatever you return is saved as an XCom (see DAG 02)


with DAG(
    dag_id="01_hello_airflow",
    description="The smallest useful Airflow DAG",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",       # run once a day ...
    catchup=False,           # ... but don't back-fill every day since start_date
    tags=["intro", "101"],
) as dag:

    # BashOperator: run a shell command on the worker.
    print_date = BashOperator(
        task_id="print_date",
        bash_command="echo 'Worker time is:' && date",
    )

    # PythonOperator: call a Python function.
    greet = PythonOperator(
        task_id="greet",
        python_callable=say_hello,
    )

    done = BashOperator(
        task_id="done",
        bash_command="echo 'Workflow complete ✅'",
    )

    # Dependencies: print_date, THEN greet, THEN done.
    print_date >> greet >> done
