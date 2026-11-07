FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml ./
COPY core ./core
COPY db ./db
COPY models ./models
COPY schemas ./schemas
COPY services ./services
COPY api ./api
COPY main.py bootstrap.py network_worker.py ./
RUN pip install --upgrade pip && pip install .

COPY alembic.ini ./
COPY alembic ./alembic

RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m bootstrap && fastapi run main.py --host 0.0.0.0 --port 8000 --proxy-headers"]
