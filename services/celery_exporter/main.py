from app.metrics.celery.exporter import Exporter
from app.core import settings


if __name__ == "__main__":
    exporter = Exporter(
        host=settings.celery.metrics_host,
        port=settings.celery.metrics_port,
        collect_events_metrics_interval_s=settings.celery.collect_events_metrics_interval_s,
        collect_queue_metrics_interval_s=settings.celery.collect_queue_metrics_interval_s,
    )
    exporter.run()
