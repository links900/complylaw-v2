web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2
worker: celery -A core worker --loglevel=info --concurrency=2