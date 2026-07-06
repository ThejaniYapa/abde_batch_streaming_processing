"""
04 · Dynamic Task Mapping
=========================
Sometimes you don't know how much work exists until the DAG is *running*
(e.g. "process every file that landed in the bucket today"). **Dynamic Task
Mapping** creates a variable number of parallel task instances at runtime with
``.expand()`` — no need to hard-code how many.

In the **Grid**/​**Graph** view you'll see the ``process`` task render as
mapped instances ``[0] [1] [2] ...``, one per discovered file, then collapse
back into a single ``summarize`` step. This is the same map → reduce shape as
Hadoop/Spark, expressed as an Airflow workflow.
"""
from __future__ import annotations

import pendulum
from airflow.decorators import dag, task


@dag(
    dag_id="04_dynamic_task_mapping",
    description="Fan out a variable number of tasks at runtime with .expand()",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    tags=["intro", "advanced"],
)
def dynamic_mapping():

    @task
    def list_files() -> list[str]:
        """Pretend we scanned a landing zone and found a batch of files."""
        files = [f"batch_{i:02d}.csv" for i in range(1, 6)]
        print(f"Discovered {len(files)} files to process")
        return files

    @task
    def process(file: str) -> int:
        """Runs once PER file — each as its own mapped task instance."""
        import random

        count = random.randint(100, 1000)
        print(f"Processed {file}: {count} records")
        return count

    @task
    def summarize(counts: list[int]) -> None:
        """Reduce step: fan every mapped result back into one number."""
        print(f"Processed {len(counts)} files, {sum(counts)} records total")

    # .expand() creates one `process` instance for each item in the list.
    counts = process.expand(file=list_files())
    summarize(counts)


dynamic_mapping()
