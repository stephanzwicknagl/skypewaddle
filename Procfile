web: gunicorn app:server --workers 4
queue: celery -A app:celery_app worker --loglevel=INFO --concurrency=2