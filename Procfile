web: gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app
release: alembic upgrade head
