write-monitor-message:
	docker exec --interactive --tty su-broker \
kafka-console-producer --bootstrap-server su-broker:9092 \
                       --topic monitor

create-topics:
	docker exec su-broker \
  kafka-topics --create --if-not-exists \
    --topic downloader \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1
	docker exec su-broker \
  kafka-topics --create --if-not-exists \
    --topic monitor \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1
	docker exec su-broker \
  kafka-topics --create --if-not-exists \
    --topic manager \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1
	docker exec su-broker \
  kafka-topics --create --if-not-exists \
    --topic storage \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1
	docker exec su-broker \
  kafka-topics --create --if-not-exists \
    --topic updater \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1
	docker exec su-broker \
  kafka-topics --create --if-not-exists \
    --topic verifier \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1
