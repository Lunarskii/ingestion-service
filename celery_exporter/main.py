from celery_exporter.exporter import Exporter

from config import settings


exporter = Exporter()


if __name__ == "__main__":
    exporter.run(
        host=settings.celery.metrics_host,
        port=settings.celery.metrics_port,
    )
