from typing import (
    Any,
    Callable,
)
import asyncio
import time
import json
import os

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import ConsumerRecord

from app.metrics.kafka import metrics
from app.core import logger


class KafkaConsumerWorker:
    # TODO добавить таймауты для настройки
    def __init__(
        self,
        topics: dict[str, Callable],
        bootstrap_servers: str = "localhost:19092",
        group_id: str | None = None,
        enable_auto_commit: bool = False,
        concurrency: int = 1,
    ):
        """
        :param topics: Словарь topic -> handler (handler принимает ConsumerRecord).
        :param bootstrap_servers: Адрес Kafka.
        :param group_id: Идентификатор группы. Если None - будет сгенерирован по PID.
        :param enable_auto_commit: Использовать автокоммит оффсетов.
        :param concurrency: Максимальное количество одновременных обработчиков.
        """

        self.pid = os.getpid()
        self.topics = list(topics.keys())
        self.handlers = topics
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id or f"{self.pid}-group"
        self.enable_auto_commit = enable_auto_commit
        self.concurrency = max(1, int(concurrency))
        self._consumer: AIOKafkaConsumer | None = None
        self._loop: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._logger = logger.bind(pid=self.pid)

    async def start(self) -> None:
        """
        Запускает потребитель (consumer) и цикл сообщений.
        """

        self._logger.info(
            f"[{self.pid}] Запуск потребителя",
            topics=self.topics,
            group_id=self.group_id,
        )
        self._consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=self.enable_auto_commit,
            value_deserializer=lambda value: json.loads(value.decode()),
        )
        await self._consumer.start()
        metrics.consumer_online_status.labels("some_client_id").set(1)
        self._loop = asyncio.create_task(self._message_loop())
        self._logger.info(
            f"[{self.pid}] Потребитель запущен",
            topics=self.topics,
            group_id=self.group_id,
        )

    async def stop(self) -> None:
        """
        Останавливает потребитель (consumer) и цикл сообщений.
        """

        self._logger.info(f"[{self.pid}] Остановка потребителя...")
        self._stop_event.set()

        if self._consumer:
            try:
                await self._consumer.stop()
            except Exception as e:
                self._logger.error(
                    f"[{self.pid}] Ошибка при остановке потребителя",
                    error_message=str(e),
                )

        if self._loop:
            await self._loop

        metrics.consumer_online_status.labels("some_client_id").set(0)
        self._logger.info(f"[{self.pid}] Потребитель остановлен",)

    async def _message_loop(self) -> None:
        """
        Основной цикл чтения сообщений и распределения их обработчикам.
        """

        assert self._consumer is not None
        semaphore = asyncio.Semaphore(self.concurrency)
        loop = asyncio.get_running_loop()
        tasks: list[asyncio.Task] = []

        async def handle_message(msg: ConsumerRecord) -> bool:
            """
            Вызывает соответствующий обработчик для сообщения.

            :param msg: Сообщение Kafka.

            :return: True, если обработка успешна, иначе False.
            """

            handler: Any | None = self.handlers.get(msg.topic)
            if handler is None:
                self._logger.warning(
                    f"[{self.pid}] Нет обработчика для топика {msg.topic}, пропуск",
                    topic=msg.topic,
                )
                return False
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(msg)
                else:
                    await loop.run_in_executor(None, handler, msg)
                metrics.messages_processed_total.labels(
                    topic=msg.topic,
                    partition=msg.partition,
                    group_id=self.group_id,
                    client_id="some_client_id",
                ).inc()
                return True
            except Exception as e:
                metrics.messages_failed_total.labels(
                    topic=msg.topic,
                    partition=msg.partition,
                    group_id=self.group_id,
                    client_id="some_client_id",
                    error_type=type(e).__name__,
                ).inc()
                self._logger.error(
                    f"[{self.pid}] Ошибка обработчика для топика {msg.topic}",
                    topic=msg.topic,
                    partition=msg.partition,
                    offset=msg.offset,
                    error_message=str(e),
                )
                # логика retry и отправка в DLQ, если будет
                # metrics.messages_dlq_total.labels(
                #     topic=msg.topic,
                #     group_id=self.group_id,
                #     client_id="some_client_id",
                #     reason="processing_error",
                # )
                return False
            finally:
                metrics.consumer_last_message_timestamp.labels(
                    topic=msg.topic,
                    partition=msg.partition,
                    group_id=self.group_id,
                    client_id="some_client_id",
                ).set(time.time())

        try:
            while not self._stop_event.is_set():
                try:
                    records_map = await self._consumer.getmany(
                        timeout_ms=1000,  # TODO вынести таймаут
                        max_records=1,
                    )
                except Exception as e:
                    self._logger.error(
                        f"[{self.pid}] Ошибка при получении сообщения из Kafka",
                        error_message=str(e),
                    )
                    await asyncio.sleep(1)
                    continue

                for messages in records_map.values():
                    for msg in messages:
                        metrics.messages_consumed_total.labels(
                            topic=msg.topic,
                            partition=msg.partition,
                            group_id=self.group_id,
                            client_id="some_client_id",
                        ).inc()
                        await semaphore.acquire()
                        tasks.append(
                            asyncio.create_task(
                                self._process_and_commit(
                                    msg=msg,
                                    handler=handle_message,
                                    semaphore=semaphore,
                                )
                            ),
                        )

                tasks = [task for task in tasks if not task.done()]
        except asyncio.CancelledError as e:
            self._logger.info(
                f"[{self.pid}] Цикл сообщений отменен",
                error_message=str(e),
            )
        except Exception as e:
            self._logger.error(
                f"[{self.pid}] Непредвиденная ошибка в цикле сообщений",
                error_message=str(e),
            )

        if tasks:
            self._logger.info(f"[{self.pid}] Ожидание невыполненных задач...")
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_and_commit(
        self,
        msg: ConsumerRecord,
        handler: Callable,
        semaphore: asyncio.Semaphore,
    ) -> None:
        """
        Вызывает функцию-обработчик (handler) с переданным сообщением.
        При успешной обработке выполняет коммит.

        :param msg: Сообщение Kafka.
        :param handler: Функция-обработчик с параметром ConsumerRecord.
        :param semaphore: Семафор, используемый для ограничения конкурентности.
                          Гарантируется, что семафор освободится при любых случаях,
                          даже если возникнет ошибка при обработке.
        """

        try:
            ok: bool = await handler(msg)
            if ok:
                try:
                    await self._consumer.commit()
                    metrics.consumer_commits_success_total.labels(
                        group_id=self.group_id,
                        client_id="some_client_id",
                    ).inc()
                except Exception as e:
                    metrics.consumer_commits_failed_total.labels(
                        group_id=self.group_id,
                        client_id="some_client_id",
                    )
                    self._logger.error(
                        f"[{self.pid}] Ошибка при коммите",
                        error_message=str(e),
                    )
            else:
                self._logger.warning(
                    f"[{self.pid}] Не удалось обработать сообщение",
                    topic=msg.topic,
                    partition=msg.partition,
                    offset=msg.offset,
                )
        finally:
            semaphore.release()
