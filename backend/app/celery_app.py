from celery import Celery

celery = Celery(
    "graphrag",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["backend.app.tasks"]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600
)