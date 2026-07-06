(defproject storm_wordcount "0.0.1-SNAPSHOT"
  :source-paths ["topologies"]
  :resource-paths ["_resources"]
  :target-path "_build"
  :min-lein-version "2.0.0"
  :jvm-opts ["-client"]
  ;; Force all dependency resolution through HTTPS mirrors. Modern Leiningen
  ;; rejects plain-HTTP repos, and some transitive Storm deps still advertise an
  ;; insecure jboss.org URL.
  :repositories {"central" {:url "https://repo1.maven.org/maven2/"}
                 "clojars" {:url "https://repo.clojars.org/"}}
  ;; Depend on the lightweight `storm-client` (the topology-building API) rather
  ;; than the heavyweight `storm-core` aggregator. storm-core pulls in
  ;; storm-server -> hadoop-auth -> json-smart, which is what drags in the
  ;; insecure jboss HTTP repository and breaks `lein jar`. The full Storm runtime
  ;; is already provided by the cluster, so the client API is all we need to
  ;; package the topology jar.
  :dependencies  [[org.apache.storm/storm-client "2.2.0"]
                  [org.apache.storm/multilang-python "2.2.0"]]
  :jar-exclusions     [#"log4j\.properties" #"backtype" #"trident" #"META-INF" #"meta-inf" #"\.yaml"]
  :uberjar-exclusions [#"log4j\.properties" #"backtype" #"trident" #"META-INF" #"meta-inf" #"\.yaml"])
