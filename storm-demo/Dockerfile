FROM storm:latest

USER root

# Install Python + pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip && \
    pip install --no-cache-dir streamparse && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER storm
