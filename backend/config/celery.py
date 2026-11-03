"""
Celery app for background tasks (readiness recompute, bulk import).

Locally, the `worker` container runs these tasks from Redis.
On Render there is no worker: CELERY_TASK_ALWAYS_EAGER=True runs the same code inline.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("shelfready")
# Read every setting that starts with CELERY_ from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")
# Find tasks.py in every installed app.
app.autodiscover_tasks()
