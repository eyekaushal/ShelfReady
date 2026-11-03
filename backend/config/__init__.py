# Load Celery when Django starts, so @shared_task functions use our app.
from config.celery import app as celery_app

__all__ = ("celery_app",)
