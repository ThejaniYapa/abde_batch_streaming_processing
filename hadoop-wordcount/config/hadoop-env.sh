# export JAVA_HOME=/usr/local/openjdk
# export JAVA_HOME=${JAVA_HOME:-/opt/java/openjdk}
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
export HDFS_NAMENODE_DIR=/hadoopdata/hdfs/namenode
export HDFS_DATANODE_DIR=/hadoopdata/hdfs/datanode
