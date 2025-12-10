web: gunicorn core.wsgi:application --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
worker: celery -A core worker --loglevel=info --concurrency=2