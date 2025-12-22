web: gunicorn --bind 0.0.0.0:${PORT:-8080} server:app
worker: python reminder_scheduler.py --loop
translator: gunicorn --bind 0.0.0.0:${PORT:-8080} translate_worker:app
