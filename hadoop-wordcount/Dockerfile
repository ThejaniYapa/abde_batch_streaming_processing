FROM eclipse-temurin:8-jdk

ENV JAVA_HOME=/opt/java/openjdk
ENV HADOOP_VERSION=3.3.6
ENV HADOOP_HOME=/opt/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

RUN apt-get update && apt-get install -y \
    ssh rsync curl python3 python3-pip net-tools

RUN curl -O https://downloads.apache.org/hadoop/common/hadoop-$HADOOP_VERSION/hadoop-$HADOOP_VERSION.tar.gz && \
    tar -xzf hadoop-$HADOOP_VERSION.tar.gz && \
    mv hadoop-$HADOOP_VERSION $HADOOP_HOME && \
    rm hadoop-$HADOOP_VERSION.tar.gz

RUN ssh-keygen -t rsa -P "" -f ~/.ssh/id_rsa && \
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys && \
    chmod 600 ~/.ssh/authorized_keys

COPY config/* $HADOOP_HOME/etc/hadoop/

RUN mkdir -p /hadoopdata/hdfs/namenode /hadoopdata/hdfs/datanode

CMD ["bash"]
