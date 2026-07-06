"""
02 · TaskFlow ETL
=================
A realistic **Extract → Transform → Load** pipeline written with the modern
**TaskFlow API** (the ``@dag`` / ``@task`` decorators).

Why students should care:
  • ``@task`` turns an ordinary Python function into an Airflow task.
  • Return values flow between tasks automatically as **XComs** — no manual
    push/pull. Notice ``transform`` simply takes ``extract``'s output as an
    argument, and that single line creates *both* the data hand-off and the
    dependency.
  • Real work is done with **pandas** (added via the custom Docker image).

Input : data/input/sales.csv          (mounted into the container)
Output: data/output/sales_summary.csv

After a run, inspect each task's **XCom** in the UI (task ▸ XCom) to see the
data that moved between steps.
"""
from __future__ import annotations

import pendulum
from airflow.decorators import dag, task

INPUT_PATH = "/opt/airflow/data/input/sales.csv"
OUTPUT_PATH = "/opt/airflow/data/output/sales_summary.csv"


@dag(
    dag_id="02_taskflow_etl",
    description="Extract → Transform → Load with the TaskFlow API + pandas",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    tags=["intro", "etl", "taskflow"],
)
def taskflow_etl():

    @task
    def extract() -> list[dict]:
        """E — read the raw sales file and pass the rows downstream."""
        import pandas as pd

        df = pd.read_csv(INPUT_PATH)
        print(f"Extracted {len(df)} rows from {INPUT_PATH}")
        # The return value is serialized to JSON and stored as an XCom.
        return df.to_dict(orient="records")

    @task
    def transform(rows: list[dict]) -> list[dict]:
        """T — compute revenue and aggregate it per product category."""
        import pandas as pd

        df = pd.DataFrame(rows)
        df["revenue"] = df["quantity"] * df["unit_price"]
        summary = (
            df.groupby("category", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
        )
        print("Revenue by category:\n" + summary.to_string(index=False))
        return summary.to_dict(orient="records")

    @task
    def load(summary_rows: list[dict]) -> str:
        """L — write the summary to disk and log the top category."""
        import os

        import pandas as pd

        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        summary = pd.DataFrame(summary_rows)
        summary.to_csv(OUTPUT_PATH, index=False)

        top = summary.iloc[0]
        print(f"Wrote {OUTPUT_PATH}")
        print(f"🏆 Top category: {top['category']} (${top['revenue']:,.2f})")
        return OUTPUT_PATH

    # The whole pipeline in one readable line: extract -> transform -> load.
    load(transform(extract()))


taskflow_etl()
