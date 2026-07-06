# Custom Airflow image = official Airflow + a few Python libs our DAGs use.
#
# Extending the official image (rather than pip-installing at runtime) is the
# recommended way to add dependencies: the build is cached and every Airflow
# component — scheduler, webserver, workers — gets the exact same environment.
FROM apache/airflow:2.10.4

# Always install extra packages as the unprivileged `airflow` user.
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
