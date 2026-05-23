import os

from celery import Celery


BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery("soa_worker", broker=BROKER_URL, backend=BROKER_URL)
