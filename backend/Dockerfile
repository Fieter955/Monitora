FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml ./
COPY app ./app
RUN pip install --upgrade pip && pip install .

COPY alembic.ini ./
COPY alembic ./alembic

RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m app.bootstrap && fastapi run app/main.py --host 0.0.0.0 --port 8000 --proxy-headers"]
