from airflow import DAG
from airflow.providers.apache.hdfs.operators.hdfs import HdfsPutFileOperator
from airflow.providers.apache.hive.operators.hive import HiveOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

dag = DAG('daily_hadoop_job', start_date=datetime(2025, 12, 22), schedule_interval='@daily')

hadoop_task = BashOperator(
    task_id='run_hadoop_job',
    bash_command='bash /home/ubuntu/run_hadoop_job.sh',
    dag=dag
)
