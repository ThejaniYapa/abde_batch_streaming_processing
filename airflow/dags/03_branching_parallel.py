"""
03 · Branching & Parallelism
============================
Airflow workflows are graphs, not straight lines. This DAG demonstrates three
control-flow capabilities in one picture:

  • **Parallel fan-out**  — three independent tasks run at the same time.
  • **Fan-in**            — a join task waits for all of them and combines results.
  • **Branching**         — ``BranchPythonOperator`` picks exactly ONE downstream
                            path at runtime (weekday vs weekend here).
  • **Trigger rules**     — the final task still runs even though the branch it
                            didn't take was *skipped*.

Open the **Graph** view after a run to see the diamond shape and which branch
lit up. Trigger it with different logical dates to flip the branch.
"""
from __future__ import annotations

import pendulum
from airflow.decorators import task
from airflow.models.dag import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.utils.trigger_rule import TriggerRule


def choose_branch(**context) -> str:
    """Return the task_id of the single branch to follow."""
    logical_date = context["logical_date"]
    if logical_date.weekday() < 5:      # Monday=0 ... Friday=4
        return "weekday_report"
    return "weekend_report"


with DAG(
    dag_id="03_branching_parallel",
    description="Parallel fan-out, a runtime branch, and a fan-in join",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    tags=["intro", "control-flow"],
) as dag:

    start = EmptyOperator(task_id="start")   # a no-op anchor / clean entry point

    @task
    def pull_source(name: str) -> int:
        """Simulate pulling data from a source system."""
        import random
        import time

        time.sleep(1)  # pretend this is real I/O
        rows = random.randint(50, 500)
        print(f"Pulled {rows} rows from source '{name}'")
        return rows

    # Three instances of the same task. With no dependency between them, the
    # LocalExecutor runs them in parallel.
    src_a = pull_source.override(task_id="pull_source_a")("A")
    src_b = pull_source.override(task_id="pull_source_b")("B")
    src_c = pull_source.override(task_id="pull_source_c")("C")

    @task
    def combine(a: int, b: int, c: int) -> int:
        """Fan-in: waits for all three sources, then sums their row counts."""
        total = a + b + c
        print(f"Combined total rows: {total}")
        return total

    combined = combine(src_a, src_b, src_c)

    # Branch: exactly one of the two reports runs; the other is skipped.
    branch = BranchPythonOperator(
        task_id="branch_on_day",
        python_callable=choose_branch,
    )
    weekday_report = EmptyOperator(task_id="weekday_report")
    weekend_report = EmptyOperator(task_id="weekend_report")

    # A default (ALL_SUCCESS) join would be skipped because one parent is
    # skipped. NONE_FAILED_MIN_ONE_SUCCESS lets `finish` run as long as nothing
    # actually failed and at least one parent succeeded.
    finish = EmptyOperator(
        task_id="finish",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # Wiring: start -> [3 parallel pulls] -> combine -> branch -> one report -> finish
    start >> [src_a, src_b, src_c]
    combined >> branch >> [weekday_report, weekend_report] >> finish
