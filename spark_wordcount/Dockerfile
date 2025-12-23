FROM bitnamilegacy/spark:3.5.2

USER root
# Install numpy for MLlib
RUN pip install --no-cache-dir numpy

# Switch back to the default Spark user
USER 1001