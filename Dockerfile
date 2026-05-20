FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=task.settings.production

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN SECRET_KEY=build-only \
    DATABASE_URL=postgres://unused:unused@127.0.0.1:5432/unused \
    ALLOWED_HOSTS=localhost \
    CSRF_TRUSTED_ORIGINS=https://localhost \
    python manage.py collectstatic --noinput --settings=task.settings.production

EXPOSE 8000

CMD sh -c "python manage.py migrate --noinput && python manage.py create_superuser_if_none && exec gunicorn task.wsgi:application --bind 0.0.0.0:${PORT:-8000}"
