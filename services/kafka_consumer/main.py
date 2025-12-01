import asyncio

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    generate_latest,
)
from prometheus_client.multiprocess import MultiProcessCollector

from services.kafka_consumer.worker import KafkaConsumerWorker
from services.kafka_consumer.consumers.document_events import save_document_meta
from app.core import settings


class App:
    async def __call__(self, scope, receive, send) -> None:
        stype: str = scope.get("type")
        if stype == "lifespan":
            await self._lifespan(receive, send)
            return
        if stype == "http":
            await self._metrics(scope, send)
            return

        await send({"type": "http.response.start", "status": 500, "headers": []})
        await send({"type": "http.response.body", "body": b"Unsupported protocol"})

    async def _lifespan(self, receive, send) -> None:
        try:
            while True:
                message = await receive()
                mtype: str = message.get("type")
                if mtype == "lifespan.startup":
                    try:
                        await self._on_startup()
                        await send({"type": "lifespan.startup.complete"})
                    except Exception as exc:
                        await send(
                            {
                                "type": "lifespan.startup.failed",
                                "message": str(exc) or "startup failed",
                            },
                        )
                elif mtype == "lifespan.shutdown":
                    try:
                        await self._on_shutdown()
                        await send({"type": "lifespan.shutdown.complete"})
                    except Exception as exc:
                        await send(
                            {
                                "type": "lifespan.shutdown.failed",
                                "message": str(exc) or "shutdown failed",
                            },
                        )
                    break
        except asyncio.CancelledError:
            raise
        except Exception:
            ...

    async def _metrics(self, scope, send):
        if scope.get("path", "") != "/metrics":
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [(b"content-type", b"text/plain; charset=utf-8")],
                },
            )
            await send({"type": "http.response.body", "body": b"Not Found"})
            return

        try:
            registry = CollectorRegistry()
            MultiProcessCollector(registry)
            data = generate_latest(registry)
            headers = [
                (b"content-type", CONTENT_TYPE_LATEST.encode()),
                (b"content-length", str(len(data)).encode()),
            ]
            await send({"type": "http.response.start", "status": 200, "headers": headers})
            await send({"type": "http.response.body", "body": data})
        except Exception:
            await send({"type": "http.response.start", "status": 500, "headers": []})
            await send({"type": "http.response.body", "body": b"Internal Server Error"})

    async def _on_startup(self) -> None:
        self.worker = KafkaConsumerWorker(
            topics={
                settings.kafka.topic_doc_new: save_document_meta,
            },
            bootstrap_servers=settings.kafka.broker,
            group_id=settings.kafka.group_id,
        )
        await self.worker.start()

    async def _on_shutdown(self) -> None:
        await self.worker.stop()


app = App()
