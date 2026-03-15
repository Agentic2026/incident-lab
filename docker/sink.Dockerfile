FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    INCIDENT_ROLE=sink

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src

ENTRYPOINT ["python", "-m", "incident_lab"]
