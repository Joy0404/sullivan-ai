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
USER root

EXPOSE 10000
# Render injects PORT. App secrets are runtime variables, never build arguments.
CMD ["python", "-m", "app.launch"]
