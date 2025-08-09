FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/somecrab/final04ka

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["gunicorn", "final04ka.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "2"]
