FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/
COPY data/ ./data/
RUN mkdir -p data/sessions

CMD ["python", "-m", "src"]
