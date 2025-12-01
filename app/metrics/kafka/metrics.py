from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
)


messages_consumed_total = Counter(
    name="kafka_messages_consumed_total",
    documentation="Общее количество сообщений, полученных из Kafka",
    labelnames=["topic", "partition", "group_id", "client_id"],
)
messages_processed_total = Counter(
    name="kafka_messages_processed_total",
    documentation="Общее количество успешно обработанных сообщений",
    labelnames=["topic", "partition", "group_id", "client_id"],
)
messages_failed_total = Counter(
    name="kafka_messages_failed_total",
    documentation="Общее количество сообщений, которые не удалось обработать (исключения или не поддающиеся повтору)",
    labelnames=["topic", "partition", "group_id", "client_id", "error_type"],
)
messages_retry_attempts_total = Counter(
    name="kafka_messages_retry_attempts_total",
    documentation="Общее количество попыток повтора обработки сообщений",
    labelnames=["topic", "group_id", "client_id"],
)
messages_dlq_total = Counter(
    name="kafka_messages_dlq_total",
    documentation="Общее количество сообщений, отправленных в DLQ",
    labelnames=["topic", "group_id", "client_id", "reason"],
)
message_processing_duration_seconds = Histogram(
    name="kafka_message_processing_duration_seconds",
    documentation="Время, затрачиваемое на обработку одного сообщения, в секундах",
    labelnames=["topic", "partition", "group_id", "client_id"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)
message_size_bytes = Histogram(
    name="kafka_message_size_bytes",
    documentation="Размер payload в сообщении в байтах",
    labelnames=["topic", "client_id"],
    buckets=(100, 500, 1000, 5_000, 10_000, 50_000, 100_000, 500_000, 1_000_000),
)

consumer_commits_success_total = Counter(
    name="kafka_consumer_commits_success_total",
    documentation="Общее количество успешных коммитов",
    labelnames=["group_id", "client_id"],
)
consumer_commits_failed_total = Counter(
    name="kafka_consumer_commits_failed_total",
    documentation="Общее количество неуспешных коммитов",
    labelnames=["group_id", "client_id"],
)
consumer_rebalances_total = Counter(
    name="kafka_consumer_rebalances_total",
    documentation="Общее количество событий ребаланса consumer-group",
    labelnames=["group_id", "client_id"],
)
consumer_errors_total = Counter(
    name="kafka_consumer_errors_total",
    documentation="Необработанные ошибки потребителя (сеть, десериализация и т.д.)",
    labelnames=["topic", "error_type"],
)
consumer_offset_lag = Gauge(
    name="kafka_consumer_offset_lag",
    documentation="Отставание между последним сообщением брокера и сообщением, принятым потребителем (для каждого раздела)",
    labelnames=["topic", "partition", "group_id"],
    multiprocess_mode="all",
)
consumer_partition_count = Gauge(
    name="kafka_consumer_partition_count",
    documentation="Количество разделов, назначенных в данный момент этому экземпляру потребителя",
    labelnames=["topic", "group_id", "client_id"],
    multiprocess_mode="all",
)
consumer_inflight_messages = Gauge(
    name="kafka_consumer_inflight_messages",
    documentation="Текущее количество обрабатываемых сообщений (в процессе обработки)",
    labelnames=["topic", "group_id", "client_id"],
    multiprocess_mode="all",
)
consumer_local_queue_size = Gauge(
    name="kafka_consumer_local_queue_size",
    documentation="Размер локальной очереди предварительной выборки/буферизации (если используется)",
    labelnames=["topic", "client_id"],
    multiprocess_mode="all",
)
consumer_last_message_timestamp = Gauge(
    name="kafka_consumer_last_message_timestamp",
    documentation="Время в секундах (Unix timestamp) последнего успешно обработанного сообщения",
    labelnames=["topic", "partition", "group_id", "client_id"],
    multiprocess_mode="all",
)
consumer_uptime_seconds = Gauge(
    name="kafka_consumer_uptime_seconds",
    documentation="Uptime потребителя в секундах",
    labelnames=["client_id"],
    multiprocess_mode="all",
)
consumer_online_status = Gauge(
    name="kafka_consumer_online_status",
    documentation="Статус потребителя. Если онлайн, то (1), иначе (0)",
    labelnames=["client_id"],
    multiprocess_mode="all",
)
consumer_fetch_duration_seconds = Histogram(
    name="kafka_consumer_fetch_duration_seconds",
    documentation="Время, затраченное на получение сообщений от брокера, в секундах",
    labelnames=["topic", "client_id"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
consumer_records_per_fetch = Histogram(
    name="kafka_consumer_records_per_fetch",
    documentation="Количество сообщений, возвращаемых за fetch/batch",
    labelnames=["topic", "client_id"],
    buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000),
)

duplicates_total = Counter(
    name="duplicates_document_total",
    documentation="Общее количество дубликатов документов, полученных из Kafka",
    labelnames=["topic", "client_id"],
)
