# Deployment — базова топологія

Перший production deployment планується на Linux + Docker Compose без Kubernetes.

Базові компоненти:

- reverse proxy / TLS;
- frontend;
- FastAPI backend;
- background worker;
- PostgreSQL;
- S3-compatible object storage;
- Redis за потреби для queue/cache/rate limiting, але не як джерело бізнес-цілісності.

Production і development мають окремі конфігурації та secrets. Схема БД змінюється тільки контрольованими Alembic migrations.
