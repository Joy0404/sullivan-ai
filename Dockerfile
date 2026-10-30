# Sullivan AI: one container serves the FastAPI API and the web app (apps/web).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/apps/api
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY apps/api/app ./app
COPY apps/web /app/apps/web

RUN useradd --create-home --uid 10001 sullivan
USER sullivan

EXPOSE 8000
# Railway injects PORT; locally it falls back to 8000.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
